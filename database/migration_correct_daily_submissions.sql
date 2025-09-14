-- 🔧 과거 오집계 보정 SQL
-- daily_submissions.submission_count를 오늘 기준으로 "transactions 수"에 맞춰 보정

-- 1. 모든 사용자에 대해 오늘 카운트를 트랜잭션 수로 맞춤
WITH tx AS (
  SELECT 
    user_id, 
    CURRENT_DATE AS d, 
    COUNT(*)::int AS cnt
  FROM transactions
  WHERE created_at::date = CURRENT_DATE
  GROUP BY user_id
)
UPDATE daily_submissions ds
SET submission_count = COALESCE(tx.cnt, 0)
FROM tx
WHERE ds.user_id = tx.user_id
  AND ds.submission_date = tx.d;

-- 2. 오늘 레코드가 없는 유저도 0으로 보장
INSERT INTO daily_submissions (user_id, submission_date, submission_count, quality_score_avg)
SELECT 
  u.id, 
  CURRENT_DATE, 
  0, 
  COALESCE((
    SELECT AVG(quality_score) 
    FROM search_queries sq
    WHERE sq.user_id = u.id 
      AND sq.created_at::date = CURRENT_DATE
  ), 50)
FROM users u
WHERE NOT EXISTS (
  SELECT 1 
  FROM daily_submissions ds
  WHERE ds.user_id = u.id 
    AND ds.submission_date = CURRENT_DATE
);

-- 3. 과거 데이터도 보정 (선택적 - 필요시 주석 해제)
/*
-- 지난 7일간의 데이터 보정
WITH tx_past AS (
  SELECT 
    user_id, 
    created_at::date AS d, 
    COUNT(*)::int AS cnt
  FROM transactions
  WHERE created_at::date >= CURRENT_DATE - INTERVAL '7 days'
    AND created_at::date < CURRENT_DATE
  GROUP BY user_id, created_at::date
)
UPDATE daily_submissions ds
SET submission_count = COALESCE(tx_past.cnt, 0)
FROM tx_past
WHERE ds.user_id = tx_past.user_id
  AND ds.submission_date = tx_past.d;

-- 과거 7일간 레코드가 없는 유저들도 0으로 보장
INSERT INTO daily_submissions (user_id, submission_date, submission_count, quality_score_avg)
SELECT 
  u.id, 
  d.date_series, 
  0, 
  COALESCE((
    SELECT AVG(quality_score) 
    FROM search_queries sq
    WHERE sq.user_id = u.id 
      AND sq.created_at::date = d.date_series
  ), 50)
FROM users u
CROSS JOIN (
  SELECT generate_series(
    CURRENT_DATE - INTERVAL '7 days',
    CURRENT_DATE - INTERVAL '1 day',
    INTERVAL '1 day'
  )::date AS date_series
) d
WHERE NOT EXISTS (
  SELECT 1 
  FROM daily_submissions ds
  WHERE ds.user_id = u.id 
    AND ds.submission_date = d.date_series
);
*/

-- 4. 보정 결과 확인 쿼리
SELECT 
  '보정 전후 비교' AS description,
  ds.user_id,
  ds.submission_date,
  ds.submission_count AS daily_submissions_count,
  COALESCE(tx.tx_count, 0) AS transactions_count,
  CASE 
    WHEN ds.submission_count = COALESCE(tx.tx_count, 0) THEN '일치'
    ELSE '불일치'
  END AS status
FROM daily_submissions ds
LEFT JOIN (
  SELECT 
    user_id,
    created_at::date AS tx_date,
    COUNT(*)::int AS tx_count
  FROM transactions
  WHERE created_at::date = CURRENT_DATE
  GROUP BY user_id, created_at::date
) tx ON ds.user_id = tx.user_id AND ds.submission_date = tx.tx_date
WHERE ds.submission_date = CURRENT_DATE
ORDER BY ds.user_id;

COMMIT;
