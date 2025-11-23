-- 일일 제출 한도 조회 성능 최적화를 위한 인덱스 추가
-- _used_today_from_tx 함수에서 사용하는 쿼리 최적화

-- user_id와 created_at 기준으로 일일 트랜잭션 조회 최적화
-- 기존 인덱스가 있더라도 날짜 기준 필터링에 최적화된 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_transactions_user_date_daily_limit
ON transactions (user_id, created_at);

-- 정산 완료된 트랜잭션 조회 최적화 (추후 보너스 한도 정책에 활용)
CREATE INDEX IF NOT EXISTS idx_transactions_user_date_status
ON transactions (user_id, created_at, status)
WHERE status = 'SETTLED';

-- 멱등성 체크를 위한 인덱스 (user_id, search_id, bid_id, created_at)
CREATE INDEX IF NOT EXISTS idx_transactions_idempotency
ON transactions (user_id, search_id, bid_id, created_at);

