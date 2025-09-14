@echo off
echo 🔧 Daily Submissions 보정 마이그레이션 실행
echo.

REM 환경 변수 설정
set PGPASSWORD=your_secure_password_123
set PGHOST=localhost
set PGPORT=5433
set PGUSER=admin
set PGDATABASE=search_exchange_db

echo 📊 현재 daily_submissions 상태 확인...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -c "
SELECT 
  '보정 전 상태' AS description,
  ds.user_id,
  ds.submission_date,
  ds.submission_count AS daily_submissions_count,
  COALESCE(tx.tx_count, 0) AS transactions_count
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
"

echo.
echo 🔧 보정 마이그레이션 실행...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f migration_correct_daily_submissions.sql

echo.
echo ✅ 보정 완료! 결과 확인:
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -c "
SELECT 
  '보정 후 상태' AS description,
  ds.user_id,
  ds.submission_date,
  ds.submission_count AS daily_submissions_count,
  COALESCE(tx.tx_count, 0) AS transactions_count,
  CASE 
    WHEN ds.submission_count = COALESCE(tx.tx_count, 0) THEN '✅ 일치'
    ELSE '❌ 불일치'
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
"

echo.
echo 🎉 Daily Submissions 보정 마이그레이션이 완료되었습니다!
pause
