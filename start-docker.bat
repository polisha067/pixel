@echo off
echo Starting AI Mail Assistant with Docker...
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy env.example to .env and fill in your Yandex Cloud credentials.
    echo Expected format:
    echo api_key=your_api_key_here
    echo folder_id=your_folder_id_here
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Stopping existing containers...
docker compose down

echo Building and starting containers...
docker compose up --build

pause
