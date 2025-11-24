#!/bin/bash

echo "Running Reasons Column Migration..."

# PostgreSQL connection settings
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=search_exchange_db
export PGUSER=admin
export PGPASSWORD=your_secure_password_123

echo "Adding reasons JSONB column to auto_bid_logs table..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f migration_add_reasons_to_auto_bid_logs.sql
if [ $? -ne 0 ]; then
    echo "Error adding reasons column"
    exit 1
fi

echo "Reasons Column Migration completed successfully!"
echo "- Added reasons JSONB column to auto_bid_logs"
echo "- Created GIN index on reasons column for better query performance"














