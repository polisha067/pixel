@echo off
echo Testing API connection...
echo.

echo Testing GET request to root...
curl http://localhost:8001/

echo.
echo.
echo Testing POST request to mail_generator...
curl -X POST http://localhost:8001/mail_generator ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"Test email\"}"

echo.
echo.
pause
