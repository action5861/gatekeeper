-- transactions 테이블의 status 컬럼 타입을 변경하고 기본값을 설정합니다.
ALTER TABLE transactions
ALTER COLUMN status TYPE VARCHAR(50),
ALTER COLUMN status SET DEFAULT 'PENDING_VERIFICATION';

-- 기존 데이터 마이그레이션 (필요시)
-- UPDATE transactions SET status = 'SETTLED' WHERE status = '1차 완료';

