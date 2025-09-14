-- 🔒 Transactions 테이블 유니크 제약조건 추가
-- 멱등성을 보장하기 위한 제약조건

-- 1. (user_id, search_id, bid_id) 조합의 일일 유니크 제약조건
-- PostgreSQL에서는 created_at::date를 직접 유니크에 사용할 수 없으므로
-- 별도의 date 컬럼을 추가하고 트리거로 관리

-- 날짜 컬럼 추가 (YYYYMMDD 형식)
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS transaction_date VARCHAR(8);

-- 기존 데이터에 대해 날짜 컬럼 업데이트
UPDATE transactions 
SET transaction_date = TO_CHAR(created_at, 'YYYYMMDD')
WHERE transaction_date IS NULL;

-- 유니크 제약조건 추가
ALTER TABLE transactions 
ADD CONSTRAINT IF NOT EXISTS uniq_user_search_bid_day
UNIQUE (user_id, search_id, bid_id, transaction_date);

-- 새로 삽입되는 레코드에 대해 자동으로 날짜 설정하는 트리거 함수
CREATE OR REPLACE FUNCTION set_transaction_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.transaction_date = TO_CHAR(NEW.created_at, 'YYYYMMDD');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS trigger_set_transaction_date ON transactions;
CREATE TRIGGER trigger_set_transaction_date
    BEFORE INSERT ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION set_transaction_date();

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_transactions_user_search_bid_date 
ON transactions(user_id, search_id, bid_id, transaction_date);

-- 기존 인덱스도 유지
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);

COMMIT;
