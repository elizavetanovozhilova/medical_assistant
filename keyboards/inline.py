from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import *

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

def get_doctors_keyboard(doctors: list) -> InlineKeyboardMarkup:
    buttons = []
    for doctor in doctors:
        doctor_id, first_name, last_name, specialization = doctor
        buttons.append(
            [InlineKeyboardButton(
                text=f"{first_name} {last_name} ({specialization})",
                callback_data=f"doctor_{doctor_id}"
            )]
        )
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_dates_keyboard(dates) -> InlineKeyboardMarkup:
    buttons = []

    # Ensure dates is always a list (handle both str and list inputs)
    if isinstance(dates, str):
        dates = [dates]

    for date in dates:
        try:
            # Handle if date is already a datetime object
            if hasattr(date, 'strftime'):
                date_str = date.strftime("%Y-%m-%d")
            # Handle if date is a string in YYYY-MM-DD format
            elif isinstance(date, str):
                date_str = date
            else:
                continue  # Skip invalid entries

            buttons.append([
                InlineKeyboardButton(
                    text=date_str.replace("-", "."),
                    callback_data=f"date_{date_str}"
                )
            ])
        except Exception as e:
            print(f"Error processing date {date}: {e}")
            continue

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="appointment")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_times_keyboard(times: list) -> InlineKeyboardMarkup:
    buttons = []
    for time_entry in times:
        try:
            if hasattr(time_entry, 'strftime'):
                time_str = time_entry.strftime("%H:%M")
            elif isinstance(time_entry, datetime):
                time_str = time_entry.strftime("%H:%M")
            elif isinstance(time_entry, str):
                time_str = time_entry
            else:
                continue

            buttons.append([InlineKeyboardButton(
                text=time_str,
                callback_data=f"time_{time_str}"
            )])
        except Exception as e:
            print(f"Error formatting time entry {time_entry}: {e}")
            continue

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="appointment")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)