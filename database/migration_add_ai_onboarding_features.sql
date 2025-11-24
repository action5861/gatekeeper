-- migration_add_ai_onboarding_features.sql
-- AI 기반 광고주 온보딩 어시스턴트 기능 추가를 위한 데이터베이스 마이그레이션

-- 1. advertiser_keywords 테이블에 source 컬럼 추가
-- AI 제안('ai_suggested'), 사용자 입력('user_added'), 사용자 확정('user_confirmed')을 구분
ALTER TABLE advertiser_keywords
ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'user_added' NOT NULL
CHECK (source IN ('user_added', 'ai_suggested', 'user_confirmed'));

-- 기존 데이터에 대한 source 값 설정 (이미 존재하는 경우)
UPDATE advertiser_keywords 
SET source = 'user_added' 
WHERE source IS NULL;

-- 2. advertiser_categories 테이블에 source 컬럼 추가
-- AI 제안('ai_suggested'), 사용자 입력('user_added'), 사용자 확정('user_confirmed')을 구분
ALTER TABLE advertiser_categories
ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'user_added' NOT NULL
CHECK (source IN ('user_added', 'ai_suggested', 'user_confirmed'));

-- 기존 데이터에 대한 source 값 설정
UPDATE advertiser_categories 
SET source = 'user_added' 
WHERE source IS NULL;

-- 3. advertisers 테이블에 approval_status 컬럼 추가
-- 광고주 승인 상태 관리: pending_analysis(AI 분석 대기), pending(심사 대기), approved(승인), rejected(거절)
ALTER TABLE advertisers
ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'pending' 
CHECK (approval_status IN ('pending_analysis', 'pending', 'approved', 'rejected'));

-- 기존 데이터에 대한 approval_status 값 설정
UPDATE advertisers 
SET approval_status = 'pending' 
WHERE approval_status IS NULL;

-- 4. advertiser_reviews 테이블의 review_status에 'pending_analysis' 추가
-- 기존 CHECK constraint를 제거하고 새로운 constraint 추가
ALTER TABLE advertiser_reviews
DROP CONSTRAINT IF EXISTS advertiser_reviews_review_status_check;

ALTER TABLE advertiser_reviews
ADD CONSTRAINT advertiser_reviews_review_status_check
CHECK (review_status IN ('pending_analysis', 'pending', 'in_progress', 'approved', 'rejected'));

-- 5. 인덱스 추가 (성능 최적화)
-- source 컬럼에 대한 인덱스 추가 (AI 제안 항목 필터링 시 성능 향상)
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_source 
ON advertiser_keywords(source);

CREATE INDEX IF NOT EXISTS idx_advertiser_categories_source 
ON advertiser_categories(source);

-- approval_status에 대한 인덱스 추가 (상태별 광고주 조회 시 성능 향상)
CREATE INDEX IF NOT EXISTS idx_advertisers_approval_status 
ON advertisers(approval_status);

-- 6. 코멘트 추가 (문서화)
COMMENT ON COLUMN advertiser_keywords.source IS 'AI 제안(ai_suggested), 사용자 입력(user_added), 또는 사용자 확정(user_confirmed) 구분';
COMMENT ON COLUMN advertiser_categories.source IS 'AI 제안(ai_suggested), 사용자 입력(user_added), 또는 사용자 확정(user_confirmed) 구분';
COMMENT ON COLUMN advertisers.approval_status IS '광고주 승인 상태: pending_analysis(AI 분석 대기), pending(심사 대기), approved(승인), rejected(거절)';

-- 마이그레이션 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully: AI onboarding features added';
END $$;

