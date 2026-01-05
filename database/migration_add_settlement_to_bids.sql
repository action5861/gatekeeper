-- ============================================
-- bids 테이블에 정산 결과 컬럼 추가
-- Single Source of Truth (SSOT) 통일을 위함
-- ============================================

ALTER TABLE bids ADD COLUMN IF NOT EXISTS settlement_decision TEXT;
ALTER TABLE bids ADD COLUMN IF NOT EXISTS settled_amount NUMERIC;
ALTER TABLE bids ADD COLUMN IF NOT EXISTS settled_at TIMESTAMPTZ;

-- 인덱스 추가 (광고주 대시보드 쿼리 성능 향상)
CREATE INDEX IF NOT EXISTS idx_bids_settled_at ON bids(settled_at) WHERE settled_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bids_advertiser_settled ON bids(advertiser_id, settled_at) WHERE settled_amount IS NOT NULL;

-- 기존 settlements 데이터를 bids에 역방향 마이그레이션 (선택적)
-- 이미 정산된 bids에 대한 settled_amount 업데이트
UPDATE bids b
SET 
    settlement_decision = s.verification_decision,
    settled_amount = s.payable_amount,
    settled_at = s.created_at
FROM (
    SELECT DISTINCT ON (trade_id)
        trade_id,
        verification_decision,
        payable_amount,
        created_at
    FROM settlements
    ORDER BY trade_id, created_at DESC
) s
WHERE b.id = s.trade_id
  AND b.settled_amount IS NULL;

