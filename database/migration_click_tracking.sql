-- 클릭 트래킹 및 적립 시스템 마이그레이션
-- 실행 날짜: 2025-01-20

-- 1. bids 테이블에 필요한 컬럼 추가
ALTER TABLE bids 
  ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'ADVERTISER' CHECK (type IN ('ADVERTISER', 'PLATFORM')),
  ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id),
  ADD COLUMN IF NOT EXISTS dest_url TEXT;

-- 2. transactions 테이블에 필요한 컬럼 추가
ALTER TABLE transactions 
  ADD COLUMN IF NOT EXISTS bid_id VARCHAR(100),
  ADD COLUMN IF NOT EXISTS advertiser_id INTEGER REFERENCES advertisers(id),
  ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'ADVERTISER' CHECK (source IN ('ADVERTISER', 'PLATFORM')),
  ADD COLUMN IF NOT EXISTS reason VARCHAR(100);

-- 3. advertiser_id를 NULL 허용하도록 수정 (PLATFORM 거래용)
ALTER TABLE transactions 
  ALTER COLUMN advertiser_id DROP NOT NULL;

-- 4. 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_bid ON transactions(bid_id);
CREATE INDEX IF NOT EXISTS idx_bids_user ON bids(user_id);

-- 5. 기존 데이터 업데이트 (필요시)
-- 기존 bids의 type을 'ADVERTISER'로 설정
UPDATE bids SET type = 'ADVERTISER' WHERE type IS NULL;

-- 기존 transactions의 source를 'ADVERTISER'로 설정
UPDATE transactions SET source = 'ADVERTISER' WHERE source IS NULL;

-- 기존 transactions의 amount를 primary_reward로 설정
UPDATE transactions SET amount = primary_reward WHERE amount IS NULL;

COMMIT;
