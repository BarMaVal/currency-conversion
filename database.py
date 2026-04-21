# database.py
# Модуль для работы с базой данных SQLite
# Объяснение для учеников: здесь мы создаём таблицу, сохраняем и получаем данные

import sqlite3
from datetime import datetime
import os

# Путь к базе данных
DB_PATH = 'currencies.db'


def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к полям по имени, а не по индексам
    return conn


def init_db():
    """
    Инициализирует базу данных: создаёт таблицу, если она не существует.
    Таблица хранит: код валюты, курс к рублю, дату обновления.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency_code TEXT UNIQUE NOT NULL,  
            rate_to_rub REAL NOT NULL,            
            updated_at TEXT NOT NULL              
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def save_exchange_rates(rates_data: dict, update_time: str):
    """
    Сохраняет или обновляет курсы валют в базе данных.

    :param rates_data: словарь {код_валюты: курс_к_рублю}
    :param update_time: строка с датой и временем обновления
    """
    conn = get_connection()
    cursor = conn.cursor()

    for currency, rate in rates_data.items():
        # INSERT OR REPLACE — если запись с таким currency_code есть, обновит её
        cursor.execute('''
            INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_rub, updated_at)
            VALUES (?, ?, ?)
        ''', (currency, rate, update_time))

    conn.commit()
    conn.close()
    print(f"✅ Сохранено курсов: {len(rates_data)}")


def get_last_update_time():
    """
    Возвращает дату и время последнего обновления курсов.
    Если данных нет — возвращает None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(updated_at) as last_update FROM exchange_rates')
    result = cursor.fetchone()

    conn.close()

    return result['last_update'] if result and result['last_update'] else None


def get_currency_rate(currency_code: str):
    """
    Получает курс конкретной валюты к рублю из базы данных.

    :param currency_code: код валюты (например, 'USD')
    :return: курс (float) или None, если валюта не найдена
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT rate_to_rub FROM exchange_rates WHERE currency_code = ?',
        (currency_code.upper(),)
    )
    result = cursor.fetchone()

    conn.close()

    return result['rate_to_rub'] if result else None


def get_all_currencies():
    """
    Возвращает список всех доступных кодов валют из базы.
    Полезно для формирования выпадающих списков в интерфейсе.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT currency_code FROM exchange_rates ORDER BY currency_code')
    currencies = [row['currency_code'] for row in cursor.fetchall()]

    conn.close()

    return currencies