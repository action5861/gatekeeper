-- search_queries 테이블에 ai_analysis_data 컬럼 추가 마이그레이션
-- 실행 날짜: 2025-01-20

-- 1. search_queries 테이블에 ai_analysis_data 컬럼 추가
ALTER TABLE search_queries 
  ADD COLUMN IF NOT EXISTS ai_analysis_data JSONB;

-- 2. 인덱스 추가 (선택사항 - JSONB 쿼리 성능 향상용)
CREATE INDEX IF NOT EXISTS idx_search_queries_ai_analysis ON search_queries USING GIN (ai_analysis_data);

COMMIT;

