@echo off
echo Running SLA Migration...

REM PostgreSQL connection settings
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=search_exchange_db
set PGUSER=admin
set PGPASSWORD=your_secure_password_123

echo Creating SLA tables...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f migration_add_sla_tables.sql
if %ERRORLEVEL% NEQ 0 (
    echo Error creating SLA tables
    exit /b 1
)

echo Altering transactions status column...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f migration_alter_transactions_status.sql
if %ERRORLEVEL% NEQ 0 (
    echo Error altering transactions table
    exit /b 1
)

echo SLA Migration completed successfully!
pause

