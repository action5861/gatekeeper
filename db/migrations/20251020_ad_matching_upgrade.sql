 -- PostgreSQL의 LIKE 검색 성능을 가속하기 위해 pg_trgm 확장을 활성화합니다.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. 키워드 매칭 성능 최적화를 위한 인덱스 추가
CREATE INDEX IF NOT EXISTS gin_adv_kw_trgm ON advertiser_keywords USING gin (lower(keyword) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_adv_kw_lower_normalized ON advertiser_keywords (lower(replace(keyword, ' ', '')));
CREATE INDEX IF NOT EXISTS idx_adv_kw_match_type ON advertiser_keywords (match_type);

-- 2. 카테고리 매칭 성능 최적화를 위한 인덱스 추가
CREATE INDEX IF NOT EXISTS gin_bc_name_trgm ON business_categories USING gin (lower(name) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_bc_path_pattern ON business_categories (path text_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_ac_path_pattern ON advertiser_categories (category_path text_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_ac_adv_id ON advertiser_categories (advertiser_id);

-- 3. 자동 입찰 설정 및 예산 확인 쿼리 최적화
CREATE INDEX IF NOT EXISTS idx_abs_adv_enabled ON auto_bid_settings (advertiser_id) WHERE is_enabled = true;

-- 4. bids 테이블에 advertiser_id 컬럼 추가 (예산 집계용)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='bids' AND column_name='advertiser_id'
    ) THEN
        ALTER TABLE bids ADD COLUMN advertiser_id INTEGER;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_bids_adv_created ON bids (advertiser_id, created_at DESC);

-- 5. auto_bid_logs 테이블에 reasons 컬럼 추가 (매칭 근거 저장용)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='auto_bid_logs' AND column_name='reasons'
    ) THEN
        ALTER TABLE auto_bid_logs ADD COLUMN reasons JSONB;
    END IF;
END $$;
