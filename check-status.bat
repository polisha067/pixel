@echo off
echo Checking Docker containers status...
echo.

docker ps -a

echo.
echo Checking if port 8001 is in use...
netstat -ano | findstr :8001

echo.
echo To see logs, run:
echo docker-compose logs backend
echo.
pause
