@echo off
echo Running clicked column migration...
psql -h localhost -p 5433 -U admin -d search_exchange_db -f migration_add_clicked_to_delivery_metrics.sql
echo Migration completed!
pause

