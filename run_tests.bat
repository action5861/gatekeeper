@echo off
chcp 65001 > nul
echo Running buyer name fix tests...

cd /d "C:\Users\MS\gatekeeper - 복사본"

echo.
echo 1. Testing database connection...
python test_buyer_name_fix.py

echo.
echo 2. Testing API dashboard...
python test_api_dashboard.py

echo.
echo Tests completed!
pause
