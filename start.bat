@echo off
echo Запуск банковской системы...
echo.

cd backend

echo Активация виртуального окружения...
call ..\venv\Scripts\activate.bat

echo Запуск сервера...
python main.py

pause

