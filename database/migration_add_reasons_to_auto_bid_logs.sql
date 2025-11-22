-- auto_bid_logs 테이블에 reasons JSONB 컬럼 추가 마이그레이션
-- 이 마이그레이션은 자동 입찰 로그에 매칭 사유를 저장하기 위한 컬럼을 추가합니다.

-- 1. reasons 컬럼이 없으면 추가 (JSONB 타입)
ALTER TABLE auto_bid_logs
  ADD COLUMN IF NOT EXISTS reasons jsonb;

-- 2. 기존 컬럼이 다른 타입(text, json 등)이면 JSONB로 변환
DO $$
BEGIN
  -- 컬럼이 이미 존재하지만 타입이 다른 경우
  IF EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'auto_bid_logs' 
    AND column_name = 'reasons'
    AND data_type != 'jsonb'
  ) THEN
    ALTER TABLE auto_bid_logs
      ALTER COLUMN reasons TYPE jsonb USING
        CASE
          WHEN reasons IS NULL THEN '[]'::jsonb
          WHEN pg_typeof(reasons)::text IN ('json', 'jsonb') THEN reasons::jsonb
          ELSE to_jsonb(reasons)
        END;
  END IF;
END $$;

-- 3. 기본값 설정 (빈 배열)
ALTER TABLE auto_bid_logs
  ALTER COLUMN reasons SET DEFAULT '[]'::jsonb;

-- 4. NULL 값이 있으면 빈 배열로 업데이트
UPDATE auto_bid_logs 
SET reasons = '[]'::jsonb 
WHERE reasons IS NULL;

-- 5. 인덱스 추가 (선택사항 - JSONB 쿼리 성능 향상)
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_reasons_gin 
  ON auto_bid_logs USING gin(reasons);














