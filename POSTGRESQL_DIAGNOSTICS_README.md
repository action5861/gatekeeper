# PostgreSQL 성능 진단 가이드

PostgreSQL 데이터베이스의 Full Scan 여부와 인덱스 사용 현황을 진단하는 스크립트입니다.

## 실행 방법

### 방법 1: Docker 컨테이너 내부에서 실행 (권장)

```bash
# postgres 컨테이너에 접속
docker exec -it postgres-db bash

# 컨테이너 내부에서 Python 및 필요한 패키지 설치
apt-get update
apt-get install -y python3 python3-pip
pip3 install psycopg2-binary

# 스크립트를 컨테이너로 복사하거나 직접 작성
# 또는 호스트에서 스크립트를 컨테이너로 복사
docker cp diagnose_postgresql_performance_sync.py postgres-db:/tmp/

# 컨테이너 내부에서 실행
python3 /tmp/diagnose_postgresql_performance_sync.py
```

### 방법 2: 로컬에서 실행 (포트 매핑 확인 필요)

1. `docker-compose.yml`에서 PostgreSQL 포트가 올바르게 매핑되어 있는지 확인
2. 로컬에서 psycopg2-binary 설치:
   ```bash
   pip install psycopg2-binary
   ```
3. 스크립트 실행:
   ```bash
   python diagnose_postgresql_performance_sync.py
   ```

### 방법 3: psql을 사용한 수동 진단

```bash
# Docker 컨테이너에 접속
docker exec -it postgres-db psql -U admin -d search_exchange_db

# 주요 쿼리 실행 계획 확인
EXPLAIN ANALYZE 
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'exact'
  AND lower(replace(keyword, ' ', '')) = ANY(ARRAY['아이폰16프로', '아이폰', '프로']);

# 인덱스 사용 현황 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

# Full Scan 확인
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC;
```

## 진단 항목

스크립트는 다음 항목들을 확인합니다:

1. **인덱스 현황**: 모든 테이블의 인덱스 목록과 정의
2. **테이블 통계**: 행 수, 크기, 마지막 분석 시간
3. **주요 쿼리 성능 분석**:
   - EXACT 매칭 쿼리
   - PHRASE 매칭 쿼리
   - BROAD 매칭 쿼리 (LIKE 패턴 - Full Scan 위험)
   - CATEGORY 매칭 쿼리
   - 광고주 상세 조회
   - 경매 조회
4. **Full Scan 여부**: 각 쿼리에서 Sequential Scan 발생 여부
5. **인덱스 사용 통계**: 사용되지 않는 인덱스 식별

## 예상 결과

### ✅ 정상적인 경우
- Full Scan 발생 쿼리 없음
- 인덱스가 적절히 사용됨
- 실행 시간이 빠름

### ⚠️ 문제가 있는 경우
- Full Scan 발생 쿼리 발견
- 인덱스가 사용되지 않음
- 실행 시간이 느림

## 성능 개선 제안

Full Scan이 발생하는 경우:

1. **LIKE '%...%' 패턴 쿼리**: `pg_trgm` 인덱스 활용
   ```sql
   CREATE INDEX idx_adv_kw_trgm 
   ON advertiser_keywords USING gin (lower(keyword) gin_trgm_ops);
   ```

2. **표현식 인덱스**: `lower(replace(...))` 같은 표현식에 인덱스 생성
   ```sql
   CREATE INDEX idx_adv_kw_exact_expr
   ON advertiser_keywords ((lower(replace(keyword, ' ', ''))));
   ```

3. **복합 인덱스**: 여러 조건을 함께 사용하는 쿼리에 복합 인덱스 생성

## 참고

- `database/init.sql`에 이미 일부 인덱스가 정의되어 있습니다
- `pg_trgm` 확장이 설치되어 있어야 trigram 인덱스를 사용할 수 있습니다
- 정기적으로 `ANALYZE`를 실행하여 통계 정보를 업데이트하세요

