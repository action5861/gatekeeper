@echo off
echo 🚀 Gatekeeper 개발 서버 시작 중...
echo.

echo 📦 Docker Compose 서비스 시작...
docker-compose up -d

echo.
echo ⏳ 서비스 시작 대기 중...
timeout /t 10 /nobreak > nul

echo.
echo 🔍 서비스 상태 확인...
docker-compose ps

echo.
echo ✅ 모든 서비스가 시작되었습니다!
echo 🌐 프론트엔드: http://localhost:3000
echo 📊 pgAdmin: http://localhost:5050
echo.
echo 🎯 개발 모드로 실행 중입니다.
echo 📝 코드를 수정하면 자동으로 반영됩니다.
echo.
pause 