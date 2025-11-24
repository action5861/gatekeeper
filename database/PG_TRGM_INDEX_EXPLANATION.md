# pg_trgm 인덱스 최적화 설명서

## 🎯 왜 필요한가?

현재 Auction Service의 `find_matching_advertisers()` 함수는 다음과 같은 쿼리 패턴을 사용합니다:

1. **정확 매칭**: `lower(replace(keyword, ' ', '')) = ANY(:tokens_norm)`
2. **부분 매칭**: `lower(keyword) LIKE '%token%'`
3. **카테고리 경로 매칭**: `category_path LIKE '경로%'`

이러한 패턴들은 **전체 테이블 스캔(Full Table Scan)**을 유발하여 성능 저하를 일으킵니다.

## 📊 성능 개선 효과

### 인덱스 없을 때 (Full Table Scan)
- 10,000개 키워드 기준: ~100-500ms
- 100,000개 키워드 기준: ~1-5초

### 인덱스 적용 후 (Index Scan)
- 10,000개 키워드 기준: ~1-10ms ⚡ **50-100배 향상**
- 100,000개 키워드 기준: ~10-50ms ⚡ **20-50배 향상**

## 🔍 각 인덱스의 역할

### 1. `idx_adv_kw_trgm` (GIN Trigram 인덱스)
```sql
CREATE INDEX idx_adv_kw_trgm
ON advertiser_keywords USING gin (lower(keyword) gin_trgm_ops);
```

**용도:**
- `LIKE '%keyword%'` 패턴 검색 최적화
- 한글 2-gram, 3-gram 기반 유사도 검색
- **BROAD 매칭 타입** 쿼리 성능 향상

**활용 쿼리 예시:**
```sql
SELECT * FROM advertiser_keywords 
WHERE lower(keyword) LIKE '%스마트폰%';  -- 인덱스 사용!
```

### 2. `idx_adv_kw_exact_expr` (표현식 인덱스)
```sql
CREATE INDEX idx_adv_kw_exact_expr
ON advertiser_keywords ((lower(replace(keyword, ' ', ''))));
```

**용도:**
- `lower(replace(keyword, ' ', ''))` 표현식 검색 최적화
- **EXACT 매칭 타입** 쿼리 성능 향상
- 공백 제거 후 정규화된 키워드 검색

**활용 쿼리 예시:**
```sql
SELECT * FROM advertiser_keywords 
WHERE lower(replace(keyword, ' ', '')) = '스마트폰';  -- 인덱스 사용!
```

### 3. `idx_cat_name_trgm` (카테고리 이름 Trigram 인덱스)
```sql
CREATE INDEX idx_cat_name_trgm
ON business_categories USING gin (lower(name) gin_trgm_ops);
```

**용도:**
- `business_categories.name LIKE '%카테고리명%'` 검색 최적화
- 카테고리 매칭 쿼리 성능 향상

**활용 쿼리 예시:**
```sql
SELECT * FROM business_categories 
WHERE lower(name) LIKE '%전자제품%';  -- 인덱스 사용!
```

### 4. `idx_adv_cat_path` (경로 패턴 인덱스)
```sql
CREATE INDEX idx_adv_cat_path
ON advertiser_categories (category_path text_pattern_ops);
```

**용도:**
- `category_path LIKE '경로%'` 패턴 검색 최적화
- 계층적 카테고리 경로 매칭 (예: '전자제품 > 스마트폰%')

**활용 쿼리 예시:**
```sql
SELECT * FROM advertiser_categories 
WHERE category_path LIKE '전자제품 > 스마트폰%';  -- 인덱스 사용!
```

## ⚙️ pg_trgm 확장이란?

**pg_trgm (PostgreSQL Trigram)**:
- 텍스트를 3글자씩 나눠서 인덱싱하는 PostgreSQL 확장
- 한글, 영어, 숫자 등 모든 문자 지원
- `LIKE`, `ILIKE`, `SIMILAR TO` 연산자 최적화
- 유사도 검색(`%`, `similarity()`) 지원

**설치:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## 🚀 실제 쿼리 성능 비교

### 인덱스 없을 때
```sql
EXPLAIN ANALYZE
SELECT advertiser_id, keyword 
FROM advertiser_keywords 
WHERE lower(keyword) LIKE '%스마트폰%';
```
**결과:** `Seq Scan on advertiser_keywords` (Full Table Scan, 느림)

### 인덱스 있을 때
```sql
EXPLAIN ANALYZE
SELECT advertiser_id, keyword 
FROM advertiser_keywords 
WHERE lower(keyword) LIKE '%스마트폰%';
```
**결과:** `Bitmap Index Scan on idx_adv_kw_trgm` (Index Scan, 빠름)

## ✅ 적용 확인 방법

```sql
-- 1. 확장 설치 확인
SELECT * FROM pg_extension WHERE extname = 'pg_trgm';

-- 2. 인덱스 존재 확인
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('advertiser_keywords', 'business_categories', 'advertiser_categories')
  AND indexname LIKE 'idx_%trgm%' OR indexname LIKE 'idx_%_expr%' OR indexname LIKE 'idx_%_path';

-- 3. 쿼리 실행 계획 확인 (인덱스 사용 여부)
EXPLAIN ANALYZE
SELECT advertiser_id 
FROM advertiser_keywords 
WHERE lower(keyword) LIKE '%테스트%';
```

## 📝 주의사항

1. **인덱스 생성 시간**: 대용량 테이블(100만 행 이상)에서는 인덱스 생성에 수분~수십분 소요될 수 있습니다.
2. **저장 공간**: GIN 인덱스는 약 2-3배의 추가 저장 공간을 사용합니다.
3. **업데이트 오버헤드**: 키워드 추가/수정 시 인덱스도 함께 업데이트되므로 약간의 오버헤드가 있습니다.

## 🎯 결론

이 인덱스들은 **반드시 필요**합니다:
- 사용자 검색어 매칭이 **실시간으로** 처리되어야 함
- 수천~수만 개의 키워드에서 빠른 검색 필요
- **프로덕션 환경**에서 응답 시간 지연 방지

**인덱스 없으면:** 검색 요청마다 전체 테이블 스캔 → 서버 부하 증가 → 사용자 대기 시간 증가

**인덱스 있으면:** 즉시 매칭 가능 → 빠른 응답 시간 → 확장 가능한 시스템

---

**작성일**: 2024년  
**상태**: ✅ 모든 인덱스 `database/init.sql`에 포함됨

