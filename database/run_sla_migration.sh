#!/bin/bash

echo "Running SLA Migration..."

# PostgreSQL connection settings
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=search_exchange_db
export PGUSER=admin
export PGPASSWORD=your_secure_password_123

echo "Creating SLA tables..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f migration_add_sla_tables.sql
if [ $? -ne 0 ]; then
    echo "Error creating SLA tables"
    exit 1
fi

echo "Altering transactions status column..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f migration_alter_transactions_status.sql
if [ $? -ne 0 ]; then
    echo "Error altering transactions table"
    exit 1
fi

echo "SLA Migration completed successfully!"

