# services.py

from db_handler.db import create_connection
import logging

logger = logging.getLogger(__name__)

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

# @dp.message(F.text.startswith("/symptom"))
# async def handle_symptom_with_advice(message: Message):
#     user_input = message.text.replace("/symptom", "").strip()
#
#     specialization = model_predict(user_input)  # todo: добавить модель
#
#     if not specialization:
#         await message.answer("😕 Не удалось определить специализацию по введённым симптомам.")
#         return
#
#     try:
#         conn = create_connection()
#         if not conn:
#             return None
#
#         with conn.cursor() as cursor:
#             tips = cursor.execute(
#                 "SELECT title, content FROM MedicalTips WHERE category = $1",
#                 specialization
#             )
#         conn.close()
#     except Exception as e:
#         await message.answer(f"⚠️ Ошибка при подключении к базе данных: {e}")
#         return
#
#     if not tips:
#         await message.answer(f"Советы по специализации «{specialization}» пока отсутствуют.")
#         return
#
#     tip = random.choice(tips)
#     response = f"💡 *{tip['title']}*\n\n{tip['content']}"
#     await message.answer(response, parse_mode="Markdown")

