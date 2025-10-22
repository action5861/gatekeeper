@echo off
echo ========================================
echo Auction Service 성능 최적화 마이그레이션 실행
echo ========================================

echo.
echo 1. 데이터베이스 연결 확인 중...
psql -h localhost -p 5432 -U admin -d search_exchange_db -c "SELECT version();" > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 연결 실패
    echo    Docker 컨테이너가 실행 중인지 확인하세요
    echo    docker-compose up -d postgres
    pause
    exit /b 1
)

echo ✅ 데이터베이스 연결 성공

echo.
echo 2. 성능 최적화 마이그레이션 실행 중...
psql -h localhost -p 5432 -U admin -d search_exchange_db -f migration_optimize_auction_performance.sql

if %errorlevel% neq 0 (
    echo ❌ 마이그레이션 실행 실패
    pause
    exit /b 1
)

echo ✅ 성능 최적화 마이그레이션 완료

echo.
echo 3. 인덱스 생성 확인 중...
psql -h localhost -p 5432 -U admin -d search_exchange_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('advertiser_keywords', 'advertiser_categories', 'auto_bid_settings', 'bids', 'auctions')
ORDER BY tablename, indexname;
"

echo.
echo 4. 성능 통계 업데이트 중...
psql -h localhost -p 5432 -U admin -d search_exchange_db -c "ANALYZE;"

echo.
echo ========================================
echo ✅ Auction Service 성능 최적화 완료!
echo ========================================
echo.
echo 주요 개선사항:
echo - N+1 쿼리 문제 해결
echo - 데이터베이스 인덱스 최적화
echo - 쿼리 성능 3-5배 향상 예상
echo - 캐싱 메커니즘 추가
echo.
echo 다음 단계:
echo 1. auction-service 재시작
echo 2. 성능 테스트 실행
echo 3. 모니터링 설정
echo.
pause
