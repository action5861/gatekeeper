# PowerShell 테스트 스크립트
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Running buyer name fix tests..." -ForegroundColor Green

Set-Location "C:\Users\MS\gatekeeper - 복사본"

Write-Host "`n1. Testing database connection..." -ForegroundColor Yellow
python test_buyer_name_fix.py

Write-Host "`n2. Testing API dashboard..." -ForegroundColor Yellow
python test_api_dashboard.py

Write-Host "`nTests completed!" -ForegroundColor Green
Read-Host "Press Enter to continue"
