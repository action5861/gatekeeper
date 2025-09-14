-- 최소 입찰가 컬럼 추가 마이그레이션
-- 실행일: 2024-01-XX

-- auto_bid_settings 테이블에 min_bid_per_keyword 컬럼 추가
ALTER TABLE auto_bid_settings 
ADD COLUMN IF NOT EXISTS min_bid_per_keyword INTEGER DEFAULT 100;

-- 기존 데이터에 대한 기본값 설정
UPDATE auto_bid_settings 
SET min_bid_per_keyword = 100 
WHERE min_bid_per_keyword IS NULL;

-- 컬럼을 NOT NULL로 변경
ALTER TABLE auto_bid_settings 
ALTER COLUMN min_bid_per_keyword SET NOT NULL;

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_min_bid ON auto_bid_settings(min_bid_per_keyword);
