# Auction Service 7초 지연 원인 분석

## 📊 실행 흐름 분석

### 주요 엔드포인트: `/start`
```
POST /start
  → start_reverse_auction()
    → generate_real_advertiser_bids()
      → find_matching_advertisers()  [병목 1]
      → 광고주 상세 정보 조회
      → 입찰 생성 및 저장
```

## 🔴 주요 병목 지점

### 1. Gemini API 호출 (가장 큰 병목) ⚠️

#### 1-1. 임베딩 생성 (`get_query_embedding`)
- **위치**: `find_matching_advertisers()` Line 962
- **실행 방식**: `asyncio.create_task()`로 백그라운드 시작 → Line 1121에서 `await`
- **예상 시간**: **1-3초**
- **문제점**: 
  - 비동기로 시작하지만, 시맨틱 매칭 로직에서 await하기 전까지 대기
  - Gemini API 응답 시간이 네트워크 지연에 따라 변동

#### 1-2. 카테고리 분류 (`classify_query_categories`)
- **위치**: `find_matching_advertisers()` Line 961
- **실행 방식**: `asyncio.create_task()`로 백그라운드 시작 → Line 1090에서 `await`
- **예상 시간**: **1-2초**
- **문제점**: 
  - `model.generate_content()` 동기 호출을 `asyncio.to_thread()`로 감싸지만 여전히 느림
  - Gemini Flash 모델 사용 시에도 1-2초 소요

#### 1-3. 의도 검증 (`verify_intent_with_gemini`) - **가장 큰 병목** 🔴
- **위치**: `find_matching_advertisers()` Line 1394
- **실행 방식**: 
  - `asyncio.Semaphore(3)`로 최대 3개 동시 호출 제한
  - `asyncio.gather()`로 병렬 실행하지만, 후보가 많으면 순차 대기
- **예상 시간**: 
  - 후보 5명 × 각 1-2초 = **5-10초** (Semaphore로 제한되어도)
  - 후보 10명이면 **10-20초** 가능
- **문제점**:
  ```python
  # Line 1408-1411
  verification_results = await asyncio.gather(
      *[verify_candidate(adv) for adv in top_candidates],
      return_exceptions=True,
  )
  ```
  - `top_candidates`가 많을수록 총 시간이 증가
  - Semaphore(3)로 제한되어도, 10명 후보면 최소 3-4초 소요 (3개씩 순차 처리)

### 2. 데이터베이스 쿼리 (상대적으로 빠름) ✅

#### 2-1. 텍스트 매칭 쿼리들 (병렬 실행)
- **위치**: `find_matching_advertisers()` Line 1039-1046
- **쿼리**: EXACT, PHRASE, BROAD, CATEGORY
- **실행 방식**: `asyncio.gather()`로 병렬 실행
- **예상 시간**: **0.1-0.5초** (병렬 실행으로 빠름)

#### 2-2. 시맨틱 매칭 쿼리 (pgvector)
- **위치**: `find_matching_advertisers()` Line 1132
- **실행 시점**: `query_embedding` 완료 후 (임베딩 대기 시간 포함)
- **예상 시간**: **0.1-0.3초** (인덱스 사용 시 빠름)

#### 2-3. 광고주 상세 정보 조회
- **위치**: `generate_real_advertiser_bids()` Line 1672
- **예상 시간**: **0.1-0.2초**

### 3. 예산 예약 및 입찰 저장 (중간 병목) ⚠️

#### 3-1. `reserve_and_insert_bid`
- **위치**: `start_auction()` Line 2238-2269
- **실행 방식**: 
  - 광고주별로 그룹화하여 병렬 실행
  - 각 그룹 내에서는 순차 실행 (트랜잭션 안전성)
- **예상 시간**: 
  - 입찰 5개 × 각 0.2-0.5초 = **1-2.5초**
- **문제점**:
  - 트랜잭션 락으로 인한 대기 가능
  - 각 입찰마다 DB 트랜잭션 실행

## ⏱️ 시간 분해 (예상)

### 시나리오 1: 후보 5명, Gemini API 정상
```
1. DB 쿼리 (병렬)              : 0.3초
2. 임베딩 생성 (대기)           : 2.0초
3. 카테고리 분류 (대기)         : 1.5초
4. 시맨틱 매칭 쿼리             : 0.2초
5. 의도 검증 (5명, Semaphore 3): 3.0초 (2+1초)
6. 광고주 상세 조회             : 0.2초
7. 입찰 생성 및 저장            : 1.5초
─────────────────────────────────────
총합: 약 8.7초
```

### 시나리오 2: 후보 10명, Gemini API 느림
```
1. DB 쿼리 (병렬)              : 0.3초
2. 임베딩 생성 (대기)           : 3.0초
3. 카테고리 분류 (대기)         : 2.0초
4. 시맨틱 매칭 쿼리             : 0.2초
5. 의도 검증 (10명, Semaphore 3): 6.0초 (3+3초)
6. 광고주 상세 조회             : 0.2초
7. 입찰 생성 및 저장            : 2.0초
─────────────────────────────────────
총합: 약 13.7초
```

## 🔍 상세 분석

### Gemini API 호출 패턴

#### 병렬 처리 현황
```python
# Line 956-962: 백그라운드로 시작
if SEMANTIC_ENABLED:
    task_cat = asyncio.create_task(classify_query_categories(search_query))
    task_emb = asyncio.create_task(get_query_embedding(search_query))

# Line 1090: 카테고리 분류 대기
query_categories = await task_cat

# Line 1121: 임베딩 대기
query_embedding = await task_emb
```

**문제점**:
- 두 작업이 병렬로 시작되지만, 각각 await 시점에서 순차 대기
- 실제로는 `max(임베딩 시간, 카테고리 시간)` 만큼만 대기하지만, 둘 다 느리면 합산됨

#### 의도 검증 병목
```python
# Line 1381: Semaphore로 제한
sem = asyncio.Semaphore(3)  # 최대 3개 동시

# Line 1408: 모든 후보를 병렬로 검증
verification_results = await asyncio.gather(
    *[verify_candidate(adv) for adv in top_candidates],
)
```

**문제점**:
- `top_candidates`가 많을수록 총 시간 증가
- Semaphore(3)로 제한되어도:
  - 5명: 2초 (3개 동시) + 1초 (2개 동시) = 3초
  - 10명: 2초 (3개) + 2초 (3개) + 2초 (3개) + 1초 (1개) = 7초

### 데이터베이스 쿼리 최적화 상태

✅ **잘 최적화됨**:
- 텍스트 매칭 쿼리들이 `asyncio.gather()`로 병렬 실행
- 인덱스 사용 확인 (이전 진단에서 확인)

⚠️ **개선 여지**:
- 시맨틱 매칭 쿼리는 임베딩 완료 후 실행 (순차 의존성)

## 📈 성능 개선 포인트 (참고용)

### 즉시 개선 가능
1. **의도 검증 최적화**
   - 후보 수 제한 (예: 상위 5명만 검증)
   - Semaphore 증가 (3 → 5)
   - 타임아웃 설정

2. **Gemini API 호출 최적화**
   - 타임아웃 설정 (예: 2초)
   - 실패 시 빠른 폴백
   - 캐싱 고려

3. **임베딩/카테고리 분류 최적화**
   - 타임아웃 설정
   - 실패 시 기본값 사용

### 장기 개선
1. **캐싱 전략**
   - 검색어 임베딩 캐싱
   - 카테고리 분류 결과 캐싱
   - 의도 검증 결과 캐싱

2. **비동기 처리**
   - 의도 검증을 백그라운드로 처리
   - 결과는 나중에 필터링

3. **데이터베이스 최적화**
   - 시맨틱 매칭 쿼리 인덱스 확인
   - 쿼리 실행 계획 분석

## 🎯 결론

### 주요 원인 (우선순위)

1. **🔴 의도 검증 (`verify_intent_with_gemini`)** - **가장 큰 병목**
   - 후보 수에 비례하여 시간 증가
   - Semaphore 제한으로 인한 순차 대기
   - 각 호출당 1-2초 소요

2. **🟡 임베딩 생성 (`get_query_embedding`)** - **두 번째 병목**
   - Gemini API 응답 시간: 1-3초
   - 네트워크 지연에 민감

3. **🟡 카테고리 분류 (`classify_query_categories`)** - **세 번째 병목**
   - Gemini API 응답 시간: 1-2초
   - 임베딩과 병렬이지만 둘 다 느리면 합산

4. **🟢 입찰 저장** - **상대적으로 빠름**
   - 트랜잭션 락으로 인한 대기 가능
   - 입찰 수에 비례

### 예상 시간 분포 (후보 5명 기준)
- 의도 검증: **3-4초** (40-50%)
- 임베딩 생성: **2-3초** (25-35%)
- 카테고리 분류: **1-2초** (12-25%)
- 기타 (DB, 입찰 저장): **1-2초** (12-25%)

### 권장 조치 (우선순위)

1. **의도 검증 후보 수 제한** (가장 효과적)
   - 상위 5명만 검증하도록 제한
   - 예상 개선: 3-4초 → 1-2초

2. **Gemini API 타임아웃 설정**
   - 각 호출에 2초 타임아웃
   - 예상 개선: 최악의 경우 방지

3. **의도 검증 Semaphore 증가**
   - 3 → 5로 증가
   - 예상 개선: 10-20% 개선

4. **캐싱 도입** (장기)
   - 검색어 임베딩 캐싱
   - 예상 개선: 2-3초 → 0.1초


