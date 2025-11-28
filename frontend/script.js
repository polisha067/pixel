// Banking Assistant - Frontend JavaScript
// Глобальные переменные
let currentLetterType = '';
let currentResponseStyle = 'official';
let currentResponse = '';

// API endpoints
const API_BASE = 'http://localhost:8000/api';

// DOM элементы
const letterText = document.getElementById('letter-text');
const analyzeBtn = document.getElementById('analyze-btn');
const resultsSection = document.getElementById('results-section');
const responseSection = document.getElementById('response-section');
const workflowSection = document.getElementById('workflow-section');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateWorkflowStep('draft');
});

// Инициализация обработчиков событий
function initializeEventListeners() {
    // Анализ письма
    analyzeBtn.addEventListener('click', analyzeLetter);

    // Выбор стиля ответа
    document.querySelectorAll('.style-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            selectResponseStyle(this.dataset.style);
        });
    });

    // Генерация ответа
    document.getElementById('generate-btn').addEventListener('click', generateResponse);

    // Действия с ответом
    document.getElementById('approve-btn').addEventListener('click', approveResponse);
    document.getElementById('edit-btn').addEventListener('click', editResponse);
}

// Анализ письма
async function analyzeLetter() {
    const text = letterText.value.trim();

    if (!text) {
        showStatusMessage('Пожалуйста, введите текст письма', 'error');
        return;
    }

    // Показываем загрузку
    analyzeBtn.innerHTML = '<div class="loading"></div> Анализируем...';
    analyzeBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        displayAnalysisResults(result);

    } catch (error) {
        console.error('Error analyzing letter:', error);
        showStatusMessage('Ошибка при анализе письма. Проверьте подключение к серверу.', 'error');
    } finally {
        analyzeBtn.innerHTML = '🔍 Анализировать письмо';
        analyzeBtn.disabled = false;
    }
}

// Отображение результатов анализа
function displayAnalysisResults(result) {
    currentLetterType = result.type;

    // Заполняем результаты анализа
    document.getElementById('letter-type').textContent = result.type_display;
    document.getElementById('urgency').textContent = result.urgency_display;

    // Ключевые параметры
    const keyParamsList = document.getElementById('key-params');
    keyParamsList.innerHTML = '';
    result.key_params.forEach(param => {
        const li = document.createElement('li');
        li.textContent = param;
        keyParamsList.appendChild(li);
    });

    // Показываем секции
    resultsSection.style.display = 'block';
    responseSection.style.display = 'block';
    workflowSection.style.display = 'block';

    showStatusMessage('Письмо успешно проанализировано!', 'success');
}

// Выбор стиля ответа
function selectResponseStyle(style) {
    currentResponseStyle = style;

    // Обновляем активную кнопку
    document.querySelectorAll('.style-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-style="${style}"]`).classList.add('active');
}

// Генерация ответа
async function generateResponse() {
    if (!currentLetterType) {
        showStatusMessage('Сначала проанализируйте письмо', 'error');
        return;
    }

    const generateBtn = document.getElementById('generate-btn');
    generateBtn.innerHTML = '<div class="loading"></div> Генерируем...';
    generateBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                letter_type: currentLetterType,
                style: currentResponseStyle,
                original_text: letterText.value
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        displayGeneratedResponse(result.response);

    } catch (error) {
        console.error('Error generating response:', error);
        showStatusMessage('Ошибка при генерации ответа. Проверьте подключение к серверу.', 'error');
    } finally {
        generateBtn.innerHTML = '🚀 Сгенерировать ответ';
        generateBtn.disabled = false;
    }
}

// Отображение сгенерированного ответа
function displayGeneratedResponse(response) {
    currentResponse = response;
    document.getElementById('response-text').textContent = response;
    document.getElementById('response-output').style.display = 'block';

    updateWorkflowStep('review');
    showStatusMessage('Ответ успешно сгенерирован!', 'success');
}

// Одобрение ответа
function approveResponse() {
    updateWorkflowStep('approved');
    showStatusMessage('Ответ одобрен и готов к отправке!', 'success');

    // Имитация отправки
    setTimeout(() => {
        showStatusMessage('Письмо успешно отправлено!', 'success');
    }, 2000);
}

// Редактирование ответа
function editResponse() {
    const responseText = document.getElementById('response-text');
    const currentText = responseText.textContent;

    // Создаем textarea для редактирования
    const textarea = document.createElement('textarea');
    textarea.value = currentText;
    textarea.style.width = '100%';
    textarea.style.minHeight = '200px';
    textarea.style.marginBottom = '10px';

    // Заменяем текст на textarea
    responseText.innerHTML = '';
    responseText.appendChild(textarea);

    // Создаем кнопку сохранения
    const saveBtn = document.createElement('button');
    saveBtn.textContent = '💾 Сохранить изменения';
    saveBtn.className = 'btn btn-success';
    saveBtn.onclick = function() {
        currentResponse = textarea.value;
        responseText.textContent = currentResponse;
        showStatusMessage('Изменения сохранены!', 'success');
    };

    responseText.appendChild(saveBtn);
}

// Обновление статуса workflow
function updateWorkflowStep(step) {
    // Сбрасываем все шаги
    document.querySelectorAll('.step').forEach(s => {
        s.classList.remove('active', 'completed');
    });

    // Активируем текущий шаг
    const currentStep = document.getElementById(`step-${step}`);
    if (currentStep) {
        currentStep.classList.add('active');

        // Помечаем предыдущие шаги как завершенные
        const steps = ['draft', 'review', 'approved'];
        const currentIndex = steps.indexOf(step);
        for (let i = 0; i < currentIndex; i++) {
            document.getElementById(`step-${steps[i]}`).classList.add('completed');
        }
    }
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

// Вспомогательные функции для демонстрации
function getDemoAnalysis() {
    return {
        type: 'complaint',
        type_display: 'Жалоба/Претензия',
        urgency: 'high',
        urgency_display: 'Высокая срочность (ответ в течение 3 дней)',
        key_params: [
            'Недовольство качеством обслуживания',
            'Требование компенсации',
            'Угроза обращения в суд',
            'Сумма претензии: 50 000 руб.'
        ]
    };
}

function getDemoResponse(style) {
    const responses = {
        official: `Уважаемые господа!

В ответ на Вашу жалобу от [дата] относительно качества предоставленных услуг сообщаем следующее:

Банк внимательно рассмотрел все обстоятельства, изложенные в Вашем обращении. Мы приносим искренние извинения за доставленные неудобства.

В целях урегулирования ситуации нами принято решение о:
1. Предоставлении компенсации в размере 50 000 рублей
2. Улучшении качества обслуживания по данному направлению

Просим Вас предоставить необходимые реквизиты для перечисления компенсации.

С уважением,
Начальник управления по работе с клиентами
[ФИО]`,
        business: `Добрый день!

Благодарим Вас за обращение и информацию о возникших проблемах с качеством обслуживания.

Мы провели внутреннее расследование и выявили причины сложившейся ситуации. Приносим извинения за причиненные неудобства.

Для компенсации неудобств мы подготовили следующие меры:
- Возврат полной суммы комиссии
- Предоставление премиального обслуживания на 3 месяца
- Персональный менеджер для сопровождения

Будем благодарны за подтверждение Вашего согласия с предложенными условиями.

С наилучшими пожеланиями,
Менеджер по работе с клиентами`,
        client: `Здравствуйте!

Огромное спасибо, что Вы сообщили нам о своей проблеме. Мы всегда стремимся предоставлять лучший сервис нашим клиентам, и Ваша обратная связь очень важна для нас.

Мы полностью понимаем Ваше разочарование и хотели бы загладить эту ситуацию. В качестве извинения мы:
- Вернем Вам всю сумму комиссии
- Предоставим повышенный процент по вкладу на 6 месяцев
- Организуем персональное обслуживание

Пожалуйста, дайте нам знать, если этот вариант Вас устраивает, или если есть что-то еще, чем мы можем помочь.

Мы ценим Ваше доверие и надеемся на дальнейшее сотрудничество.

С уважением,
Ваша команда поддержки`
    };

    return responses[style] || responses.business;
}
