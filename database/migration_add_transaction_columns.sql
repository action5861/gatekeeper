-- 🗄️ Database Migration: Add missing columns to transactions table
-- 📅 Created: 2025-01-20
-- 🎯 Purpose: Fix 500 error caused by missing search_id, bid_id, ad_type columns
-- ⚠️  Issue: user-service tries to INSERT into non-existent columns

-- 📝 Migration Description:
-- The user-service /api/user/earnings endpoint attempts to insert data into
-- search_id, bid_id, and ad_type columns that don't exist in the transactions table.
-- This migration adds these missing columns to resolve the 500 error.

-- 🔧 Add missing columns to transactions table
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS search_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS bid_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS ad_type VARCHAR(50);

-- 📊 Add indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_transactions_search_id ON transactions(search_id);
CREATE INDEX IF NOT EXISTS idx_transactions_ad_type ON transactions(ad_type);

-- ✅ Verify the migration
-- You can run this query to verify the columns were added:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'transactions' 
-- AND column_name IN ('search_id', 'bid_id', 'ad_type');

-- 📝 Migration completed successfully
-- The transactions table now supports the enhanced earnings tracking
-- with search_id, bid_id, and ad_type columns as required by user-service.




