-- business_categories 중복 데이터 정리 및 UNIQUE 제약 추가

-- 1. 먼저 중복 데이터 확인
-- SELECT name, level, COUNT(*) as count 
-- FROM business_categories 
-- WHERE level = 1 
-- GROUP BY name, level 
-- HAVING COUNT(*) > 1;

-- 2. 중복 데이터 삭제 (각 카테고리별로 가장 오래된 것 하나만 남기기)
DELETE FROM business_categories bc1
WHERE bc1.id NOT IN (
    SELECT MIN(bc2.id)
    FROM business_categories bc2
    WHERE bc2.level = 1
    GROUP BY bc2.name, bc2.level
)
AND bc1.level = 1;

-- 3. UNIQUE 제약 추가 (name + level 조합이 유일해야 함)
ALTER TABLE business_categories
ADD CONSTRAINT business_categories_name_level_unique UNIQUE (name, level);

-- 4. 확인
SELECT name, level, COUNT(*) as count 
FROM business_categories 
WHERE level = 1 
GROUP BY name, level 
ORDER BY name;

