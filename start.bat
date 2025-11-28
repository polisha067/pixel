@echo off
echo Starting AI Mail Assistant...
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy env.example to .env and fill in your Yandex Cloud credentials.
    pause
    exit /b 1
)

REM Start backend server
echo Starting backend server...
echo Frontend is now integrated into FastAPI!
echo.
echo Server will be available at: http://localhost:8001
echo.
cd backend
python main.py

pause
