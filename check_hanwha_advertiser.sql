-- 한화생명 광고주 카테고리 및 매칭 설정 확인 쿼리

-- 1. 광고주 기본 정보 확인
SELECT 
    id,
    company_name,
    website_url,
    category,  -- 표준 14개 카테고리 중 하나 (서비스, 의료/건강 등)
    approval_status,
    created_at
FROM advertisers
WHERE company_name LIKE '%한화생명%' OR company_name LIKE '%한화%';

-- 2. 광고주 카테고리 설정 확인 (advertiser_categories 테이블)
SELECT 
    ac.id,
    ac.advertiser_id,
    a.company_name,
    ac.category_path,
    ac.category_level,
    ac.is_primary,
    ac.source
FROM advertiser_categories ac
JOIN advertisers a ON ac.advertiser_id = a.id
WHERE a.company_name LIKE '%한화생명%' OR a.company_name LIKE '%한화%';

-- 3. 광고주 키워드 설정 확인
SELECT 
    ak.id,
    ak.advertiser_id,
    a.company_name,
    ak.keyword,
    ak.match_type,
    ak.priority,
    ak.source
FROM advertiser_keywords ak
JOIN advertisers a ON ak.advertiser_id = a.id
WHERE a.company_name LIKE '%한화생명%' OR a.company_name LIKE '%한화%'
ORDER BY ak.priority DESC, ak.match_type;

-- 4. 자동 입찰 설정 확인 (매칭에 필수)
SELECT 
    abs.id,
    abs.advertiser_id,
    a.company_name,
    abs.is_enabled,  -- 이게 true여야 매칭됨!
    abs.daily_budget,
    abs.max_bid_per_keyword,
    abs.min_quality_score,
    abs.preferred_categories
FROM auto_bid_settings abs
JOIN advertisers a ON abs.advertiser_id = a.id
WHERE a.company_name LIKE '%한화생명%' OR a.company_name LIKE '%한화%';

-- 5. 광고주 심사 상태 확인
SELECT 
    ar.id,
    ar.advertiser_id,
    a.company_name,
    ar.review_status,  -- 'approved'여야 매칭 가능
    ar.recommended_bid_min,
    ar.recommended_bid_max
FROM advertiser_reviews ar
JOIN advertisers a ON ar.advertiser_id = a.id
WHERE a.company_name LIKE '%한화생명%' OR a.company_name LIKE '%한화%';

-- 6. 종합 진단 쿼리 (한화생명 광고주 전체 상태)
SELECT 
    a.id AS advertiser_id,
    a.company_name,
    a.category AS standard_category,
    a.approval_status,
    COUNT(DISTINCT ak.id) AS keyword_count,
    COUNT(DISTINCT ac.id) AS category_count,
    abs.is_enabled AS auto_bid_enabled,
    ar.review_status,
    CASE 
        WHEN abs.is_enabled = false THEN '❌ 자동 입찰 비활성화'
        WHEN ar.review_status != 'approved' THEN '❌ 심사 미승인'
        WHEN COUNT(DISTINCT ak.id) = 0 THEN '❌ 키워드 없음'
        WHEN COUNT(DISTINCT ac.id) = 0 AND a.category IS NULL THEN '⚠️ 카테고리 미설정'
        ELSE '✅ 정상'
    END AS status_diagnosis
FROM advertisers a
LEFT JOIN advertiser_keywords ak ON a.id = ak.advertiser_id
LEFT JOIN advertiser_categories ac ON a.id = ac.advertiser_id
LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id
WHERE a.company_name LIKE '%한화생명%' OR a.company_name LIKE '%한화%'
GROUP BY a.id, a.company_name, a.category, a.approval_status, abs.is_enabled, ar.review_status;

