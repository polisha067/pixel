/**
 * Логика интерфейса сотрудника
 * 
 * Этот файл содержит функции для:
 * - Просмотра назначенных писем
 * - Работы с письмом (открытие, редактирование)
 * - Чата с нейросетью для редактирования ответа
 * - Отправки финального ответа
 */

// ID текущего сотрудника
let currentEmployeeId = null;
let currentLetterId = null;

/**
 * Инициализация страницы сотрудника
 */
function initEmployeePage() {
    const savedEmployeeId = localStorage.getItem('employeeId');
    
    if (!savedEmployeeId) {
        showRegistrationForm();
    } else {
        currentEmployeeId = parseInt(savedEmployeeId);
        loadEmployeeInterface();
    }
}

/**
 * Показать форму регистрации сотрудника
 */
function showRegistrationForm() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <header>
            <h1>Регистрация сотрудника</h1>
        </header>
        <form id="registrationForm" class="registration-form">
            <div class="form-group">
                <label for="employeeName">Ваше имя:</label>
                <input type="text" id="employeeName" required>
            </div>
            <div class="form-group">
                <label for="employeeEmail">Email:</label>
                <input type="email" id="employeeEmail" required>
            </div>
            <div class="form-group">
                <label for="employeeDepartment">Отдел:</label>
                <input type="text" id="employeeDepartment" placeholder="Например: Отдел кредитования">
            </div>
            <div class="form-group">
                <label for="employeeCategory">Категория услуг:</label>
                <select id="employeeCategory" required>
                    <option value="">Выберите категорию</option>
                    <option value="credit">Кредиты</option>
                    <option value="insurance">Страхование (ОСАГО, КАСКО)</option>
                    <option value="mortgage">Ипотека</option>
                    <option value="deposit">Вклады и депозиты</option>
                    <option value="cards">Банковские карты</option>
                    <option value="business">Бизнес-услуги</option>
                    <option value="investment">Инвестиции</option>
                    <option value="online_banking">Интернет-банкинг</option>
                    <option value="currency">Валютные операции</option>
                    <option value="other">Прочее</option>
                </select>
            </div>
            <button type="submit">Зарегистрироваться</button>
        </form>
        <div id="message"></div>
    `;
    
    document.getElementById('registrationForm').addEventListener('submit', handleEmployeeRegistration);
}

/**
 * Обработка регистрации сотрудника
 */
async function handleEmployeeRegistration(e) {
    e.preventDefault();
    
    const name = document.getElementById('employeeName').value;
    const email = document.getElementById('employeeEmail').value;
    const department = document.getElementById('employeeDepartment').value;
    const category = document.getElementById('employeeCategory').value;
    const messageDiv = document.getElementById('message');
    
    messageDiv.innerHTML = '<div class="loading">Регистрация...</div>';
    
    try {
        const employee = await registerEmployee(name, email, department, category);
        
        currentEmployeeId = employee.id;
        localStorage.setItem('employeeId', employee.id);
        localStorage.setItem('employeeName', employee.user.name);
        localStorage.setItem('employeeCategory', category);
        
        messageDiv.innerHTML = '<div class="success">Регистрация успешна!</div>';
        
        setTimeout(() => {
            loadEmployeeInterface();
        }, 1000);
    
    } catch (error) {
        messageDiv.innerHTML = `<div class="error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Загрузить интерфейс сотрудника
 */
function loadEmployeeInterface() {
    const employeeName = localStorage.getItem('employeeName') || 'Сотрудник';
    const category = localStorage.getItem('employeeCategory') || '';
    
    const container = document.querySelector('.container');
    container.innerHTML = `
        <header>
            <h1>👔 Личный кабинет сотрудника</h1>
            <p class="subtitle">Добро пожаловать, ${employeeName}! Категория: ${getCategoryName(category)}</p>
        </header>
        
        <nav style="margin-bottom: 20px;">
            <button onclick="window.location.href='index.html'">← Назад</button>
        </nav>
        
        <!-- Фильтр по статусу -->
        <div style="margin-bottom: 20px;">
            <label>Фильтр по статусу: </label>
            <select id="statusFilter" onchange="loadEmployeeLetters()">
                <option value="">Все</option>
                <option value="waiting">Ожидание</option>
                <option value="in_progress">В работе</option>
                <option value="sent">Отправлено</option>
            </select>
        </div>
        
        <!-- Список писем -->
        <section>
            <h2>📬 Назначенные обращения</h2>
            <div id="lettersList" class="letters-list">
                <div class="loading">Загрузка...</div>
            </div>
        </section>
        
        <!-- Модальное окно для работы с письмом -->
        <div id="letterModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Работа с обращением</h2>
                    <span class="close" onclick="closeLetterModal()">&times;</span>
                </div>
                <div id="letterModalContent">
                    <!-- Контент загружается динамически -->
                </div>
            </div>
        </div>
    `;
    
    loadEmployeeLetters();
}

/**
 * Загрузить список писем сотрудника
 */
async function loadEmployeeLetters() {
    const lettersList = document.getElementById('lettersList');
    if (!lettersList) return;
    
    const statusFilter = document.getElementById('statusFilter')?.value || null;
    
    lettersList.innerHTML = '<div class="loading">Загрузка писем...</div>';
    
    try {
        const letters = await getEmployeeLetters(currentEmployeeId, statusFilter);
        
        if (letters.length === 0) {
            lettersList.innerHTML = '<p style="text-align: center; color: #666;">Нет назначенных обращений</p>';
            return;
        }
        
        lettersList.innerHTML = letters.map(letter => `
            <div class="letter-card" onclick="openLetter(${letter.id})" style="cursor: pointer;">
                <div class="letter-header">
                    <span class="letter-id">Обращение #${letter.id}</span>
                    <span class="letter-status status-${letter.status}">
                        ${getStatusName(letter.status)}
                    </span>
                </div>
                <div class="letter-text">${escapeHtml(letter.text.substring(0, 200))}${letter.text.length > 200 ? '...' : ''}</div>
                <div class="letter-meta">
                    <span>📅 ${formatDate(letter.created_at)}</span>
                    <span>🏷️ ${getCategoryName(letter.category)}</span>
                </div>
            </div>
        `).join('');
    
    } catch (error) {
        lettersList.innerHTML = `<div class="error">Ошибка при загрузке писем: ${error.message}</div>`;
    }
}

/**
 * Открыть письмо для работы
 */
async function openLetter(letterId) {
    currentLetterId = letterId;
    const modal = document.getElementById('letterModal');
    const content = document.getElementById('letterModalContent');
    
    modal.style.display = 'block';
    content.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const letter = await getEmployeeLetter(letterId, currentEmployeeId);
        
        content.innerHTML = `
            <div class="letter-details">
                <h3>Обращение от клиента:</h3>
                <div class="letter-text" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    ${escapeHtml(letter.text)}
                </div>
                
                <h3>Черновик ответа (от нейросети):</h3>
                <div id="draftResponse" style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px; white-space: pre-wrap;">
                    ${escapeHtml(letter.draft_response || 'Черновик еще не создан')}
                </div>
                
                <h3>💬 Чат для редактирования ответа:</h3>
                <div class="chat-container">
                    <div id="chatMessages" class="chat-messages">
                        <!-- Сообщения загружаются отдельно -->
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chatInput" placeholder="Например: 'Сделай ответ более вежливым' или 'Добавь информацию о документах'">
                        <button onclick="sendChatMessageToAI()">Отправить</button>
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <h3>Финальный ответ:</h3>
                    <textarea id="finalResponse" style="width: 100%; min-height: 150px; margin-bottom: 10px;">${escapeHtml(letter.draft_response || '')}</textarea>
                    <button class="btn-success" onclick="sendFinalResponseToUser()">Отправить ответ пользователю</button>
                </div>
            </div>
        `;
        
        // Загружаем историю чата
        loadChatMessages(letterId);
        
        // Устанавливаем обработчик Enter для чата
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessageToAI();
            }
        });
    
    } catch (error) {
        content.innerHTML = `<div class="error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Загрузить историю чата
 */
async function loadChatMessages(letterId) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    try {
        const messages = await getChatMessages(letterId, currentEmployeeId);
        
        if (messages.length === 0) {
            chatMessages.innerHTML = '<p style="color: #666; text-align: center;">История чата пуста</p>';
            return;
        }
        
        chatMessages.innerHTML = messages.map(msg => `
            <div class="chat-message message-${msg.role}">
                <strong>${msg.role === 'employee' ? 'Вы' : 'Ассистент'}:</strong>
                <p style="margin-top: 5px;">${escapeHtml(msg.message)}</p>
                <small style="opacity: 0.7;">${formatDate(msg.timestamp)}</small>
            </div>
        `).join('');
        
        // Прокручиваем вниз
        chatMessages.scrollTop = chatMessages.scrollHeight;
    
    } catch (error) {
        console.error('Ошибка при загрузке чата:', error);
    }
}

/**
 * Отправить сообщение в чат для редактирования ответа
 */
async function sendChatMessageToAI() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) {
        alert('Введите сообщение');
        return;
    }
    
    const chatMessages = document.getElementById('chatMessages');
    const draftResponse = document.getElementById('draftResponse');
    const finalResponse = document.getElementById('finalResponse');
    
    // Добавляем сообщение сотрудника в чат сразу
    chatMessages.innerHTML += `
        <div class="chat-message message-employee">
            <strong>Вы:</strong>
            <p style="margin-top: 5px;">${escapeHtml(message)}</p>
        </div>
    `;
    
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Показываем загрузку
    chatMessages.innerHTML += '<div class="loading">Ассистент думает...</div>';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await sendChatMessage(currentLetterId, currentEmployeeId, message);
        
        // Убираем загрузку
        chatMessages.innerHTML = chatMessages.innerHTML.replace('<div class="loading">Ассистент думает...</div>', '');
        
        // Добавляем ответ ассистента
        chatMessages.innerHTML += `
            <div class="chat-message message-assistant">
                <strong>Ассистент:</strong>
                <p style="margin-top: 5px;">${escapeHtml(response.improved_response)}</p>
            </div>
        `;
        
        // Обновляем черновик и финальный ответ
        draftResponse.textContent = response.updated_draft;
        finalResponse.value = response.updated_draft;
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    
    } catch (error) {
        chatMessages.innerHTML = chatMessages.innerHTML.replace('<div class="loading">Ассистент думает...</div>', '');
        chatMessages.innerHTML += `<div class="error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Отправить финальный ответ пользователю
 */
async function sendFinalResponseToUser() {
    const finalResponse = document.getElementById('finalResponse');
    const responseText = finalResponse.value.trim();
    
    if (!responseText) {
        alert('Введите текст ответа');
        return;
    }
    
    if (!confirm('Отправить ответ пользователю?')) {
        return;
    }
    
    try {
        await sendFinalResponse(currentLetterId, currentEmployeeId, responseText);
        
        alert('Ответ успешно отправлен пользователю!');
        
        // Закрываем модальное окно
        closeLetterModal();
        
        // Обновляем список писем
        loadEmployeeLetters();
    
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

/**
 * Закрыть модальное окно письма
 */
function closeLetterModal() {
    document.getElementById('letterModal').style.display = 'none';
    currentLetterId = null;
}

/**
 * Получить название статуса
 */
function getStatusName(status) {
    const statusNames = {
        'waiting': 'Ожидание',
        'in_progress': 'В работе',
        'sent': 'Отправлено',
        'closed': 'Закрыто'
    };
    return statusNames[status] || status;
}

/**
 * Получить название категории
 */
function getCategoryName(category) {
    const categoryNames = {
        'credit': 'Кредиты',
        'insurance': 'Страхование',
        'mortgage': 'Ипотека',
        'deposit': 'Вклады',
        'cards': 'Карты',
        'business': 'Бизнес',
        'investment': 'Инвестиции',
        'online_banking': 'Интернет-банкинг',
        'currency': 'Валюта',
        'other': 'Прочее'
    };
    return categoryNames[category] || category;
}

/**
 * Форматировать дату
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

/**
 * Экранировать HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEmployeePage);
} else {
    initEmployeePage();
}

