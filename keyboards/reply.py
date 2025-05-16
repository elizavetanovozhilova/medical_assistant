from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Начать")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Меню")]
        ],
        resize_keyboard=True
    )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

