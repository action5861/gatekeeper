-- 하이마트 광고주 카테고리 확인

-- 1. 하이마트 광고주 ID 찾기
SELECT 
    id,
    username,
    email,
    company_name,
    category,
    approval_status
FROM advertisers
WHERE company_name ILIKE '%하이마트%' 
   OR company_name ILIKE '%HI-MART%'
   OR company_name ILIKE '%himart%'
ORDER BY id;

-- 2. 하이마트 광고주의 카테고리 조회 (위에서 찾은 advertiser_id를 사용)
-- 예: advertiser_id = 1인 경우
SELECT 
    ac.id,
    ac.advertiser_id,
    ac.category_path,
    ac.category_level,
    ac.is_primary,
    ac.source,
    ac.created_at,
    bc.name as category_name
FROM advertiser_categories ac
LEFT JOIN business_categories bc ON ac.category_path = bc.path
WHERE ac.advertiser_id = (
    SELECT id 
    FROM advertisers 
    WHERE company_name ILIKE '%하이마트%' 
       OR company_name ILIKE '%HI-MART%'
       OR company_name ILIKE '%himart%'
    LIMIT 1
)
ORDER BY ac.is_primary DESC, ac.category_level ASC, ac.category_path ASC;

-- 3. 하이마트 광고주의 advertisers.category 컬럼 확인
SELECT 
    id,
    company_name,
    category,
    website_url
FROM advertisers
WHERE company_name ILIKE '%하이마트%' 
   OR company_name ILIKE '%HI-MART%'
   OR company_name ILIKE '%himart%';







