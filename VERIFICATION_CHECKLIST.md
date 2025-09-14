# 🔍 Daily 사용량 통일 검증 체크리스트

## 📋 검증 항목

### 1. 환경 설정 확인
- [ ] `.env` 파일에 `DEFAULT_DAILY_LIMIT=5` 설정 확인
- [ ] 데이터베이스 마이그레이션 실행 완료
  - [ ] `migration_add_transaction_constraints.sql` 실행
  - [ ] `migration_correct_daily_submissions.sql` 실행

### 2. 로그인 → 대시보드 확인
- [ ] 로그인 성공
- [ ] `/dashboard` 접근 시 Today's Usage가 `0/5`로 표시
- [ ] 검색만 여러 번 해도 사용량 변동 없음 (0/5 유지)

### 3. 광고 클릭 → 보상 지급 테스트
- [ ] 검색 후 입찰 광고 클릭
- [ ] 네트워크 탭에서 `/api/user/earnings` 1회만 호출 확인
- [ ] 대시보드 Today's Usage가 `1/5`로 갱신
- [ ] 거래 1건 생성 확인

### 4. 중복 클릭 방지 테스트
- [ ] 동일한 광고를 빠르게 여러 번 클릭
- [ ] `/api/user/earnings`에서 멱등성 응답 확인
- [ ] 사용량이 중복으로 증가하지 않음

### 5. 일일 한도 초과 테스트
- [ ] 5번째 광고 클릭까지 정상 작동
- [ ] 6번째 광고 클릭 시 HTTP 429 에러 반환
- [ ] 에러 메시지: "일일 제출 한도(5회)를 초과했습니다"

### 6. 새로고침 후 일관성 확인
- [ ] 브라우저 새로고침 후 대시보드 표시 일치
- [ ] 서버 계산 기준이므로 일관된 표시 확인

### 7. 데이터베이스 정합성 확인
```sql
-- 오늘 트랜잭션 수와 daily_submissions 일치 확인
SELECT 
  ds.user_id,
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
    COUNT(*)::int AS tx_count
  FROM transactions
  WHERE created_at::date = CURRENT_DATE
  GROUP BY user_id
) tx ON ds.user_id = tx.user_id
WHERE ds.submission_date = CURRENT_DATE
ORDER BY ds.user_id;
```

## 🚨 문제 발생 시 체크리스트

### 백엔드 문제
- [ ] user-service 로그 확인
- [ ] 데이터베이스 연결 상태 확인
- [ ] 환경 변수 설정 확인

### 프론트엔드 문제
- [ ] 브라우저 개발자 도구 네트워크 탭 확인
- [ ] API 응답 상태 코드 확인
- [ ] StrictMode 가드 작동 확인

### 데이터베이스 문제
- [ ] transactions 테이블 유니크 제약조건 확인
- [ ] daily_submissions 테이블 데이터 정합성 확인
- [ ] 마이그레이션 실행 상태 확인

## 📊 성공 기준

✅ **모든 검증 항목 통과 시:**
- Daily 사용량이 트랜잭션 수 기준으로 정확히 계산됨
- 중복 호출/집계가 완전히 차단됨
- 멱등성이 보장됨
- 일일 한도가 정확히 적용됨
- 프론트엔드와 백엔드 표시가 일치함

## 🔧 문제 해결 명령어

```bash
# 데이터베이스 보정 마이그레이션 실행
cd database
./run_correction_migration.sh  # Linux/Mac
# 또는
run_correction_migration.bat   # Windows

# 서비스 재시작
docker-compose restart user-service

# 로그 확인
docker-compose logs -f user-service
```
