# 일일 제출 한도 시스템 리팩터링 완료 보고서

## 📋 개요

일일 제출 한도 시스템을 안전하고 효율적으로 리팩터링하여, 하드 캡(Hard Cap) + 보너스 한도(Bonus Cap) 구조로 정리하고, 모든 한도 계산 로직을 공통 모듈로 분리했습니다.

## ✅ 완료된 작업

### 1. 공통 한도 정책 모듈 생성

**파일**: `services/shared/limit_policy.py`

- `LimitInfo` dataclass 생성: `daily_max`, `level` 필드 포함
- `calculate_dynamic_limit()` 함수 구현
- 기존 비즈니스 규칙 유지:
  - 70점 미만: 기본 한도 (5회)
  - 70점 이상: 기본 한도 + 10회 (15회)
- 추후 확장 가능한 구조로 설계 (settled_today 파라미터 포함)

**변경 목적**: 
- 한도 정책의 단일 소스(Single Source of Truth) 제공
- User Service와 Quality Service에서 동일한 정책 사용 보장
- 향후 정책 변경 시 한 곳만 수정하면 모든 서비스에 반영

### 2. User Service 리팩터링

**파일**: `services/user-service/main.py`

#### 2-1. 공통 모듈 import
- `from shared.limit_policy import calculate_dynamic_limit, LimitInfo` 추가
- 기존 `calculate_dynamic_limit()` 함수 제거

#### 2-2. 헬퍼 함수 개선
- `_used_today_from_tx()`: 기존 로직 유지 (오늘 생성된 모든 트랜잭션 카운트)
- `_settled_today_from_tx()`: 새로 추가 (오늘 정산 완료된 트랜잭션 카운트, 추후 확장용)
- `_remaining_from_tx()`: 공통 모듈 사용하도록 수정

#### 2-3. 한도 체크 + 트랜잭션 생성 통합
- `_check_limit_and_create_transaction()` 함수 생성
- **하나의 DB 트랜잭션 내에서** 다음 작업 수행:
  1. 오늘 사용량 조회 (`_used_today_from_tx`)
  2. 오늘 정산 완료 건수 조회 (`_settled_today_from_tx`, 확장용)
  3. 공통 모듈로 한도 계산 (`calculate_dynamic_limit`)
  4. 하드 캡 초과 여부 체크
  5. 트랜잭션 생성 (PENDING_VERIFICATION 상태)

**변경 목적**:
- Race condition 방지: 모든 작업을 하나의 DB 트랜잭션으로 처리
- 코드 중복 제거: 기존에 흩어져 있던 한도 체크 로직 통합
- 안전성 향상: 동시 요청 시에도 한도 초과 방지

#### 2-4. `/api/user/earnings` 엔드포인트 리팩터링
- 기존 복잡한 한도 체크 로직 제거
- `_check_limit_and_create_transaction()` 함수 호출로 단순화
- 멱등성 체크는 그대로 유지

### 3. Quality Service 리팩터링

**파일**: `services/quality-service/main.py`

- 공통 모듈 import 추가
- 기존 `calculate_dynamic_limit()` 함수 제거
- `/calculate-limit` 엔드포인트에서 공통 모듈 사용
- `SubmissionLimit` 모델에 "Standard" 레벨 추가 (호환성)

**변경 목적**:
- User Service와 동일한 한도 정책 사용
- 정책 변경 시 한 곳만 수정하면 모든 서비스에 반영

### 4. DB 인덱스 추가

**파일**: `database/migration_add_transactions_daily_limit_index.sql`

다음 인덱스 추가:
1. `idx_transactions_user_date_daily_limit`: user_id, created_at 기준 (일일 트랜잭션 조회 최적화)
2. `idx_transactions_user_date_status`: user_id, created_at, status 기준 (정산 완료 트랜잭션 조회 최적화, 추후 확장용)
3. `idx_transactions_idempotency`: user_id, search_id, bid_id, created_at 기준 (멱등성 체크 최적화)

**변경 목적**:
- `_used_today_from_tx()` 함수의 성능 향상
- 추후 정산 완료 건수 기반 보너스 한도 정책 구현 시 성능 최적화

## 🔄 변경 전후 비교

### 변경 전
- User Service와 Quality Service에 각각 `calculate_dynamic_limit()` 함수 존재
- 한도 체크 로직이 여러 곳에 분산
- 트랜잭션 생성 전후로 한도 체크가 분리되어 race condition 위험
- 코드 중복 및 유지보수 어려움

### 변경 후
- 공통 모듈(`shared/limit_policy.py`)에서 한도 정책 관리
- 한도 체크 + 트랜잭션 생성이 하나의 DB 트랜잭션으로 처리
- Race condition 방지
- 코드 중복 제거 및 유지보수 용이

## 📊 기존 비즈니스 규칙 유지

다음 규칙은 그대로 유지됩니다:
- **기본 한도**: 환경 변수 `DEFAULT_DAILY_LIMIT` (기본값: 5회)
- **70점 미만**: 기본 한도 (5회)
- **70점 이상**: 기본 한도 + 10회 (15회)
- **사용량 계산**: 오늘 생성된 모든 트랜잭션 카운트 (상태 무관)

## 🚀 향후 확장 가능성

공통 모듈의 구조는 다음 확장을 지원합니다:

1. **정산 완료 건수 기반 보너스 한도**
   - `settled_today` 파라미터 활용
   - 예: 정산 완료 5건 이상 시 추가 한도 제공

2. **품질 점수 등급별 세분화**
   - 90점 이상: 20회
   - 80점 이상: 15회
   - 70점 이상: 12회
   - 70점 미만: 5회

3. **하이브리드 한도 정책**
   - 기본 한도: 모든 트랜잭션 카운트 (실시간)
   - 보너스 한도: 정산 완료된 트랜잭션만 카운트

## 📝 테스트 시나리오

다음 시나리오를 수동/자동 테스트로 점검하세요:

1. **품질 점수 60점 유저**
   - 오늘 처음 제출 → 통과, used=1, dailyLimit=5
   - 5회까지는 통과, 6회째 요청 시 429 응답

2. **품질 점수 80점 유저**
   - 현재 정책상 15회로 계산되는지 확인
   - 15회까지 통과, 16회째 요청 시 429

3. **동시 요청**
   - 같은 유저가 거의 동시에 여러 요청을 보내더라도,
   - 하드 캡을 넘기지 않고 초과분은 429로 처리되는지 확인
   - (DB 트랜잭션 내에서 카운트 + 생성이 잘 묶였는지 확인)

## 🔧 마이그레이션 실행

DB 인덱스를 추가하려면 다음 SQL을 실행하세요:

```sql
-- database/migration_add_transactions_daily_limit_index.sql 파일 실행
```

또는 직접 실행:

```bash
psql -U admin -d search_exchange_db -f database/migration_add_transactions_daily_limit_index.sql
```

## 📌 주의사항

1. **환경 변수 확인**: `DEFAULT_DAILY_LIMIT` 환경 변수가 설정되어 있는지 확인
2. **Python 경로**: `services/shared` 디렉토리가 Python 경로에 포함되어 있는지 확인
3. **기존 기능 유지**: 기존 비즈니스 규칙은 그대로 유지되므로, 기존 동작과 동일해야 함

## ✨ 개선 효과

1. **안전성 향상**: Race condition 방지로 동시 요청 시에도 한도 초과 방지
2. **유지보수성 향상**: 한도 정책 변경 시 한 곳만 수정하면 모든 서비스에 반영
3. **성능 향상**: DB 인덱스 추가로 일일 트랜잭션 조회 성능 개선
4. **확장성 향상**: 추후 정산 완료 건수 기반 보너스 한도 정책 구현 용이

