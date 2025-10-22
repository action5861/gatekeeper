#!/bin/bash
echo "Running clicked column migration..."
PGPASSWORD=your_secure_password_123 psql -h localhost -p 5433 -U admin -d search_exchange_db -f migration_add_clicked_to_delivery_metrics.sql
echo "Migration completed!"

