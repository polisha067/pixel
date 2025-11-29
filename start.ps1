Write-Host "Запуск банковской системы..." -ForegroundColor Green
Write-Host ""

# Активация виртуального окружения
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Виртуальное окружение не найдено. Установка зависимостей..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    pip install tzdata
}

Write-Host ""
Write-Host "Запуск сервера на http://127.0.0.1:8002" -ForegroundColor Cyan
Write-Host ""

cd backend
python main.py

