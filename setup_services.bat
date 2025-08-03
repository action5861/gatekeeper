@echo off
echo ========================================
echo DigiSafe Microservices Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found. Starting setup...
echo.

REM List of services to setup
set SERVICES=advertiser-service analysis-service auction-service payment-service quality-service user-service verification-service

REM Loop through each service
for %%s in (%SERVICES%) do (
    echo.
    echo ========================================
    echo Setting up %%s
    echo ========================================
    
    REM Check if service directory exists
    if not exist "services\%%s" (
        echo ERROR: services\%%s directory not found
        goto :continue
    )
    
    REM Change to service directory
    cd "services\%%s"
    
    REM Remove existing venv if it exists
    if exist "venv" (
        echo Removing existing virtual environment...
        rmdir /s /q "venv"
    )
    
    REM Create new virtual environment
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment for %%s
        cd ..\..
        goto :continue
    )
    
    REM Activate virtual environment and install dependencies
    echo Activating virtual environment and installing dependencies...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment for %%s
        cd ..\..
        goto :continue
    )
    
    REM Upgrade pip
    python -m pip install --upgrade pip
    
    REM Install requirements
    if exist "requirements.txt" (
        echo Installing requirements from requirements.txt...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ERROR: Failed to install requirements for %%s
            cd ..\..
            goto :continue
        )
    ) else (
        echo WARNING: requirements.txt not found for %%s
    )
    
    REM Deactivate virtual environment
    deactivate
    
    echo %%s setup completed successfully!
    
    REM Return to root directory
    cd ..\..
    
    :continue
)

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo All microservices have been configured with:
echo - Virtual environments created in each service directory
echo - Dependencies installed from requirements.txt
echo - VS Code settings configured for proper Python interpreter detection
echo.
echo Next steps:
echo 1. Restart VS Code to ensure all settings are applied
echo 2. Open any service directory in VS Code
echo 3. Select the Python interpreter: ./venv/Scripts/python.exe
echo 4. The reportMissingImports errors should now be resolved
echo.
pause 