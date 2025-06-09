from datetime import datetime, timedelta
import psycopg2
from psycopg2 import OperationalError
from typing import Optional, List, Tuple
from enum import Enum
import os


class Weekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

CLINIC_WORK_HOURS = {
    Weekday.MONDAY: (7, 30, 20, 0),
    Weekday.TUESDAY: (7, 30, 20, 0),
    Weekday.WEDNESDAY: (7, 30, 20, 0),
    Weekday.THURSDAY: (7, 30, 20, 0),
    Weekday.FRIDAY: (7, 30, 20, 0),
    Weekday.SATURDAY: (8, 0, 17, 0),
    Weekday.SUNDAY: (8, 0, 15, 0),
}


def create_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
        )
        return conn
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


def get_doctor_schedule(doctor_id: int) -> List[Tuple[int, int]]:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT weekday 
                FROM DoctorSchedules 
                WHERE doctor_id = %s
            """, (doctor_id,))
            return [row[0] for row in cursor.fetchall()]
    except psycopg2.Error as e:
        print(f"Ошибка при получении расписания врача: {e}")
        return []
    finally:
        conn.close()


def generate_available_dates(doctor_id: int, days_ahead: int = 30) -> List[datetime.date]:
    doctor_schedule = get_doctor_schedule(doctor_id)
    if not doctor_schedule:
        return []

    available_dates = []
    today = datetime.now().date()

    for day in range(days_ahead):
        current_date = today + timedelta(days=day)
        weekday = current_date.weekday()

        if weekday in doctor_schedule:
            available_dates.append(current_date)

    return available_dates


def generate_available_times(doctor_id: int, date: datetime.date) -> List[datetime.time]:
    weekday = Weekday(date.weekday())
    if weekday not in CLINIC_WORK_HOURS:
        return []

    start_hour, start_minute, end_hour, end_minute = CLINIC_WORK_HOURS[weekday]
    start_time = datetime.combine(date, datetime.min.time()).replace(hour=start_hour, minute=start_minute)
    end_time = datetime.combine(date, datetime.min.time()).replace(hour=end_hour, minute=end_minute)

    existing_appointments = get_existing_appointments(doctor_id, date)
    booked_times = {appt.time() for appt in existing_appointments}

    available_times = []
    current_time = start_time

    while current_time < end_time:
        if current_time.time() not in booked_times:
            available_times.append(current_time.time())
        current_time += timedelta(hours=1)

    return available_times


def get_existing_appointments(doctor_id: int, date: datetime.date) -> List[datetime.date]:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT appointment_date 
                FROM Appointments 
                WHERE doctor_id = %s AND DATE(appointment_date) = %s AND status = 'scheduled'
            """, (doctor_id, date))
            return [row[0] for row in cursor.fetchall()]
    except psycopg2.Error as e:
        print(f"Ошибка при получении записей: {e}")
        return []
    finally:
        conn.close()


def create_appointment(tg_id: int, doctor_id: int, date: str, time: str) -> bool:
    conn = create_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM Users WHERE tg_id = %s", (str(tg_id),))
            user_row = cursor.fetchone()
            if not user_row:
                print(f"Пользователь с tg_id={tg_id} не найден")
                return False

            user_id = user_row[0]

            appointment_datetime = f"{date} {time}"
            cursor.execute("""
                INSERT INTO Appointments (user_id, doctor_id, appointment_date, status)
                VALUES (%s, %s, %s, 'scheduled')
            """, (user_id, doctor_id, appointment_datetime))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Ошибка при создании записи: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


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


def get_doctors() -> list:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.doctor_id, d.first_name, d.last_name, s.name as specialization 
                FROM Doctors d
                JOIN Specializations s ON d.specialization_id = s.specialization_id
            """)
            return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"Ошибка при получении списка врачей: {e}")
        return []
    finally:
        conn.close()


def get_doctor_info(doctor_id: int) -> Optional[dict]:
    conn = create_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.doctor_id, 
                    d.first_name, 
                    d.last_name, 
                    d.phone, 
                    d.email, 
                    d.description,
                    s.name AS specialization,
                    s.description AS specialization_description
                FROM Doctors d
                JOIN Specializations s ON d.specialization_id = s.specialization_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "doctor_id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "phone": row[3],
                    "email": row[4],
                    "description": row[5],
                    "specialization": row[6],
                    "specialization_description": row[7],
                }
            else:
                return None
    except psycopg2.Error as e:
        print(f"Ошибка при получении информации о враче: {e}")
        return None
    finally:
        conn.close()

def get_doctors_by_specialization(specialization: str) -> list:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.doctor_id, d.first_name, d.last_name, s.name as specialization 
                FROM Doctors d
                JOIN Specializations s ON d.specialization_id = s.specialization_id
                WHERE s.name ILIKE %s
            """, (f"%{specialization}%",))
            return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"Ошибка при получении врачей по специализации: {e}")
        return []
    finally:
        conn.close()


def get_user_data(tg_id: str) -> Optional[dict]:
    conn = create_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    user_id, first_name, last_name, gender, 
                    phone, email, birth_date
                FROM Users 
                WHERE tg_id = %s
            """, (tg_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "gender": row[3],
                    "phone": row[4],
                    "email": row[5],
                    "birth_date": row[6].strftime("%d.%m.%Y") if row[6] else None
                }
            return None
    except psycopg2.Error as e:
        print(f"Error getting user data: {e}")
        return None
    finally:
        conn.close()

def get_last_appointment(user_id: int) -> Optional[dict]:
    conn = create_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.appointment_id,
                    a.appointment_date,
                    d.first_name || ' ' || d.last_name as doctor_name,
                    s.name as specialization
                FROM Appointments a
                JOIN Doctors d ON a.doctor_id = d.doctor_id
                JOIN Specializations s ON d.specialization_id = s.specialization_id
                WHERE a.user_id = %s
                ORDER BY a.appointment_date DESC
                LIMIT 1
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "appointment_id": row[0],
                    "date": row[1].strftime("%d.%m.%Y"),
                    "time": row[1].strftime("%H:%M"),
                    "doctor_name": row[2],
                    "specialization": row[3]
                }
            return None
    except psycopg2.Error as e:
        print(f"Error getting last appointment: {e}")
        return None
    finally:
        conn.close()


def get_doctor_data(doctor_id: int) -> Optional[dict]:
    conn = create_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.first_name, d.last_name,
                    s.name as specialization
                FROM Doctors d
                JOIN Specializations s ON d.specialization_id = s.specialization_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "first_name": row[0],
                    "last_name": row[1],
                    "specialization": row[2]
                }
            return None
    except psycopg2.Error as e:
        print(f"Error getting doctor data: {e}")
        return None
    finally:
        conn.close()


def get_user_diagnoses(user_id: int) -> List[dict]:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    diagnosis_name, diagnosis_date
                FROM Diagnoses
                WHERE user_id = %s
                ORDER BY diagnosis_date DESC
            """, (user_id,))

            return [
                {
                    "name": row[0],
                    "date": row[1].strftime("%d.%m.%Y")
                }
                for row in cursor.fetchall()
            ]
    except psycopg2.Error as e:
        print(f"Error getting user diagnoses: {e}")
        return []
    finally:
        conn.close()


def get_user_appointments(user_id: int) -> List[dict]:
    conn = create_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.appointment_id,
                    a.appointment_date,
                    d.first_name || ' ' || d.last_name as doctor_name,
                    s.name as specialization
                FROM Appointments a
                JOIN Doctors d ON a.doctor_id = d.doctor_id
                JOIN Specializations s ON d.specialization_id = s.specialization_id
                WHERE a.user_id = %s
                ORDER BY a.appointment_date DESC
                LIMIT 5
            """, (user_id,))

            return [
                {
                    "appointment_id": row[0],
                    "date": row[1].strftime("%d.%m.%Y"),
                    "time": row[1].strftime("%H:%M"),
                    "doctor_name": row[2],
                    "specialization": row[3]
                }
                for row in cursor.fetchall()
            ]
    except psycopg2.Error as e:
        print(f"Error getting user appointments: {e}")
        return []
    finally:
        conn.close()


def get_last_diagnosis(user_id: int) -> Optional[dict]:
    conn = create_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    diagnosis_name, diagnosis_date
                FROM Diagnoses
                WHERE user_id = %s
                ORDER BY diagnosis_date DESC
                LIMIT 1
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "date": row[1].strftime("%d.%m.%Y")
                }
            return None
    except psycopg2.Error as e:
        print(f"Error getting last diagnosis: {e}")
        return None
    finally:
        conn.close()