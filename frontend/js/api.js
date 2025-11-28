/**
 * Функции для работы с API
 * 
 * Этот файл содержит все функции для отправки запросов к backend API.
 * Используется на всех страницах для взаимодействия с сервером.
 */

// Базовый URL API (изменяйте при необходимости)
// Если порт 8000 занят, используйте 8001 или другой свободный порт
const API_BASE_URL = 'http://localhost:8001';

/**
 * Базовая функция для отправки HTTP запросов
 * 
 * @param {string} endpoint - Эндпоинт API (например, '/api/users/letters')
 * @param {string} method - HTTP метод ('GET', 'POST', 'PUT', 'DELETE')
 * @param {object} data - Данные для отправки (для POST/PUT запросов)
 * @returns {Promise} - Промис с ответом от сервера
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    // Формируем полный URL
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Настройки запроса
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    // Если есть данные, добавляем их в тело запроса
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        // Отправляем запрос
        const response = await fetch(url, options);
        
        // Проверяем статус ответа
        if (!response.ok) {
            // Если ошибка, пытаемся получить сообщение об ошибке
            const errorData = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        // Парсим JSON ответ
        const result = await response.json();
        return result;
    
    } catch (error) {
        console.error('Ошибка при запросе к API:', error);
        throw error;
    }
}

// ========== Функции для авторизации ==========

/**
 * Регистрация обычного пользователя
 */
async function registerUser(name, email) {
    return apiRequest('/api/auth/register/user', 'POST', {
        name: name,
        email: email,
        role: 'user'
    });
}

/**
 * Регистрация сотрудника
 */
async function registerEmployee(name, email, department, category) {
    return apiRequest('/api/auth/register/employee', 'POST', {
        name: name,
        email: email,
        department: department,
        category: category
    });
}

/**
 * Авторизация (простая, по email)
 */
async function login(email) {
    return apiRequest(`/api/auth/login?email=${encodeURIComponent(email)}`, 'GET');
}

// ========== Функции для пользователей ==========

/**
 * Отправить новое письмо
 * 
 * @param {number} userId - ID пользователя
 * @param {string} text - Текст письма
 */
async function sendLetter(userId, text) {
    return apiRequest(`/api/users/letters?user_id=${userId}`, 'POST', {
        text: text
    });
}

/**
 * Получить все письма пользователя
 * 
 * @param {number} userId - ID пользователя
 */
async function getMyLetters(userId) {
    return apiRequest(`/api/users/letters?user_id=${userId}`, 'GET');
}

/**
 * Получить конкретное письмо пользователя
 * 
 * @param {number} letterId - ID письма
 * @param {number} userId - ID пользователя
 */
async function getUserLetter(letterId, userId) {
    return apiRequest(`/api/users/letters/${letterId}?user_id=${userId}`, 'GET');
}

// ========== Функции для сотрудников ==========

/**
 * Получить все письма сотрудника
 * 
 * @param {number} employeeId - ID сотрудника
 * @param {string} status - Фильтр по статусу (опционально)
 */
async function getEmployeeLetters(employeeId, status = null) {
    let endpoint = `/api/employees/letters?employee_id=${employeeId}`;
    if (status) {
        endpoint += `&status=${status}`;
    }
    return apiRequest(endpoint, 'GET');
}

/**
 * Получить конкретное письмо для работы
 * 
 * @param {number} letterId - ID письма
 * @param {number} employeeId - ID сотрудника
 */
async function getEmployeeLetter(letterId, employeeId) {
    return apiRequest(`/api/employees/letters/${letterId}?employee_id=${employeeId}`, 'GET');
}

/**
 * Отправить сообщение в чат для редактирования ответа
 * 
 * @param {number} letterId - ID письма
 * @param {number} employeeId - ID сотрудника
 * @param {string} message - Сообщение от сотрудника
 */
async function sendChatMessage(letterId, employeeId, message) {
    return apiRequest(
        `/api/employees/letters/${letterId}/chat?employee_id=${employeeId}`,
        'POST',
        { message: message }
    );
}

/**
 * Получить историю чата для письма
 * 
 * @param {number} letterId - ID письма
 * @param {number} employeeId - ID сотрудника
 */
async function getChatMessages(letterId, employeeId) {
    return apiRequest(`/api/employees/letters/${letterId}/chat?employee_id=${employeeId}`, 'GET');
}

/**
 * Отправить финальный ответ пользователю
 * 
 * @param {number} letterId - ID письма
 * @param {number} employeeId - ID сотрудника
 * @param {string} finalResponse - Финальный текст ответа
 */
async function sendFinalResponse(letterId, employeeId, finalResponse) {
    return apiRequest(
        `/api/employees/letters/${letterId}/send?employee_id=${employeeId}`,
        'POST',
        { final_response: finalResponse }
    );
}

// ========== Функции для статистики ==========

/**
 * Получить общую статистику
 */
async function getOverviewStatistics() {
    return apiRequest('/api/statistics/overview', 'GET');
}

/**
 * Получить статистику по категориям
 */
async function getStatisticsByCategory() {
    return apiRequest('/api/statistics/by_category', 'GET');
}

/**
 * Получить статистику по сотруднику
 * 
 * @param {number} employeeId - ID сотрудника
 */
async function getStatisticsByEmployee(employeeId) {
    return apiRequest(`/api/statistics/by_employee?employee_id=${employeeId}`, 'GET');
}

