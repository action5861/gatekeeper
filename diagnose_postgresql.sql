-- PostgreSQL 성능 진단 쿼리
-- Full Scan 여부 및 인덱스 사용 현황 확인

\echo '========================================'
\echo '📊 인덱스 현황 확인'
\echo '========================================'

SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

\echo ''
\echo '========================================'
\echo '📈 테이블 통계 정보'
\echo '========================================'

SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''
\echo '========================================'
\echo '🔎 인덱스 사용 통계'
\echo '========================================'

SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    CASE WHEN idx_scan = 0 THEN '⚠️  미사용' ELSE '✅ 사용 중' END as status
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC, tablename, indexname;

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - EXACT 매칭'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'exact'
  AND lower(replace(keyword, ' ', '')) = ANY(ARRAY['아이폰16프로', '아이폰', '프로']::text[]);

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - PHRASE 매칭'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'phrase'
  AND (
        lower(replace(keyword, ' ', '')) = ANY(ARRAY['아이폰16프로', '아이폰', '프로']::text[])
     OR EXISTS (
          SELECT 1 FROM unnest(ARRAY['아이폰16프로', '아이폰', '프로']::text[]) t(tok)
          WHERE lower(replace(keyword, ' ', '')) LIKE '%' || tok || '%'
             OR tok LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
     )
  );

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - BROAD 매칭 (LIKE 패턴)'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'broad'
  AND (
    '아이폰16프로' LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
    OR lower(replace(keyword, ' ', '')) LIKE '%' || '아이폰16프로' || '%'
  );

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - CATEGORY 매칭'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
WITH matched_categories AS (
    SELECT DISTINCT path
    FROM business_categories
    WHERE is_active = true
      AND lower(name) LIKE ANY(ARRAY['%아이폰%', '%프로%']::text[])
)
SELECT ac.advertiser_id, ac.category_path, ac.is_primary
FROM advertiser_categories ac
JOIN matched_categories mc ON ac.category_path LIKE mc.path || '%';

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - 광고주 상세 조회'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT 
    a.id as advertiser_id, a.company_name, a.website_url,
    abs.daily_budget, abs.max_bid_per_keyword,
    ar.recommended_bid_min, ar.recommended_bid_max
FROM advertisers a
LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id AND ar.review_status = 'approved'
WHERE abs.is_enabled = true AND a.id = ANY(ARRAY[1, 2, 3]::int[])
LIMIT 10;

\echo ''
\echo '========================================'
\echo '🔬 주요 쿼리 성능 진단 - 경매 조회'
\echo '========================================'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT * FROM auctions WHERE search_id = 'search_001';

\echo ''
\echo '========================================'
\echo '📊 Full Scan 발생 테이블 확인'
\echo '========================================'

SELECT 
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    seq_tup_read as seq_tuples_read,
    idx_scan as index_scans,
    idx_tup_fetch as idx_tuples_fetched,
    CASE 
        WHEN seq_scan > idx_scan * 10 AND seq_scan > 100 THEN '⚠️  Full Scan 주의'
        WHEN seq_scan > 0 THEN '⚠️  Full Scan 발생'
        ELSE '✅ Index Scan 사용'
    END as scan_status
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC;

\echo ''
\echo '========================================'
\echo '진단 완료'
\echo '========================================'

