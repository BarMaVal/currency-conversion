# app.py
# Основное Flask-приложение для конвертера валют

from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import database

# Создаём приложение Flask
app = Flask(__name__)

# URL внешнего API
API_URL = "https://api.exchangerate-api.com/v4/latest/RUB"



# Функция получения курсов с API

def fetch_exchange_rates():
    """
    Получает актуальные курсы валют с внешнего API.
    Возвращает словарь: {'USD': 90.5, 'EUR': 98.2, ...}
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()

        data = response.json()
        base = data.get('base', 'RUB')
        api_rates = data.get('rates', {})

        rates = {}

        if base == 'RUB':
            # API вернул: 1 RUB = 0.011 USD
            # Нам нужно: 1 USD = 90.91 RUB
            for currency, rate in api_rates.items():
                if rate > 0:
                    rates[currency] = round(1 / rate, 4)
        else:
            # Если базовая валюта не RUB, конвертируем через кросс-курс
            if 'RUB' in api_rates:
                base_to_rub = api_rates['RUB']
                for currency, rate in api_rates.items():
                    if currency == 'RUB':
                        rates['RUB'] = 1.0
                    elif rate > 0:
                        rates[currency] = round(base_to_rub / rate, 4)

        rates['RUB'] = 1.0
        return rates

    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return None


def get_available_currencies_from_api():
    """
    Получает список всех доступных валют с внешнего API.
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        # API возвращает словарь rates: {"USD": 0.011, "EUR": 0.009, ...}
        currencies = list(data.get('rates', {}).keys())
        currencies.append('RUB')  # Добавляем сам рубль
        currencies = sorted(set(currencies))  # Убираем дубликаты и сортируем

        return currencies
    except:
        return None


# ️ МАРШРУТЫ (эндпоинты)


@app.route('/') #декоратор маршрутизации - регистрирует функцию index во внутреннем словаре маршрутов приложения
def index(): # endpoint - функция возвращающая то что будет показано на гл странице
    """Главная страница"""
    currencies = database.get_all_currencies() # извлекаем данные из бд

    # Если БД пуста — запрашиваем список валют с API
    if not currencies:
        api_currencies = get_available_currencies_from_api()
        if api_currencies:
            currencies = api_currencies
        else:
            # Фоллбэк на базовый список
            currencies = ['RUB', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'KZT', 'BYN', 'UAH']

    return render_template('index.html', currencies=currencies)


@app.route('/api/update-rates', methods=['POST'])
def update_rates():
    """Обновление курсов валют в БД"""
    rates = fetch_exchange_rates()

    if not rates:
        return jsonify({
            'success': False,
            'message': '❌ Не удалось получить курсы с API'
        }), 500

    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        database.save_exchange_rates(rates, update_time)
        return jsonify({
            'success': True,
            'message': f'✅ Курсы обновлены! {update_time}',
            'updated_at': update_time,
            'currencies_count': len(rates)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Ошибка БД: {str(e)}'
        }), 500


@app.route('/api/last-update', methods=['GET'])
def get_last_update():
    """Получить время последнего обновления"""
    last_update = database.get_last_update_time()

    if last_update:
        return jsonify({
            'success': True,
            'updated_at': last_update
        })
    else:
        return jsonify({
            'success': False,
            'message': '⚠️ Курсы ещё не обновлялись'
        }), 404


@app.route('/api/convert', methods=['POST'])
def convert_currency():
    """Конвертация валют"""
    data = request.get_json()

    # Валидация
    from_currency = data.get('from', '').upper()
    to_currency = data.get('to', '').upper()
    amount = data.get('amount')

    if not from_currency or not to_currency:
        return jsonify({
            'success': False,
            'message': '⚠️ Выберите обе валюты'
        }), 400

    try:
        amount = float(amount)
        if amount < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': '⚠️ Введите корректную сумму'
        }), 400

    # Получаем курсы из БД
    rate_from = database.get_currency_rate(from_currency)
    rate_to = database.get_currency_rate(to_currency)

    if rate_from is None:
        return jsonify({
            'success': False,
            'message': f'⚠️ Курс {from_currency} не найден. Обновите курсы!'
        }), 404

    if rate_to is None:
        return jsonify({
            'success': False,
            'message': f'⚠️ Курс {to_currency} не найден. Обновите курсы!'
        }), 404

    # Конвертация
    result = amount * rate_from / rate_to
    result = round(result, 2)

    return jsonify({
        'success': True,
        'result': result,
        'details': {
            'from': f'{amount} {from_currency}',
            'to': f'{result} {to_currency}',
            'rate_from_rub': rate_from,
            'rate_to_rub': rate_to
        }
    })


# =============================================================================
# 🚀 ЗАПУСК ПРИЛОЖЕНИЯ — должно быть В КОНЦЕ файла!
# =============================================================================
if __name__ == '__main__':
    # Инициализация БД
    database.init_db()

    # Запуск сервера
    app.run(debug=True, host='127.0.0.1', port=5000)