import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.common import router
from time_func import send_appointment_reminders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    asyncio.create_task(send_appointment_reminders())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
