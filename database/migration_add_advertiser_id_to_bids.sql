-- 입찰 테이블에 광고주 ID 컬럼 추가 마이그레이션
-- 실행 날짜: 2025-01-20

-- 1. bids 테이블에 advertiser_id 컬럼 추가
ALTER TABLE bids 
  ADD COLUMN IF NOT EXISTS advertiser_id INTEGER REFERENCES advertisers(id);

-- 2. 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_bids_advertiser ON bids(advertiser_id);

-- 3. 기존 데이터 업데이트 (buyer_name을 기반으로 광고주 ID 매칭)
UPDATE bids 
SET advertiser_id = (
    SELECT a.id 
    FROM advertisers a 
    WHERE a.company_name = bids.buyer_name 
    LIMIT 1
)
WHERE advertiser_id IS NULL 
AND buyer_name IS NOT NULL 
AND buyer_name != '시스템';

COMMIT;
