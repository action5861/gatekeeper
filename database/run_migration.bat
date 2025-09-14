@echo off
REM 🗄️ Database Migration Runner (Windows)
REM 📅 Created: 2025-01-20
REM 🎯 Purpose: Execute the transaction table migration

echo 🚀 Starting database migration...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if postgres-db container is running
docker ps | findstr "postgres-db" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ postgres-db container is not running. Please start the services first:
    echo    docker-compose up -d
    pause
    exit /b 1
)

echo 📊 Executing migration: Add missing columns to transactions table...

REM Execute the migration
docker exec -i postgres-db psql -U postgres -d postgres < migration_add_transaction_columns.sql

if %errorlevel% equ 0 (
    echo ✅ Migration completed successfully!
    echo.
    echo 🔍 Verifying the migration...
    
    REM Verify the columns were added
    docker exec -i postgres-db psql -U postgres -d postgres -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'transactions' AND column_name IN ('search_id', 'bid_id', 'ad_type') ORDER BY column_name;"
    
    echo.
    echo 🎉 Migration verification complete!
    echo The 500 error should now be resolved.
) else (
    echo ❌ Migration failed. Please check the error messages above.
    pause
    exit /b 1
)

pause




