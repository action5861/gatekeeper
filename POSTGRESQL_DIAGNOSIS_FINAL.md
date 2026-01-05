# PostgreSQL 성능 진단 최종 결과

## 📊 진단 요약

### ✅ 정상 작동하는 쿼리 (Index Scan 사용)

1. **EXACT 매칭**: Index Scan 사용, 실행 시간 0.021ms ✅
2. **PHRASE 매칭**: Index Scan 사용, 실행 시간 0.038ms ✅  
3. **경매 조회**: Index Scan 사용, 실행 시간 0.552ms ✅

### ❌ Full Scan 발생 쿼리 (성능 개선 필요)

1. **BROAD 매칭 쿼리**
   - **현재**: Seq Scan (Full Scan) ❌
   - **실행 시간**: 0.263-0.529ms
   - **스캔된 행 수**: 374행
   - **원인**: `LIKE '%...%'` 패턴은 pg_trgm 인덱스를 자동으로 사용하지 않음

2. **CATEGORY 매칭 쿼리**
   - **현재**: Seq Scan on `business_categories` ❌
   - **실행 시간**: 0.713ms
   - **스캔된 행 수**: 2360행

## 🔧 조치 사항

### 완료된 작업

1. ✅ `pg_trgm` 확장 설치
2. ✅ `idx_adv_kw_trgm` GIN 인덱스 생성

### 추가 작업 필요

**BROAD 매칭 쿼리 최적화 방법:**

현재 쿼리:
```sql
WHERE match_type = 'broad'
  AND (
    :query_norm LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
    OR lower(replace(keyword, ' ', '')) LIKE '%' || :query_norm || '%'
  )
```

**옵션 1: pg_trgm 연산자 사용 (권장)**
```sql
WHERE match_type = 'broad'
  AND (
    lower(replace(keyword, ' ', '')) % :query_norm  -- 유사도 연산자
    OR similarity(lower(replace(keyword, ' ', '')), :query_norm) > 0.3
  )
```

**옵션 2: 현재 쿼리 유지 + 통계 업데이트**
```sql
-- 통계 정보 업데이트로 쿼리 플래너가 인덱스를 고려하도록
ANALYZE advertiser_keywords;

-- 또는 설정 변경
SET enable_seqscan = off;  -- 테스트용 (프로덕션에서는 권장하지 않음)
```

## 📈 성능 영향 분석

### 현재 상황
- **데이터 규모**: advertiser_keywords 테이블에 374행
- **Full Scan 시간**: 0.263-0.529ms (현재는 빠름)
- **예상 문제**: 데이터가 10,000행 이상으로 증가하면 성능 저하 예상

### 예상 성능 개선
- **현재 (374행)**: Full Scan 0.263ms
- **10,000행 예상**: Full Scan ~7ms
- **인덱스 사용 시**: 0.01-0.1ms (70-700배 개선)

## 💡 권장 사항

### 즉시 조치
1. ✅ `pg_trgm` 확장 설치 완료
2. ✅ `idx_adv_kw_trgm` 인덱스 생성 완료
3. ⚠️ **BROAD 매칭 쿼리를 pg_trgm 연산자 사용하도록 수정** (필수)

### 장기 조치
1. 정기적으로 `ANALYZE` 실행하여 통계 정보 업데이트
2. 데이터 증가에 따른 성능 모니터링
3. 쿼리 실행 계획 정기 점검

## 🔍 코드 수정 위치

`services/auction_service/main.py`의 `BROAD_SQL` 쿼리 수정 필요:

```python
# 현재 (Line 335-343)
BROAD_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'broad'
  AND (
    :query_norm LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
    OR lower(replace(keyword, ' ', '')) LIKE '%' || :query_norm || '%'
  )
"""

# 수정 제안
BROAD_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'broad'
  AND (
    lower(replace(keyword, ' ', '')) % :query_norm
    OR similarity(lower(replace(keyword, ' ', '')), :query_norm) > 0.3
  )
"""
```

## ✅ 결론

1. **EXACT, PHRASE, 경매 조회**: 인덱스를 효율적으로 사용 중 ✅
2. **BROAD 매칭**: Full Scan 발생 - 쿼리 수정 필요 ⚠️
3. **인덱스는 준비됨**: `pg_trgm` 인덱스 생성 완료 ✅
4. **다음 단계**: BROAD 매칭 쿼리를 pg_trgm 연산자 사용하도록 수정

