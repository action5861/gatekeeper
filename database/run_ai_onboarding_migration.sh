#!/bin/bash

echo "Running AI Onboarding Migration..."

# PostgreSQL connection settings
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=search_exchange_db
export PGUSER=admin
export PGPASSWORD=your_secure_password_123

echo "Adding AI onboarding features to database..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f migration_add_ai_onboarding_features.sql
if [ $? -ne 0 ]; then
    echo "Error adding AI onboarding features"
    exit 1
fi

echo "AI Onboarding Migration completed successfully!"
echo "- Added source column to advertiser_keywords"
echo "- Added source column to advertiser_categories"
echo "- Added approval_status column to advertisers"
echo "- Updated review_status in advertiser_reviews"

