-- DigiSafe Auction Service Migration: 플랫폼 광고주 및 auto_bid_logs 보강

-- 기존 스키마의 NOT NULL 컬럼을 모두 채워줍니다.
INSERT INTO advertisers (
    id,
    username,
    email,
    hashed_password,
    company_name,
    website_url,
    daily_budget,
    approval_status,
    created_at,
    updated_at
)
VALUES (
    1,
    'platform_system',
    'platform@intendex.com',
    '$2b$12$platformsystemplaceholderhash000000000000000000000000000000',
    'Platform System',
    'https://intendex.com',
    100000.00,
    'approved',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;


-- 2) auto_bid_logs.reasons JSONB 컬럼 보장
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'auto_bid_logs'
          AND column_name = 'reasons'
    ) THEN
        ALTER TABLE auto_bid_logs
            ADD COLUMN reasons JSONB DEFAULT '[]'::jsonb;
    END IF;
END$$;


-- 3) reasons 컬럼이 JSONB가 아닐 경우 JSONB로 변환
DO $$
DECLARE
    v_udt TEXT;
BEGIN
    SELECT udt_name INTO v_udt
    FROM information_schema.columns
    WHERE table_name = 'auto_bid_logs'
      AND column_name = 'reasons';

    IF v_udt IS NOT NULL AND v_udt <> 'jsonb' THEN
        ALTER TABLE auto_bid_logs
            ALTER COLUMN reasons TYPE JSONB
            USING
                CASE
                    WHEN reasons IS NULL THEN '[]'::jsonb
                    WHEN pg_typeof(reasons)::text = 'jsonb' THEN reasons
                    ELSE to_jsonb(reasons)
                END;
    END IF;
END$$;


-- 4) advertiser_id는 NULL 허용 상태 유지 (재보장)
ALTER TABLE auto_bid_logs
    ALTER COLUMN advertiser_id DROP NOT NULL;

