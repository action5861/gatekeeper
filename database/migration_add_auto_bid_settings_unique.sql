-- 자동 입찰 설정 광고주 고유 제약 추가 마이그레이션
-- 실행일: 2025-11-09

-- 중복 레코드가 있을 경우 최신(updated_at DESC, id DESC)만 남기고 정리
WITH ranked_settings AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY advertiser_id
            ORDER BY updated_at DESC NULLS LAST, id DESC
        ) AS rn
    FROM auto_bid_settings
)
DELETE FROM auto_bid_settings
WHERE id IN (
    SELECT id FROM ranked_settings WHERE rn > 1
);

-- 광고주별로 하나의 레코드만 존재하도록 고유 인덱스 생성
CREATE UNIQUE INDEX IF NOT EXISTS idx_auto_bid_settings_advertiser_unique
ON auto_bid_settings(advertiser_id);

