-- Migration: delivery_metrics 테이블에 clicked 컬럼 추가
-- SLA 검증 개선: 광고 클릭 여부를 추적하기 위한 컬럼

-- clicked 컬럼 추가 (기본값 false)
ALTER TABLE delivery_metrics
ADD COLUMN IF NOT EXISTS clicked BOOLEAN DEFAULT FALSE;

-- 인덱스 추가 (clicked 기준 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_delivery_metrics_clicked 
ON delivery_metrics(clicked);

-- 확인
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'delivery_metrics'
ORDER BY ordinal_position;

