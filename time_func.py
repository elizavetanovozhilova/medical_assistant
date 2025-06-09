# time_func.py
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
import db_handler

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)


async def send_appointment_reminders():
    while True:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        target_date = tomorrow.date()

        conn = db_handler.db.create_connection()
        if not conn:
            print("❌ Нет подключения к БД")
            await asyncio.sleep(3600)
            continue

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u.tg_id,
                        a.appointment_date,
                        d.first_name || ' ' || d.last_name AS doctor_name,
                        s.name AS specialization
                    FROM Appointments a
                    JOIN Users u ON a.user_id = u.user_id
                    JOIN Doctors d ON a.doctor_id = d.doctor_id
                    JOIN Specializations s ON d.specialization_id = s.specialization_id
                    WHERE DATE(a.appointment_date) = %s
                """, (target_date,))

                rows = cursor.fetchall()

                for row in rows:
                    tg_id = int(row[0])
                    date_str = row[1].strftime("%d.%m.%Y")
                    time_str = row[1].strftime("%H:%M")
                    doctor = row[2]
                    specialization = row[3]

                    text = (
                        f"🔔 Напоминание о приеме:\n\n"
                        f"📅 {date_str} в {time_str}\n"
                        f"👨‍⚕️ Врач: {doctor} ({specialization})"
                    )

                    try:
                        await bot.send_message(chat_id=tg_id, text=text)
                    except Exception as e:
                        print(f"Ошибка отправки уведомления пользователю {tg_id}: {e}")

        except Exception as e:
            print(f"Ошибка при получении данных о приемах: {e}")
        finally:
            conn.close()

        await asyncio.sleep(86400)
