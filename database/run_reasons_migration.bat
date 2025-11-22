@echo off
echo Running Reasons Column Migration...

REM PostgreSQL connection settings
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=search_exchange_db
set PGUSER=admin
set PGPASSWORD=your_secure_password_123

echo Adding reasons JSONB column to auto_bid_logs table...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f migration_add_reasons_to_auto_bid_logs.sql
if %ERRORLEVEL% NEQ 0 (
    echo Error adding reasons column
    exit /b 1
)

echo Reasons Column Migration completed successfully!
echo - Added reasons JSONB column to auto_bid_logs
echo - Created GIN index on reasons column for better query performance
pause














