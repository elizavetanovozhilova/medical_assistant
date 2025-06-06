import psycopg2
from psycopg2 import OperationalError
from typing import Optional


def create_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            dbname="medical_assistant",
            user="postgres",
            password="1"
        )
        return conn
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


def check_auth(tg_id: int) -> bool:
    conn = create_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Users WHERE tg_id = %s", (tg_id,))
            return cursor.fetchone() is not None
    except psycopg2.Error as e:
        print(f"Ошибка при проверке авторизации: {e}")
        return False
    finally:
        conn.close()


def register_user(
    tg_id: str,
    username: Optional[str],
    first_name: str,
    last_name: str,
    gender: str,
    phone: str,
    email: Optional[str] = None,
    birth_date: Optional[str] = None
) -> bool:
    conn = create_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Users 
                (first_name, last_name, gender, phone, email, tg_id, birth_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, gender, phone, email, tg_id, birth_date)
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()