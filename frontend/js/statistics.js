/**
 * Логика страницы статистики
 * 
 * Загружает и отображает статистику обработки писем
 */

/**
 * Инициализация страницы статистики
 */
function initStatisticsPage() {
    loadOverviewStatistics();
    loadCategoryStatistics();
}

/**
 * Загрузить общую статистику
 */
async function loadOverviewStatistics() {
    const container = document.getElementById('overviewStats');
    if (!container) return;
    
    try {
        const stats = await getOverviewStatistics();
        
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Всего обращений</div>
                <div class="stat-value">${stats.total_letters}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Ожидание</div>
                <div class="stat-value">${stats.by_status.waiting || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">В работе</div>
                <div class="stat-value">${stats.by_status.in_progress || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Отправлено</div>
                <div class="stat-value">${stats.by_status.sent || 0}</div>
            </div>
        `;
    
    } catch (error) {
        container.innerHTML = `<div class="error">Ошибка при загрузке статистики: ${error.message}</div>`;
    }
}

/**
 * Загрузить статистику по категориям
 */
async function loadCategoryStatistics() {
    const container = document.getElementById('categoryStats');
    if (!container) return;
    
    try {
        const stats = await getStatisticsByCategory();
        
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
        
        let html = '<div class="stats-grid">';
        
        for (const [category, data] of Object.entries(stats)) {
            if (data.total > 0) {
                html += `
                    <div class="stat-card">
                        <div class="stat-label">${categoryNames[category] || category}</div>
                        <div class="stat-value">${data.total}</div>
                        <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                            <div>Ожидание: ${data.by_status.waiting || 0}</div>
                            <div>В работе: ${data.by_status.in_progress || 0}</div>
                            <div>Отправлено: ${data.by_status.sent || 0}</div>
                        </div>
                    </div>
                `;
            }
        }
        
        html += '</div>';
        
        if (Object.values(stats).every(d => d.total === 0)) {
            html = '<p style="text-align: center; color: #666;">Нет данных для отображения</p>';
        }
        
        container.innerHTML = html;
    
    } catch (error) {
        container.innerHTML = `<div class="error">Ошибка при загрузке статистики: ${error.message}</div>`;
    }
}

// Инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStatisticsPage);
} else {
    initStatisticsPage();
}

