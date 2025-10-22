@echo off
echo Running AI Onboarding Migration...

REM PostgreSQL connection settings
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=search_exchange_db
set PGUSER=admin
set PGPASSWORD=your_secure_password_123

echo Adding AI onboarding features to database...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f migration_add_ai_onboarding_features.sql
if %ERRORLEVEL% NEQ 0 (
    echo Error adding AI onboarding features
    exit /b 1
)

echo AI Onboarding Migration completed successfully!
echo - Added source column to advertiser_keywords
echo - Added source column to advertiser_categories
echo - Added approval_status column to advertisers
echo - Updated review_status in advertiser_reviews
pause

