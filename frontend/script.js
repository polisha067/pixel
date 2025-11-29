// ИИ-ассистент для ответов на письма
// Глобальные переменные
let currentResponse = '';

// API endpoint - используем относительный путь
const API_BASE = '';

// DOM элементы
const letterText = document.getElementById('letter-text');
const generateBtn = document.getElementById('generate-btn');
const responseSection = document.getElementById('response-section');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

// Инициализация обработчиков событий
function initializeEventListeners() {
    // Генерация ответа
    generateBtn.addEventListener('click', generateResponse);
}

// Генерация ответа
async function generateResponse() {
    const text = letterText.value.trim();

    if (!text) {
        showStatusMessage('Пожалуйста, введите текст письма', 'error');
        return;
    }

    // Показываем загрузку
    generateBtn.innerHTML = '<div class="loading"></div> Генерируем...';
    generateBtn.disabled = true;

    try {
        const url = `${API_BASE}/mail_generator`;
        console.log('Sending request to:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: text })
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const result = await response.json();
        console.log('Response received:', result);
        
        if (result.content) {
            displayGeneratedResponse(result.content);
        } else {
            throw new Error('Response does not contain content field');
        }

    } catch (error) {
        console.error('Error generating response:', error);
        let errorMessage = 'Ошибка при генерации ответа. ';
        
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage += 'Не удалось подключиться к серверу. Проверьте, что сервер запущен на http://localhost:8001';
        } else if (error.message.includes('HTTP error')) {
            errorMessage += `Ошибка сервера: ${error.message}`;
        } else {
            errorMessage += error.message;
        }
        
        showStatusMessage(errorMessage, 'error');
    } finally {
        generateBtn.innerHTML = 'Сгенерировать ответ';
        generateBtn.disabled = false;
    }
}

// Отображение сгенерированного ответа
function displayGeneratedResponse(response) {
    currentResponse = response;
    document.getElementById('response-text').textContent = response;
    responseSection.style.display = 'block';

    showStatusMessage('Ответ успешно сгенерирован!', 'success');
}

// Показать сообщение статуса
function showStatusMessage(message, type) {
    // Удаляем предыдущие сообщения
    const existingMessages = document.querySelectorAll('.status-message');
    existingMessages.forEach(msg => msg.remove());

    // Создаем новое сообщение
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message status-${type}`;
    messageDiv.textContent = message;

    // Добавляем в начало main
    const main = document.querySelector('main');
    main.insertBefore(messageDiv, main.firstChild);

    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

