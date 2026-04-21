// static/script.js

document.addEventListener('DOMContentLoaded', function() {

    // === Элементы страницы ===
    const form = document.getElementById('convert-form');
    const btnUpdate = document.getElementById('btn-update');
    const lastUpdateSpan = document.getElementById('last-update');
    const updateMessage = document.getElementById('update-message');
    const resultBlock = document.getElementById('result-block');
    const conversionResult = document.getElementById('conversion-result');
    const conversionDetails = document.getElementById('conversion-details');
    const errorMessage = document.getElementById('error-message');

    // === Функция: показать сообщение об ошибке ===
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('d-none');
        // Скрыть через 5 секунд
        setTimeout(() => errorMessage.classList.add('d-none'), 5000);
    }

    // === Функция: скрыть все сообщения ===
    function clearMessages() {
        errorMessage.classList.add('d-none');
        resultBlock.classList.add('d-none');
        updateMessage.textContent = '';
    }

    // === ЗАПРОС 1: Получить время последнего обновления ===
    async function fetchLastUpdate() {
        try {
            const response = await fetch('/api/last-update');
            const data = await response.json();

            if (data.success) {
                lastUpdateSpan.textContent = data.updated_at;
                lastUpdateSpan.className = 'badge bg-success';
            } else {
                lastUpdateSpan.textContent = 'Не обновлялось';
                lastUpdateSpan.className = 'badge bg-warning text-dark';
            }
        } catch (error) {
            console.error('Ошибка при получении времени обновления:', error);
            lastUpdateSpan.textContent = 'Ошибка';
            lastUpdateSpan.className = 'badge bg-danger';
        }
    }

    // === ЗАПРОС 2: Обновить курсы валют ===
    btnUpdate.addEventListener('click', async function() {
        clearMessages();
        btnUpdate.disabled = true;
        btnUpdate.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Загрузка...';

        try {
            const response = await fetch('/api/update-rates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (data.success) {
                updateMessage.textContent = data.message;
                updateMessage.className = 'text-success small';
                lastUpdateSpan.textContent = data.updated_at;
                lastUpdateSpan.className = 'badge bg-success';
            } else {
                showError(data.message);
            }
        } catch (error) {
            showError('❌ Ошибка соединения с сервером');
            console.error(error);
        } finally {
            btnUpdate.disabled = false;
            btnUpdate.innerHTML = '🔄 Обновить курсы с внешнего API';
        }
    });

    // === ЗАПРОС 3: Конвертация валют (отправка формы через Ajax) ===
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // 🔥 Важно: отменяем стандартную отправку формы!

        clearMessages();

        // 1. Валидация на стороне клиента (дополнительная защита)
        const amount = document.getElementById('amount').value;
        const from = document.getElementById('from-currency').value;
        const to = document.getElementById('to-currency').value;

        if (!amount || parseFloat(amount) <= 0) {
            showError('⚠️ Введите корректную положительную сумму');
            return;
        }

        // 2. Подготовка данных для отправки
        const requestData = {
            from: from,
            to: to,
            amount: parseFloat(amount)
        };

        // 3. Отправка POST-запроса на сервер
        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)  // Преобразуем объект в JSON-строку
            });

            const data = await response.json();

            if (data.success) {
                // ✅ Показываем результат
                conversionResult.textContent = `${data.result} ${data.details.to.split(' ')[1]}`;
                conversionDetails.textContent = `Курс ${data.details.from.split(' ')[1]}: ${data.details.rate_from_rub} RUB | Курс ${data.details.to.split(' ')[1]}: ${data.details.rate_to_rub} RUB`;
                resultBlock.classList.remove('d-none');
            } else {
                // ❌ Показываем ошибку от сервера
                showError(data.message);
            }
        } catch (error) {
            showError('❌ Ошибка соединения с сервером');
            console.error('Ошибка конвертации:', error);
        }
    });

    // === При загрузке страницы: получить время обновления ===
    fetchLastUpdate();

    // === Дополнительно: автообновление времени каждые 30 секунд ===
    setInterval(fetchLastUpdate, 30000);
});
