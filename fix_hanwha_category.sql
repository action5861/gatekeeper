-- 한화생명 광고주 카테고리 수정
UPDATE advertisers 
SET category = '서비스' 
WHERE id = 39;

-- 확인
SELECT id, company_name, category, approval_status 
FROM advertisers 
WHERE id = 39;

