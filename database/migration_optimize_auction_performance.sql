-- Auction Service 성능 최적화 마이그레이션
-- 작성일: 2024-01-XX
-- 목적: N+1 쿼리 문제 해결 및 광고 매칭 로직 성능 개선

-- 1. 광고주 키워드 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_keyword ON advertiser_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_advertiser_id ON advertiser_keywords(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_match_type ON advertiser_keywords(match_type);
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_priority ON advertiser_keywords(priority);

-- 2. 광고주 카테고리 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_advertiser_categories_path ON advertiser_categories(category_path);
CREATE INDEX IF NOT EXISTS idx_advertiser_categories_advertiser_id ON advertiser_categories(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_advertiser_categories_primary ON advertiser_categories(is_primary);

-- 3. 자동 입찰 설정 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_advertiser_id ON auto_bid_settings(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_enabled ON auto_bid_settings(is_enabled);
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_min_quality ON auto_bid_settings(min_quality_score);

-- 4. 광고주 심사 결과 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_advertiser_reviews_advertiser_id ON advertiser_reviews(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_advertiser_reviews_status ON advertiser_reviews(review_status);

-- 5. 비즈니스 카테고리 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_business_categories_active ON business_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_business_categories_path ON business_categories(path);
CREATE INDEX IF NOT EXISTS idx_business_categories_name ON business_categories(name);

-- 6. 입찰 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_bids_auction_id ON bids(auction_id);
CREATE INDEX IF NOT EXISTS idx_bids_advertiser_id ON bids(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_bids_type ON bids(type);
CREATE INDEX IF NOT EXISTS idx_bids_created_at ON bids(created_at);

-- 7. 경매 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_auctions_search_id ON auctions(search_id);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
CREATE INDEX IF NOT EXISTS idx_auctions_expires_at ON auctions(expires_at);

-- 8. 광고주 테이블 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_advertisers_company_name ON advertisers(company_name);
CREATE INDEX IF NOT EXISTS idx_advertisers_created_at ON advertisers(created_at);

-- 9. 복합 인덱스 생성 (자주 함께 조회되는 컬럼들)
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_composite ON advertiser_keywords(advertiser_id, match_type, priority);
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_composite ON auto_bid_settings(advertiser_id, is_enabled, min_quality_score);
CREATE INDEX IF NOT EXISTS idx_advertiser_categories_composite ON advertiser_categories(advertiser_id, is_primary, category_path);

-- 10. 풀텍스트 검색 인덱스 (한글 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_fulltext ON advertiser_keywords USING gin(to_tsvector('korean', keyword));

-- 11. 통계 정보 업데이트
ANALYZE advertiser_keywords;
ANALYZE advertiser_categories;
ANALYZE auto_bid_settings;
ANALYZE advertiser_reviews;
ANALYZE business_categories;
ANALYZE bids;
ANALYZE auctions;
ANALYZE advertisers;

-- 12. 쿼리 성능 모니터링을 위한 뷰 생성
CREATE OR REPLACE VIEW v_advertiser_matching_stats AS
SELECT 
    a.id as advertiser_id,
    a.company_name,
    COUNT(DISTINCT ak.id) as keyword_count,
    COUNT(DISTINCT ac.id) as category_count,
    abs.is_enabled as auto_bid_enabled,
    abs.daily_budget,
    abs.max_bid_per_keyword,
    ar.review_status
FROM advertisers a
LEFT JOIN advertiser_keywords ak ON a.id = ak.advertiser_id
LEFT JOIN advertiser_categories ac ON a.id = ac.advertiser_id
LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id
GROUP BY a.id, a.company_name, abs.is_enabled, abs.daily_budget, abs.max_bid_per_keyword, ar.review_status;

-- 13. 성능 모니터링을 위한 함수 생성
CREATE OR REPLACE FUNCTION get_matching_advertisers_performance(
    search_query TEXT,
    quality_score INTEGER
) RETURNS TABLE (
    advertiser_id INTEGER,
    company_name VARCHAR(100),
    match_score NUMERIC,
    match_reasons TEXT[]
) AS $$
BEGIN
    -- 이 함수는 최적화된 광고주 매칭 로직을 구현합니다
    -- 실제 구현은 application layer에서 처리됩니다
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- 14. 자동 입찰 로그 테이블 최적화 (이미 존재하는 경우)
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_advertiser_id ON auto_bid_logs(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_created_at ON auto_bid_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_query ON auto_bid_logs(search_query);

-- 15. 파티셔닝을 위한 테이블 준비 (대용량 데이터 처리)
-- 입찰 테이블을 날짜별로 파티셔닝
-- CREATE TABLE bids_2024_01 PARTITION OF bids
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 16. 캐시 테이블 생성 (자주 조회되는 데이터)
CREATE TABLE IF NOT EXISTS advertiser_matching_cache (
    id SERIAL PRIMARY KEY,
    search_query_hash VARCHAR(64) NOT NULL,
    advertiser_id INTEGER NOT NULL,
    match_score NUMERIC(5,2) NOT NULL,
    match_reasons TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(search_query_hash, advertiser_id)
);

CREATE INDEX IF NOT EXISTS idx_advertiser_matching_cache_hash ON advertiser_matching_cache(search_query_hash);
CREATE INDEX IF NOT EXISTS idx_advertiser_matching_cache_expires ON advertiser_matching_cache(expires_at);

-- 17. 성능 모니터링을 위한 메트릭 테이블
CREATE TABLE IF NOT EXISTS auction_performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(10,4) NOT NULL,
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data JSONB
);

CREATE INDEX IF NOT EXISTS idx_auction_performance_metrics_name ON auction_performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_auction_performance_metrics_time ON auction_performance_metrics(measurement_time);

-- 18. 쿼리 실행 계획 분석을 위한 설정
-- SET enable_seqscan = off;  -- 순차 스캔 비활성화 (개발 환경에서만)
-- SET random_page_cost = 1.1;  -- SSD 환경에 맞게 조정

COMMENT ON INDEX idx_advertiser_keywords_keyword IS '광고주 키워드 검색 최적화';
COMMENT ON INDEX idx_advertiser_categories_path IS '광고주 카테고리 경로 검색 최적화';
COMMENT ON INDEX idx_auto_bid_settings_composite IS '자동 입찰 설정 복합 검색 최적화';
COMMENT ON TABLE advertiser_matching_cache IS '광고주 매칭 결과 캐시 테이블';
COMMENT ON TABLE auction_performance_metrics IS '경매 성능 메트릭 수집 테이블';
