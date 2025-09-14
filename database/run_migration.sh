#!/bin/bash

# 🗄️ Database Migration Runner
# 📅 Created: 2025-01-20
# 🎯 Purpose: Execute the transaction table migration

echo "🚀 Starting database migration..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if postgres-db container is running
if ! docker ps | grep -q "postgres-db"; then
    echo "❌ postgres-db container is not running. Please start the services first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "📊 Executing migration: Add missing columns to transactions table..."

# Execute the migration
docker exec -i postgres-db psql -U postgres -d postgres < migration_add_transaction_columns.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo ""
    echo "🔍 Verifying the migration..."
    
    # Verify the columns were added
    docker exec -i postgres-db psql -U postgres -d postgres -c "
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'transactions' 
    AND column_name IN ('search_id', 'bid_id', 'ad_type')
    ORDER BY column_name;"
    
    echo ""
    echo "🎉 Migration verification complete!"
    echo "The 500 error should now be resolved."
else
    echo "❌ Migration failed. Please check the error messages above."
    exit 1
fi




