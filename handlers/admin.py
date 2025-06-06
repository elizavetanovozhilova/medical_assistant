from aiogram import types
#from filters.is_admin import IsAdmin

async def admin_panel(message: types.Message):
    await message.answer("Добро пожаловать в панель администратора!")