-- 한화생명 광고주의 표준 카테고리를 '서비스'로 설정
UPDATE advertisers 
SET category = '서비스' 
WHERE id = 39;

-- 확인
SELECT id, company_name, category 
FROM advertisers 
WHERE id = 39;

-- DB손해보험과 비교
SELECT id, company_name, category 
FROM advertisers 
WHERE id IN (15, 39) 
ORDER BY id;

