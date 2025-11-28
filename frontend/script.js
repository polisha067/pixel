// Конфигурация
const API_BASE_URL = 'http://127.0.0.1:8001';

// Получаем элементы DOM
const emailInput = document.getElementById('emailInput');
const generateBtn = document.getElementById('generateBtn');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const error = document.getElementById('error');
const generatedEmail = document.getElementById('generatedEmail');

// Основная функция генерации email
async function generateEmail() {
    console.log('Функция generateEmail вызвана'); // Для отладки

    const emailText = emailInput.value.trim();

    // Валидация
    if (!emailText) {
        showError('Пожалуйста, введите текст письма');
        return;
    }

    // Сброс состояний
    hideError();
    hideResult();
    setLoading(true);

    try {
        console.log('Отправка запроса к API...');

        const response = await fetch(`${API_BASE_URL}/mail_generator`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: emailText
            })
        });

        console.log('Получен ответ:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
        }

        const data = await response.json();
        console.log('Данные получены:', data);

        // Показываем результат
        displayResult(data.content);

    } catch (err) {
        console.error('Ошибка:', err);
        showError(`Ошибка: ${err.message}`);
    } finally {
        setLoading(false);
    }
}

// Функции для управления UI
function setLoading(isLoading) {
    if (isLoading) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Генерация...';
        loading.style.display = 'block';
    } else {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Сгенерировать ответ';
        loading.style.display = 'none';
    }
}

function displayResult(content) {
    generatedEmail.textContent = content;
    result.style.display = 'block';
    error.style.display = 'none';
}

function hideResult() {
    result.style.display = 'none';
}

function showError(message) {
    error.textContent = message;
    error.style.display = 'block';
    result.style.display = 'none';
}

function hideError() {
    error.style.display = 'none';
}

// Добавляем обработчики событий
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, добавляем обработчики...');

    // Обработчик для кнопки
    generateBtn.addEventListener('click', generateEmail);

    // Обработчик для Enter в текстовом поле
    emailInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            generateEmail();
        }
    });

    console.log('Обработчики добавлены');
});

// Для отладки - проверяем, что элементы найдены
console.log('Элементы DOM:');
console.log('generateBtn:', generateBtn);
console.log('emailInput:', emailInput);
console.log('loading:', loading);
console.log('result:', result);