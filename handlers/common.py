from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import get_main_menu, get_gender_keyboard
from db_handler.db import check_auth, register_user
from keyboards.reply import get_menu_reply_keyboard
from keyboards.inline import get_help_back_keyboard
from utils import get_user_data, get_last_appointment, get_doctor_data
from keyboards.inline import get_medcard_keyboard, get_recommendation_keyboard
from model import get_doctor, predict_intent, get_date


from docx import Document
from docx2pdf import convert
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, user
from datetime import datetime
import os
import logging

router = Router()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger = logging.getLogger(__name__)
user_data = {}


class CertificateData:
    def __init__(self):
        self.user_id = None
        self.full_name = None
        self.birth_date = None
        self.diagnosis = None
        self.start_date = None
        self.end_date = None
        self.doctor_id = None
        self.doctor_name = None
        self.clinic_name = "Разумед"
        self.waiting_for = None


class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_phone = State()


class RecommendationStates(StatesGroup):
    waiting_for_symptoms = State()


class MenuState(StatesGroup):
    waiting_for_input = State()


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def is_date_before(date_str1: str, date_str2: str) -> bool:
    try:
        d1 = datetime.strptime(date_str1, "%d.%m.%Y")
        d2 = datetime.strptime(date_str2, "%d.%m.%Y")
        return d1 <= d2
    except ValueError:
        return False


def is_current_year(date_str: str) -> bool:
    try:
        date = datetime.strptime(date_str, "%d.%m.%Y")
        return date.year == datetime.now().year
    except ValueError:
        return False


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)

    if check_auth(user_id):
        await message.answer(
            "С возвращением! Главное меню:",
            reply_markup=get_menu_reply_keyboard()
        )
    else:
        await message.answer("Введите ваше имя:", reply_markup=get_menu_reply_keyboard())
        await state.set_state(RegistrationStates.waiting_for_first_name)


@router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите вашу фамилию:")
    await state.set_state(RegistrationStates.waiting_for_last_name)


@router.message(RegistrationStates.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Укажите ваш пол:", reply_markup=get_gender_keyboard())
    await state.set_state(RegistrationStates.waiting_for_gender)


@router.callback_query(RegistrationStates.waiting_for_gender)
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = 'М' if callback.data == 'gender_male' else 'Ж'
    await state.update_data(gender=gender)
    await callback.message.edit_text(f"Пол: {gender}")
    await callback.message.answer("Введите вашу дату рождения (ДД.ММ.ГГГГ):")
    await state.set_state(RegistrationStates.waiting_for_birth_date)


@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    birth_date = message.text.strip()
    birth_date = get_date(birth_date)
    if not is_valid_date(birth_date):
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
        return

    await state.update_data(birth_date=birth_date)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user = message.from_user

    success = register_user(
        tg_id=str(user.id),
        username=user.username,
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        gender=user_data['gender'],
        phone=message.text,
        birth_date=user_data['birth_date']
    )

    if success:
        await state.clear()
        await message.answer(
            "Регистрация успешно завершена!",
            reply_markup=get_menu_reply_keyboard()
        )
        await state.set_state(MenuState.waiting_for_input)
        await message.answer("🏠Главное меню:", reply_markup=get_main_menu())
    else:
        await message.answer("Ошибка регистрации. Попробуйте позже.")


@router.callback_query(lambda c: c.data == "main_menu")
async def process_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MenuState.waiting_for_input)
    await callback.message.answer(
        "🏠Главное меню:",
        reply_markup=get_main_menu()
    )


@router.message(lambda msg: msg.text == "Меню")
async def handle_menu_button(message: types.Message, state: FSMContext):
    await state.set_state(MenuState.waiting_for_input)
    await message.answer(
        "🏠Главное меню:",
        reply_markup=get_main_menu()
    )


@router.message(MenuState.waiting_for_input)
async def main_menu_text_handler(message: types.Message, state: FSMContext):
    intent = predict_intent(message.text)

    if intent == "рекомендация":
        await ask_for_symptoms(message, state)

    elif intent == "запись":
        await handler_appointment(message, state)

    elif intent == 'оставить_отзыв':
        pass
        #await функция для оставления отзыва

    elif intent == 'читать_отзыв':
        pass
        #await функция для чтения отзывов

    elif intent == "справка":
        data = user_data.get(tg_id)
        if not data:
            await start_certificate_process(message, state)
            return
        await ask_for_symptoms(message, state)

    elif intent == 'профиль':
        await handle_medcard_profile(message, state)

    elif intent == 'приемы':
        await handle_medcard_appointments(message, state)

    elif intent == 'диагнозы':
        await handle_medcard_diagnoses(message, state)

    elif intent == 'график':
        await message.answer(
            "🕒 *График работы:*\n\n"
            "📅 *Понедельник – Пятница:* 07:30 – 20:00\n"
            "📅 *Суббота:* 08:00 – 17:00\n"
            "📅 *Воскресенье:* 08:00 – 15:00\n\n"
            "🔹 *График в праздничные дни* — уточняйте заранее.\n"
            "⛔ *Ночного приёма нет.*",
            parse_mode="Markdown"
        )

    elif intent == 'адреса':
        await message.answer(
            "🏥 *Наши филиалы:*\n\n"
            "📍 ул. Ю. Фучика, 53а\n"
            "📍 ул. Ак. Глушко, д. 15а\n"
            "📍 ул. Беломорская, д. 6",
            parse_mode="Markdown"
        )

    elif intent == 'специальности':
        await message.answer(
            "🏥 Наши специальности:\n\n"
            "• Гастроэнтерология\n"
            "• Гематология\n"
            "• Гинекология\n"
            "• Дерматовенерология\n"
            "• Кардиология\n"
            "• Маммология\n"
            "• Неврология\n"
            "• Нутрициология\n"
            "• Отоларингология\n"
            "• Офтальмология\n"
            "• Проктология\n"
            "• Психотерапия\n"
            "• Сосудистая хирургия\n"
            "• Урология\n"
            "• Хирургия\n"
            "• Эндокринология",
            parse_mode="Markdown"
        )

    elif intent == 'поддержка':
        await message.answer(
            "Если у вас возникли технические вопросы или нужна помощь, с удовольствием вам ответит наш специалист "
            "— @fliwoll. Пожалуйста, обращайтесь!",
            parse_mode="Markdown"
        )


    elif intent == 'функционал':
        await handler_help(message, state)

    else:
        await message.answer(f"❓ Извините, я пока не понял ваш запрос.\nЕсли вы не нашли нужную "
                             f"функцию в меню или у вас возник вопрос — пожалуйста, напишите в поддержку: "
                             f"@fliwoll. Мы обязательно поможем!")


#БЛОК ЗАПИСЬ НА ПРИЕМ
@router.callback_query(lambda c: c.data == "appointment")
async def start_appointment(callback: types.CallbackQuery, state: FSMContext):
    await handler_appointment(callback.message, state)


async def handler_appointment(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📅 Давайте запишем вас на приём. Уточните, пожалуйста, дату:")


#БЛОК РЕКОМЕНДАЦИЙ
@router.callback_query(lambda c: c.data == "recommendation")
async def start_recommendation(callback: types.CallbackQuery, state: FSMContext):
    await ask_for_symptoms(callback.message, state)


async def ask_for_symptoms(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Пожалуйста, опишите ваши симптомы:")
    await state.set_state(RecommendationStates.waiting_for_symptoms)


@router.message(RecommendationStates.waiting_for_symptoms)
async def process_symptoms(message: types.Message, state: FSMContext):
    symptoms = message.text
    if not symptoms or not isinstance(symptoms, str):
        await message.answer("Ошибка: описание симптомов отсутствует или неверного формата.")
        return

    doctor = get_doctor(symptoms)

    await state.update_data(predicted_doctor=doctor)

    await message.answer(
        f"Согласно вашим симптомам: {symptoms}\n\n"
        f"Рекомендуем вам обратиться к врачу по специальности: *{doctor}*.\n\n"
        "❓ Желаете записаться на приём?",
        reply_markup=get_recommendation_keyboard(),
        parse_mode="Markdown"
    )

    await state.clear()


#БЛОК МЕДКАРТЫ
@router.callback_query(lambda c: c.data == "medical_card")
async def process_help_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Что вы хотите узнать?",
        reply_markup=get_medcard_keyboard()
    )


@router.callback_query(lambda c: c.data == "medcard_profile")
async def start_medcard_profile(callback: types.CallbackQuery, state: FSMContext):
    await handle_medcard_profile(callback.message, state)


async def handle_medcard_profile(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    user = get_user_data(tg_id)
    if not user:
        await message.answer("Профиль не найден.")
        return

    text = (
        f"👤 Профиль:\n\n"
        f"Имя: {user['first_name']}\n"
        f"Фамилия: {user['last_name']}\n"
        f"Пол: {user['gender']}\n"
        f"Телефон: {user['phone']}\n"
        f"Дата рождения: {user.get('birth_date', 'не указана')}"
    )
    await message.answer(text)


@router.callback_query(lambda c: c.data == "medcard_appointments")
async def start_medcard_appointments(callback: types.CallbackQuery, state: FSMContext):
    await handle_medcard_appointments(callback.message, state)


async def handle_medcard_appointments(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = str(message.from_user.id)
    appointments = get_last_appointment(tg_id)

    if not appointments:
        await message.answer("Нет данных о приёмах.")
        return

    text = (
        f"📅 Последний приём:\n\n"
        f"Дата: {appointments['date']}\n"
        f"Доктор: {appointments['doctor_name']}"
    )
    await message.answer(text)


@router.callback_query(lambda c: c.data == "medcard_diagnoses")
async def start_medcard_diagnoses(callback: types.CallbackQuery, state: FSMContext):
    await handle_medcard_diagnoses(callback.message, state)


async def handle_medcard_diagnoses(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = str(message.from_user.id)
    # Заглушка – можно сделать get_user_diagnoses(tg_id)
    diagnoses = ["ОРВИ - 10.03.2024", "Грипп - 02.01.2025"]

    if not diagnoses:
        await message.answer("Диагнозов не найдено.")
        return

    text = "💊 Ваши диагнозы:\n\n" + "\n".join(diagnoses)
    await message.answer(text)


#БЛОК СПРАВКИ
@router.callback_query(lambda c: c.data == "reference")
async def start_certificate(callback: types.CallbackQuery, state: FSMContext):
    await start_certificate_process(callback.message, state)


async def start_certificate_process(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = str(message.from_user.id)
    db_user = get_user_data(tg_id)

    if not db_user:
        await message.answer("Вы не зарегистрированы в системе.")
        return

    data = CertificateData()
    data.user_id = db_user['user_id']
    data.full_name = f"{db_user['first_name']} {db_user['last_name']}"
    data.birth_date = db_user.get('birth_date')

    last_appointment = get_last_appointment(data.user_id)
    if last_appointment:
        data.doctor_id = last_appointment['doctor_id']
        doctor = get_doctor_data(data.doctor_id)
        if doctor:
            data.doctor_name = f"{doctor['first_name']} {doctor['last_name']}"

    user_data[tg_id] = data
    await handler_certificate(message, data, state)



async def ask_diagnosis(message: types.Message, data: CertificateData):
    data.waiting_for = 'diagnosis'
    await message.answer(
        "Выберите диагноз:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=txt)] for txt in ["ОРВИ", "Грипп", "Ангина", "Другое"]] + [[KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
    )


async def generate_certificate(message: types.Message, data: CertificateData, state: FSMContext):
    tg_id = message.from_user.id
    docx_path = os.path.join(OUTPUT_DIR, f"certificate_{tg_id}.docx")
    pdf_path = os.path.join(OUTPUT_DIR, f"certificate_{tg_id}.pdf")

    doc = Document()
    doc.add_heading("Медицинская справка", level=1)
    doc.add_paragraph(f"Выдана: {data.full_name}")
    doc.add_paragraph(f"Дата рождения: {data.birth_date}")
    doc.add_paragraph(f"Диагноз: {data.diagnosis}")
    doc.add_paragraph(f"Период болезни: с {data.start_date} по {data.end_date}")
    doc.add_paragraph("Справка выдана для предоставления по месту требования.")
    doc.add_paragraph(f"Врач: {data.doctor_name or 'Не указан'}")
    doc.add_paragraph(f"Медицинское учреждение: {data.clinic_name}")
    doc.add_paragraph(f"Дата выдачи: {datetime.now().strftime('%d.%m.%Y')}")

    doc.save(docx_path)
    convert(docx_path, pdf_path)

    await message.answer("Ваша справка готова!")
    await message.answer_document(FSInputFile(pdf_path))
    await state.set_state(MenuState.waiting_for_input)
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu())

    os.remove(docx_path)
    os.remove(pdf_path)


@router.message()
async def handler_certificate(message: types.Message, data, state):
    text = message.text.strip()
    await ask_diagnosis(message, data)

    if data.waiting_for == 'diagnosis':
        if text not in ["ОРВИ", "Грипп", "Ангина", "Другое"]:
            await message.answer("Пожалуйста, выберите диагноз из списка.")
            return
        if text == "Другое":
            data.waiting_for = 'custom_diagnosis'
            await message.answer("Введите ваш диагноз:", reply_markup=ReplyKeyboardRemove())
        else:
            data.diagnosis = text
            data.waiting_for = 'start_date'
            await message.answer("Введите дату начала болезни (ДД.ММ.ГГГГ):", reply_markup=ReplyKeyboardRemove())
        return

    if data.waiting_for == 'custom_diagnosis':
        data.diagnosis = text
        data.waiting_for = 'start_date'
        await message.answer("Введите дату начала болезни (ДД.ММ.ГГГГ):")
        return

    if data.waiting_for == 'start_date':
        text = get_date(text)
        if not is_valid_date(text):
            await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
            return
        if not is_current_year(text):
            await message.answer(f"Дата начала должна быть в {datetime.now().year} году.")
            return
        data.start_date = text
        data.waiting_for = 'end_date'
        await message.answer("Введите дату начала болезни (ДД.ММ.ГГГГ):", reply_markup=ReplyKeyboardRemove())
        return

    if data.waiting_for == 'end_date':
        text = get_date(text)
        if not is_valid_date(text):
            await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
            return
        if not is_current_year(text):
            await message.answer(f"Дата окончания должна быть в {datetime.now().year} году.")
            return
        if not is_date_before(data.start_date, text):
            await message.answer("Дата окончания не может быть раньше даты начала.")
            return
        data.end_date = text
        await generate_certificate(message, data, state)
        return


#БЛОК ПОМОЩИ
@router.callback_query(lambda c: c.data == "help")
async def start_help(callback: types.CallbackQuery, state: FSMContext):
    await handler_help(callback.message, state)


@router.callback_query(lambda c: c.data == "help")
async def handler_help(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❓ Помощь\n\n"
        "📌 Основные функции:\n\n"
        "• 📝 Записаться к врачу: выбор специалиста, даты и времени.\n"
        "• 💊 Рекомендация: подбор врача по симптомам.\n"
        "• 🩺 Мед карта: ваши данные\n"
        "• 📄 Справка: справки, налоги, история посещений.\n\n"
        "⚙️ Дополнительно:\n\n"
        "• Напоминания ⏰\n"
        "• Изменение данных 👤\n"
        "• FAQ ❓\n\n"
        "🔄 Навигация:\n\n"
        "• «Назад» — вернуться в предыдущее меню.\n"
        "• «Главное меню» — к основным разделам.\n"
        "📩 Поддержка: @fliwoll\n\n"
        "Кнопки:\n\n"
        "• 🔙 Назад\n"
        "• 🏠 Главное меню",
        reply_markup=get_help_back_keyboard()
    )
