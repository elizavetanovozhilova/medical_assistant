import os
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from docx import Document
from docx2pdf import convert
from db_handler.db import create_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "сюда надо вставить токен ботика"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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


user_data = {}

def get_user_data(tg_id: int) -> dict:
    conn = create_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE tg_id = %s", (str(tg_id),))
            if cursor.rowcount == 0:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, cursor.fetchone()))
    except Exception as e:
        logger.error(f"DB error get_user_data: {e}")
        return None
    finally:
        conn.close()

def get_last_appointment(user_id: int) -> dict:
    conn = create_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM appointments WHERE user_id = %s ORDER BY appointment_date DESC LIMIT 1",
                (user_id,)
            )
            if cursor.rowcount == 0:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, cursor.fetchone()))
    except Exception as e:
        logger.error(f"DB error get_last_appointment: {e}")
        return None
    finally:
        conn.close()

def get_doctor_data(doctor_id: int) -> dict:
    conn = create_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
            if cursor.rowcount == 0:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, cursor.fetchone()))
    except Exception as e:
        logger.error(f"DB error get_doctor_data: {e}")
        return None
    finally:
        conn.close()

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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    logger.info(f"User {tg_id} started bot")

    db_user = get_user_data(tg_id)
    if not db_user:
        await message.answer("Вы не зарегистрированы в системе. Пожалуйста, зарегистрируйтесь.")
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

    await ask_diagnosis(message, data)

async def ask_diagnosis(message: types.Message, data: CertificateData):
    data.waiting_for = 'diagnosis'
    await message.answer(
        "Выберите диагноз:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=txt)] for txt in ["ОРВИ", "Грипп", "Ангина", "Другое"]],
            resize_keyboard=True
        )
    )

@dp.message()
async def general_handler(message: types.Message):
    tg_id = message.from_user.id
    if tg_id not in user_data:
        await message.answer("Пожалуйста, начните сначала с /start.")
        return

    data = user_data[tg_id]
    text = message.text.strip()

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
        if not is_valid_date(text):
            await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
            return
        if not is_current_year(text):
            await message.answer(f"Дата начала должна быть в {datetime.now().year} году. Попробуйте снова.")
            return
        data.start_date = text
        data.waiting_for = 'end_date'
        await message.answer("Введите дату окончания болезни (ДД.ММ.ГГГГ):")
        return

    if data.waiting_for == 'end_date':
        if not is_valid_date(text):
            await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
            return
        if not is_current_year(text):
            await message.answer(f"Дата окончания должна быть в {datetime.now().year} году. Попробуйте снова.")
            return
        if not is_date_before(data.start_date, text):
            await message.answer("Дата окончания не может быть раньше даты начала. Введите дату окончания заново:")
            return
        data.end_date = text
        await generate_certificate(message, data)
        return

    await message.answer("Неизвестная команда. Попробуйте снова или начните с /start.")

async def generate_certificate(message: types.Message, data: CertificateData):
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

    os.remove(docx_path)
    os.remove(pdf_path)
    del user_data[tg_id]


@dp.message(F.text.startswith("/symptom"))
async def handle_symptom_with_advice(message: Message):
    user_input = message.text.replace("/symptom", "").strip()

    specialization = model_predict(user_input)  # todo: добавить модель

    if not specialization:
        await message.answer("😕 Не удалось определить специализацию по введённым симптомам.")
        return

    try:
        conn = create_connection()
        if not conn:
            return None
            
        with conn.cursor() as cursor:
            tips = cursor.execute(
                "SELECT title, content FROM MedicalTips WHERE category = $1",
                specialization
            )
        conn.close()
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при подключении к базе данных: {e}")
        return

    if not tips:
        await message.answer(f"Советы по специализации «{specialization}» пока отсутствуют.")
        return

    tip = random.choice(tips)
    response = f"💡 *{tip['title']}*\n\n{tip['content']}"
    await message.answer(response, parse_mode="Markdown")

if __name__ == "__main__":
    dp.run_polling(bot)
