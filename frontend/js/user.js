/**
 * Логика интерфейса пользователя (клиента банка)
 * 
 * Этот файл содержит функции для:
 * - Отправки обращений
 * - Просмотра своих писем
 * - Просмотра ответов на письма
 */

// ID текущего пользователя (в реальном приложении получается при авторизации)
let currentUserId = null;

/**
 * Инициализация страницы пользователя
 * Загружается при открытии страницы user.html
 */
function initUserPage() {
    // Пытаемся получить ID пользователя из localStorage
    // В реальном приложении это делается через авторизацию
    const savedUserId = localStorage.getItem('userId');
    
    if (!savedUserId) {
        // Если пользователь не авторизован, показываем форму регистрации
        showRegistrationForm();
    } else {
        // Если авторизован, загружаем интерфейс
        currentUserId = parseInt(savedUserId);
        loadUserInterface();
    }
    
    // Обработчик формы отправки письма
    const letterForm = document.getElementById('letterForm');
    if (letterForm) {
        letterForm.addEventListener('submit', handleSendLetter);
    }
}

/**
 * Показать форму регистрации
 */
function showRegistrationForm() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <header>
            <h1>Регистрация пользователя</h1>
        </header>
        <form id="registrationForm" class="registration-form">
            <div class="form-group">
                <label for="userName">Ваше имя:</label>
                <input type="text" id="userName" required>
            </div>
            <div class="form-group">
                <label for="userEmail">Email:</label>
                <input type="email" id="userEmail" required>
            </div>
            <button type="submit">Зарегистрироваться</button>
        </form>
        <div id="message"></div>
    `;
    
    document.getElementById('registrationForm').addEventListener('submit', handleRegistration);
}

/**
 * Обработка регистрации пользователя
 */
async function handleRegistration(e) {
    e.preventDefault();
    
    const name = document.getElementById('userName').value;
    const email = document.getElementById('userEmail').value;
    const messageDiv = document.getElementById('message');
    
    messageDiv.innerHTML = '<div class="loading">Регистрация...</div>';
    
    try {
        const user = await registerUser(name, email);
        
        // Сохраняем ID пользователя
        currentUserId = user.id;
        localStorage.setItem('userId', user.id);
        localStorage.setItem('userName', user.name);
        
        messageDiv.innerHTML = '<div class="success">Регистрация успешна!</div>';
        
        // Загружаем интерфейс пользователя
        setTimeout(() => {
            loadUserInterface();
        }, 1000);
    
    } catch (error) {
        messageDiv.innerHTML = `<div class="error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Загрузить интерфейс пользователя
 */
function loadUserInterface() {
    const userName = localStorage.getItem('userName') || 'Пользователь';
    
    const container = document.querySelector('.container');
    container.innerHTML = `
        <header>
            <h1>👤 Личный кабинет пользователя</h1>
            <p class="subtitle">Добро пожаловать, ${userName}!</p>
        </header>
        
        <nav style="margin-bottom: 20px;">
            <button onclick="window.location.href='index.html'">← Назад</button>
        </nav>
        
        <!-- Форма отправки письма -->
        <section class="send-letter-section">
            <h2>📝 Отправить обращение в банк</h2>
            <form id="letterForm">
                <div class="form-group">
                    <label for="letterText">Текст обращения:</label>
                    <textarea id="letterText" required placeholder="Опишите ваш вопрос или обращение..."></textarea>
                </div>
                <button type="submit">Отправить обращение</button>
            </form>
            <div id="letterMessage"></div>
        </section>
        
        <!-- Список моих писем -->
        <section class="my-letters-section" style="margin-top: 40px;">
            <h2>📬 Мои обращения</h2>
            <div id="lettersList" class="letters-list">
                <div class="loading">Загрузка...</div>
            </div>
        </section>
    `;
    
    // Добавляем обработчик формы
    document.getElementById('letterForm').addEventListener('submit', handleSendLetter);
    
    // Загружаем список писем
    loadMyLetters();
}

/**
 * Обработка отправки письма
 */
async function handleSendLetter(e) {
    e.preventDefault();
    
    const text = document.getElementById('letterText').value;
    const messageDiv = document.getElementById('letterMessage');
    
    if (!text.trim()) {
        messageDiv.innerHTML = '<div class="error">Пожалуйста, введите текст обращения</div>';
        return;
    }
    
    messageDiv.innerHTML = '<div class="loading">Отправка обращения...</div>';
    
    try {
        const letter = await sendLetter(currentUserId, text);
        
        messageDiv.innerHTML = '<div class="success">Обращение успешно отправлено! Ожидайте ответа.</div>';
        
        // Очищаем форму
        document.getElementById('letterText').value = '';
        
        // Обновляем список писем
        loadMyLetters();
    
    } catch (error) {
        messageDiv.innerHTML = `<div class="error">Ошибка при отправке: ${error.message}</div>`;
    }
}

/**
 * Загрузить список писем пользователя
 */
async function loadMyLetters() {
    const lettersList = document.getElementById('lettersList');
    
    if (!lettersList) return;
    
    lettersList.innerHTML = '<div class="loading">Загрузка писем...</div>';
    
    try {
        const letters = await getMyLetters(currentUserId);
        
        if (letters.length === 0) {
            lettersList.innerHTML = '<p style="text-align: center; color: #666;">У вас пока нет обращений</p>';
            return;
        }
        
        lettersList.innerHTML = letters.map(letter => `
            <div class="letter-card">
                <div class="letter-header">
                    <span class="letter-id">Обращение #${letter.id}</span>
                    <span class="letter-status status-${letter.status}">
                        ${getStatusName(letter.status)}
                    </span>
                </div>
                <div class="letter-text">${escapeHtml(letter.text)}</div>
                <div class="letter-meta">
                    <span>📅 ${formatDate(letter.created_at)}</span>
                    <span>🏷️ ${getCategoryName(letter.category)}</span>
                </div>
                ${letter.final_response ? `
                    <div style="margin-top: 15px; padding: 15px; background: #e9ecef; border-radius: 8px;">
                        <strong>Ответ банка:</strong>
                        <p style="margin-top: 10px;">${escapeHtml(letter.final_response)}</p>
                    </div>
                ` : letter.draft_response ? `
                    <div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                        <strong>Статус:</strong> Ответ готовится
                    </div>
                ` : ''}
            </div>
        `).join('');
    
    } catch (error) {
        lettersList.innerHTML = `<div class="error">Ошибка при загрузке писем: ${error.message}</div>`;
    }
}

/**
 * Получить название статуса на русском
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
 * Получить название категории на русском
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
 * Форматировать дату для отображения
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

/**
 * Экранировать HTML для безопасности
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUserPage);
} else {
    initUserPage();
}

