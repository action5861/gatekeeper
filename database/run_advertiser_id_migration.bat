@echo off
echo Running advertiser_id migration for bids table...

psql -h localhost -U admin -d search_exchange_db -f migration_add_advertiser_id_to_bids.sql

if %ERRORLEVEL% EQU 0 (
    echo Migration completed successfully!
) else (
    echo Migration failed with error code %ERRORLEVEL%
)

pause
