# Website Analysis Service

AI 기반 웹사이트 분석 마이크로서비스입니다. 광고주의 웹사이트를 분석하여 최적의 키워드와 카테고리를 자동으로 생성합니다.

## 최근 업데이트 (2026-02-01)

- **Redis 캐싱**: URL 기반 AI 분석 결과 캐싱 (Cache First → Lock Later). 동일 URL 재요청 시 즉시 반환.
- **동시성 제한**: `asyncio.Semaphore(2)`로 동시 브라우저 분석 최대 2개.
- **대기열 API**: `GET /queue-status` — `available_slots`, `waiting_requests`, `estimated_wait_time` 제공.
- **타임아웃**: 분석 작업 60초 초과 시 자동 종료 및 Semaphore 반환.
- **의존성**: `redis[hiredis]`, Docker Compose에 Redis 서비스 및 `REDIS_URL` 추가.

## 기능

- 🌐 웹사이트 스크래핑 (Playwright)
- 🤖 AI 기반 비즈니스 분석 (Google Gemini)
- 🔑 자동 키워드 생성 (최대 20개)
- 📂 자동 카테고리 분류 (최대 5개)
- 📊 분석 상태 추적 및 조회

## 기술 스택

- **FastAPI**: 비동기 웹 프레임워크
- **Playwright**: 브라우저 자동화 및 웹 스크래핑
- **BeautifulSoup**: HTML 파싱
- **Google Gemini AI**: 자연어 처리 및 비즈니스 분석
- **AsyncPG**: PostgreSQL 비동기 연결

## 설치 및 실행

### 로컬 환경

```bash
# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium --with-deps

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 실제 값으로 수정

# 서비스 실행
uvicorn main:app --host 0.0.0.0 --port 8009 --reload
```

### Docker 환경

```bash
# Docker 이미지 빌드
docker build -t website-analysis-service .

# Docker 컨테이너 실행
docker run -p 8009:8009 \
  -e DATABASE_URL=postgresql://admin:password@host.docker.internal:5432/search_exchange_db \
  -e GEMINI_API_KEY=your_api_key \
  website-analysis-service
```

## API 엔드포인트

### POST /analyze
웹사이트 분석을 백그라운드로 시작합니다.

**요청:**
```json
{
  "advertiser_id": 1,
  "url": "https://example.com"
}
```

**응답:**
```json
{
  "message": "Analysis started in the background.",
  "advertiser_id": 1,
  "url": "https://example.com"
}
```

### GET /status/{advertiser_id}
특정 광고주의 분석 상태를 조회합니다.

**응답:**
```json
{
  "advertiser_id": 1,
  "approval_status": "pending",
  "review_status": "pending",
  "website_analysis": "이 회사는...",
  "ai_suggested_keywords": 15,
  "ai_suggested_categories": 3
}
```

### GET /queue-status
대기열 상태 조회 (프론트엔드 대기 시간 표시용).

**응답:**
```json
{
  "available_slots": 2,
  "waiting_requests": 0,
  "estimated_wait_time": 0
}
```

### GET /health
헬스 체크 엔드포인트입니다.

**응답:**
```json
{
  "status": "ok",
  "service": "website-analysis-service"
}
```

## 분석 프로세스

1. **상태 변경**: `approval_status`를 `pending_analysis`로 변경
2. **웹사이트 스크래핑**: Playwright로 웹페이지 텍스트 추출
3. **AI 분석**: Gemini AI로 비즈니스 요약, 키워드, 카테고리 생성
4. **결과 저장**: 
   - `advertiser_reviews.website_analysis` 업데이트
   - `advertiser_keywords` 테이블에 `source='ai_suggested'`로 저장
   - `advertiser_categories` 테이블에 `source='ai_suggested'`로 저장
5. **상태 완료**: `approval_status`를 `pending`으로 변경 (관리자 심사 대기)

## 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| DATABASE_URL | PostgreSQL 연결 URL | `postgresql://user:pass@host:5432/db` |
| REDIS_URL | Redis 연결 URL (캐시용) | `redis://redis:6379/0` |
| GEMINI_API_KEY | Google Gemini API 키 | `AIza...` |

## 주의사항

- Chromium 브라우저가 약 300MB의 디스크 공간을 사용합니다
- 웹사이트 스크래핑은 최대 60초 타임아웃이 설정되어 있습니다
- Gemini API 호출에는 API 키가 필요하며, 사용량 제한이 있을 수 있습니다
- 분석은 백그라운드로 실행되므로 즉시 결과를 반환하지 않습니다

## 트러블슈팅

### Playwright 설치 오류
```bash
playwright install chromium --with-deps
```

### 데이터베이스 연결 오류
- `DATABASE_URL`이 올바른지 확인
- PostgreSQL 서버가 실행 중인지 확인
- 방화벽 설정 확인

### Gemini API 오류
- API 키가 유효한지 확인
- API 사용량 제한을 확인
- 네트워크 연결 확인

