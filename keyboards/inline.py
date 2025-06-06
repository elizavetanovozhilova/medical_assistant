from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📝 Записаться к врачу", callback_data="appointment")],
        [InlineKeyboardButton(text="💊 Рекомендация", callback_data="recommendation")],
        [InlineKeyboardButton(text="🩺 Мед карта", callback_data="medical_card")],
        [InlineKeyboardButton(text="📄 Справка", callback_data="reference")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_doctors_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Терапевт", callback_data="doctor_therapist")],
        [InlineKeyboardButton(text="Кардиолог", callback_data="doctor_cardio")],
        [InlineKeyboardButton(text="Невролог", callback_data="doctor_neuro")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_gender_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Мужской ♂️", callback_data="gender_male")],
        [InlineKeyboardButton(text="Женский ♀️", callback_data="gender_female")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_help_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]
    )

def get_medcard_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📋 Данные профиля", callback_data="medcard_profile")],
        [InlineKeyboardButton(text="📅 Данные о приёмах", callback_data="medcard_appointments")],
        [InlineKeyboardButton(text="💊 Диагнозы", callback_data="medcard_diagnoses")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_recommendation_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Да", callback_data="appointment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)