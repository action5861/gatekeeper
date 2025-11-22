# Intendex - Real-time Intent Exchange Platform

검색 의도를 실시간으로 거래하는 세계 최초의 인텐트 거래소

> "List what you're searching for. Advertisers bid in real-time. Get settled when SLA is verified—or they get refunded."

---

## 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [시스템 아키텍처](#-시스템-아키텍처)
3. [사용자 여정](#-사용자-여정)
4. [핵심 비즈니스 플로우](#-핵심-비즈니스-플로우)
5. [AI 분석 시스템](#-ai-분석-시스템-gemini)
6. [2단계 하이브리드 SLA 시스템](#-2단계-하이브리드-sla-시스템-핵심)
7. [주요 기능 상세](#-주요-기능-상세)
8. [빠른 시작](#-빠른-시작)
9. [API 엔드포인트](#-api-엔드포인트)
10. [테스트 가이드](#-테스트-가이드)
11. [문제 해결](#-문제-해결)
12. [개발 히스토리](#-개발-히스토리)

---

## 📖 프로젝트 개요

### Intendex란?

**Intendex**는 사용자의 검색 의도(Intent)를 실시간으로 경매하여 가치를 측정하고 거래하는 세계 최초의 인텐트 거래소입니다.

### 왜 만들었나?

전통적인 광고 네트워크의 문제점:
- ❌ **불투명한 가격**: 광고주가 실제 효과를 알 수 없음
- ❌ **봇 트래픽**: 클릭 수는 많지만 실제 매출은 없음
- ❌ **중간 수수료**: 복잡한 계층 구조로 비효율적
- ❌ **사용자 혜택 없음**: 데이터를 제공하지만 돈을 받지 못함

### Intendex의 해결책:

- ✅ **투명한 거래**: 모든 입찰가와 정산이 블록체인처럼 공개적으로 로깅됨
- ✅ **SLA 검증**: 2단계 검증으로 진짜 관심도만 측정 (봇 자동 차단)
- ✅ **직접 거래**: 중간 업체 없이 사용자 ↔ 광고주 직접 매칭
- ✅ **사용자 수익**: 검색 의도에 대해 바로 돈을 받음

### 핵심 혁신

1. **검색 의도는 자산**: 당신의 "무엇을 할려고 하는 생각이나 계획"이이 실제 자산이 됩니다.
2. **AI 기반 평가**: Google Gemini가 검색어 가치를 실시간 평가
3. **SLA 보장**: 광고주는 진짜 클릭에만 돈을 지불, 사용자는 더 많이 탐색하면 더 많이 버세요
4. **자동화**: AI가 광고주 키워드를 자동 추천, 광고주는 파라미터만 설정

---

## 🏗️ 시스템 아키텍처

### 마이크로서비스 구성

| 서비스 | 포트 | 역할 | 상태 |
|--------|------|------|------|
| **Frontend** | 3000 | Next.js 프론트엔드 | ✅ |
| **API Gateway** | 8000 | 서비스 간 통신 관리 | ✅ |
| **Analysis Service** | 8001 | 검색어 AI 품질 평가 (Gemini) | ✅ |
| **Auction Service** | 8002 | 역경매 및 입찰 처리 | ✅ |
| **Payment Service** | 8003 | 레거시 보상 시스템 | ⚠️ Deprecated |
| **Verification Service** | 8004 | 2단계 SLA 검증 | ✅ |
| **User Service** | 8005 | 사용자 및 거래 등록 | ✅ |
| **Quality Service** | 8006 | 동적 제출 한도 | ✅ |
| **Advertiser Service** | 8007 | 광고주 및 자동입찰 | ✅ |
| **Settlement Service** | 8008 | SLA 기반 정산 | ✅ |
| **Website Analysis Service** | 8009 | 광고주 웹사이트 AI 분석 (Gemini) | ✅ |
| **PostgreSQL** | 5433 | 데이터베이스 | ✅ |

### 기술 스택

**Frontend**
- Next.js 15.4.2 (App Router), TypeScript, React 19
- Tailwind CSS 4, TanStack Query
- Lucide React, Recharts

**Backend**
- FastAPI (Python 3.11), PostgreSQL 15
- **Google Gemini (models/gemini-flash-latest)** ⭐
- AsyncPG, Pydantic, Uvicorn

**AI/ML**
- **Google Gemini API** - 검색어 상업적 가치 분석
- **Google Gemini API** - 광고주 웹사이트 자동 분석
- Playwright - 웹 스크래핑

**Infrastructure**
- Docker, Docker Compose, Terraform (AWS)

--- 

## 🎯 사용자 여정

### 👤 사용자(검색자) 여정

#### 1️⃣ 회원가입 및 로그인
```
1. 사이트 접속: http://localhost:3000
2. 회원가입: 이메일, 사용자명, 비밀번호
3. 로그인
4. 메인 페이지 이동
```

#### 2️⃣ 검색 의도 입력
```
메인 페이지 (/)
├─ 검색창에 의도 입력
│  예: "맥북 프로 M3 최저가 비교"
│
├─ 🤖 AI 자동 분석 (1초 디바운싱)
│  - 로딩 UI: "AI가 검색어 가치를 분석하고 있습니다..."
│  - 예상 소요: 5~10초
│
└─ 결과 표시
   ├─ 품질 점수: 95/100 (Grade: A)
   ├─ 상업적 가치: HIGH
   ├─ 개선 제안: 3개 항목
   ├─ AI 추천 키워드: 5개
   └─ (필요시) AI가 더 나은 검색어 추천
```

#### 3️⃣ 경매 시작
```
"List & Start Auction" 버튼 클릭
  ↓
역경매 시작 (Auction Service)
  - 광고주 키워드 매칭
  - 자동입찰 실행
  - 입찰가순 정렬
  ↓
광고 목록 표시
  - 광고주 1: ₩2,400 (평점: 4.8)
  - 광고주 2: ₩2,100 (평점: 4.5)
  - 광고주 3: ₩1,800 (평점: 4.0)
```

#### 4️⃣ 광고 클릭 및 정산
```
광고 클릭
  ↓
📊 1차 SLA 평가
  - v_atf 체크 (광고가 보였나?)
  - clicked 체크 (실제 클릭했나?)
  - ✅ 통과 → PENDING_RETURN
  ↓
🔄 광고주 사이트로 즉시 이동
  - localStorage에 {trade_id, click_time} 저장
  - 사용자는 광고주 사이트 탐색
  ↓
(사용자가 정산 확인 위해 복귀)
  ↓
📊 2차 SLA 평가 (자동)
  - 체류 시간 = 복귀 시각 - 클릭 시각
  - >= 10초 → PASSED (₩200 전액)
  - >= 5초 → PARTIAL (₩140, 70%)
  - < 5초 → PARTIAL (₩100, 50%)
  ↓
💰 자동 정산 완료
  - 잔고 업데이트
  - 대시보드에 즉시 반영
```

#### 5️⃣ 대시보드 확인
```
/dashboard 접속
├─ 오늘 수익: ₩1,240
├─ 오늘 입찰: 15건
├─ 성공률: 87%
├─ 평균 품질: 82점
└─ 거래 내역 (실시간 업데이트)
```

---

### 🏢 광고주 여정

#### 1️⃣ 회원가입 및 AI 분석
```
1. 광고주 회원가입
   - 회사명: "나이키 코리아"
   - 웹사이트: https://www.nike.com/kr/
   - 일일 예산: ₩50,000

2. AI 자동 분석 시작 (백그라운드)
   ┌─────────────────────────────────┐
   │ Website Analysis Service 실행     │
   │ 1. Playwright로 웹사이트 스크래핑│
   │ 2. Gemini AI로 키워드/카테고리 분석│
   │ 3. 소요 시간: 7~13초             │
   └─────────────────────────────────┘
   ↓
AI 분석 완료
   - 키워드 20개 추천
     ["나이키", "운동화", "스니커즈", ...]
   - 카테고리 5개 추천
     ["스포츠 용품 쇼핑몰", "러닝/운동화", ...]
   - 비즈니스 요약 생성
```

#### 2️⃣ AI 제안 검토
```
/advertiser/review-suggestions 접속
├─ AI 추천 키워드 20개 표시
│  - 수정 가능
│  - 삭제 가능
│
├─ AI 추천 카테고리 5개 표시
│  - 수정 가능
│
└─ "AI 제안 승인 및 심사 요청" 버튼 클릭
   ↓
관리자 심사 대기 (status: pending)
```

#### 3️⃣ 관리자 승인 후 대시보드
```
1. 관리자가 최종 승인
2. 상태 변경: pending → approved
3. 자동입찰 시작 가능
```

#### 4️⃣ 자동입찰 설정
```
/advertiser/auto-bidding 접속
├─ 자동입찰 ON/OFF
├─ 일일 예산: ₩50,000
├─ 최대 입찰가: ₩3,000
├─ 최소 품질 점수: 70점
└─ 설정 저장
   ↓
자동입찰 활성화
  - 매칭되는 의도에 자동 입찰
  - 예산 소진 시 자동 중지
```

#### 5️⃣ 성과 모니터링
```
/advertiser/dashboard 접속
├─ 오늘 지출: ₩32,400
├─ 오늘 클릭: 12건
├─ 전환율: 8.3% (12클릭/145노출)
├─ 평균 CPC: ₩2,700
└─ 입찰 내역 (실시간)
```

---

### 👨‍💼 관리자 여정

#### 심사 프로세스
```
1. 광고주 가입 신청 접수
   - AI 분석 결과 자동 생성
   - 키워드 20개 + 카테고리 5개

2. /admin/advertiser-review 접속
   ├─ 목록: 승인 대기 광고주 15건
   ├─ 상세 보기: 키워드, 카테고리 검토
   └─ 결정
      - 승인 → 광고주 입찰 시작 가능
      - 거절 → 승인 거부 (사유 기록)

3. 승인된 광고주 모니터링
   - 악성 키워드 감지
   - 이상 입찰 패턴 체크
```

---

## 🔄 핵심 비즈니스 플로우

### 1. 검색어 품질 평가 (AI 기반)

```
사용자 입력 (예: "나이키 에어맥스 270 블랙 구매")
  ↓
🤖 AI 분석 중 로딩 UI 표시
  "AI가 검색어 가치를 분석하고 있습니다..."
  "상업적 의도, 구체성, 구매 단계를 평가 중입니다"
  ↓
Analysis Service (Gemini API)
  - 소요 시간: 약 5~10초
  - 타임아웃: 10초 (실패 시 Legacy 사용)
  ↓
AI 분석 결과
  - 종합 점수: 0-100점
  - 상업적 의도: 0.0~1.0
  - 구체성 수준: 0.0~1.0
  - 카테고리: Shopping/Health/Finance 등
  - 구매 단계: Awareness/Consideration/Decision
  - 주된 감정: Curiosity/Urgency/Neutral 등
  - 예측 키워드: 4~5개
  ↓
실시간 표시 (디바운싱 1초)
```

**예시 결과**:
```json
{
  "score": 95,
  "commercial_intent": 1.00,
  "specificity_level": 0.95,
  "value_category": "Shopping",
  "buyer_journey_stage": "Decision",
  "primary_emotion": "Urgency",
  "predicted_keywords": [
    "나이키 에어맥스 270 최저가",
    "에어맥스 270 블랙 가격",
    "나이키 운동화 구매처"
  ]
}
```

### 2. 역경매 및 광고 매칭

```
검색어 제출
  ↓
Auction Service
  ├─ 실제 광고주 키워드 매칭
  ├─ 자동입찰 실행 (ML 기반)
  └─ 플랫폼 폴백 (구글, 네이버, 쿠팡)
  ↓
광고 목록 표시 (입찰가순)
```

### 3. 2단계 SLA 평가 및 정산 ⭐

#### 1차 평가 (광고 클릭 시)
```
광고 클릭
  ↓
v_atf, clicked 측정 (3초 내)
  ↓
부정 클릭 검증
  ├─ clicked = false → FAILED
  ├─ v_atf < 0.3 → FAILED (봇)
  └─ 정상 → PENDING_RETURN
  ↓
localStorage 저장 {trade_id, click_time}
  ↓
즉시 광고주 사이트로 리다이렉트
```

#### 2차 평가 (사용자 복귀 시)
```
광고주 사이트 탐색
  ↓
정산 확인 위해 복귀
  ↓
visibilitychange 감지
  ↓
체류 시간 = 복귀 시각 - 클릭 시각
  ↓
최종 판정
  ├─ >= 10초 → PASSED (전액 200원)
  ├─ >= 5초 → PARTIAL (부분 150원)
  └─ < 5초 → PARTIAL (부분 100원)
  ↓
Settlement Service → 잔고 업데이트
```

---

## 🤖 AI 분석 시스템 (Gemini)

### 1. Analysis Service (검색어 분석)

**목적**: 사용자 검색어의 상업적 가치를 AI로 정확하게 평가

**기술 스택**:
- Google Gemini API (`models/gemini-flash-latest`)
- 하이브리드 분석 (AI 70% + Legacy 30%)
- 타임아웃: 10초

**분석 지표**:
| 지표 | 설명 | 범위 |
|------|------|------|
| `commercial_intent` | 상업적 의도 | 0.0~1.0 |
| `specificity_level` | 검색어 구체성 | 0.0~1.0 |
| `value_category` | 카테고리 | Shopping, Travel, Finance 등 |
| `buyer_journey_stage` | 구매 단계 | Awareness, Consideration, Decision |
| `primary_emotion` | 주된 감정 | Curiosity, Urgency, Doubt 등 |
| `predicted_keywords` | 예측 키워드 | 4~5개 |

**예시**:
```python
# 입력: "맥북 프로 M3 최저가 비교"
{
  "commercial_intent": 0.98,      # 매우 높은 구매 의도
  "specificity_level": 0.92,      # 구체적인 제품명
  "value_category": "Shopping",
  "buyer_journey_stage": "Decision",  # 구매 직전 단계
  "primary_emotion": "Urgency",
  "predicted_keywords": [
    "맥북 프로 M3 가격",
    "M3 최저가 할인",
    "맥북 M3 14인치 특가"
  ]
}
# 최종 점수: 96/100
```

**성능**:
- 평균 응답 시간: **4.5~5초**
- 타임아웃 설정: **10초**
- 실패 시: Legacy 분석으로 자동 폴백 (0.1초)

**로딩 UI**:
```tsx
// 사용자에게 명확한 피드백 제공
🤖 AI가 검색어 가치를 분석하고 있습니다...
상업적 의도, 구체성, 구매 단계를 평가 중입니다 (약 5~10초 소요)
● ● ● (애니메이션)
```

### 2. Website Analysis Service (광고주 웹사이트 분석) ⭐

**목적**: 광고주 가입 시 웹사이트를 자동으로 분석하여 키워드/카테고리 추천

#### 🎯 핵심 기능

**자동 온보딩 시스템**:
```
광고주 회원가입
  ↓
웹사이트 URL + 비즈니스 정보 입력
  ↓
백그라운드에서 AI 분석 시작
  ↓
광고주는 대시보드에서 상태 확인
  ↓
분석 완료 후 제안 검토 페이지로 이동
  ↓
AI 제안 승인 또는 수정
  ↓
관리자 최종 심사 대기
```

#### 🔧 기술 스택

- **Google Gemini API** (`models/gemini-flash-latest`)
- **Playwright** - JavaScript 렌더링 + 동적 콘텐츠 스크래핑
- **BeautifulSoup4** - HTML 파싱 및 텍스트 추출
- **FastAPI** - 비동기 처리 (BackgroundTasks)

#### 📊 분석 프로세스 상세

```
1. 광고주 웹사이트 URL 입력
   예: https://www.nike.com/kr/
   
2. 상태 변경: approval_status = 'pending_analysis'

3. Playwright로 페이지 렌더링
   - 브라우저: Chromium (Headless)
   - 대기: networkidle (모든 리소스 로드 완료)
   - 타임아웃: 60초
   
4. BeautifulSoup으로 텍스트 추출
   - 불필요한 태그 제거 (script, style, nav, footer)
   - 텍스트만 추출
   - 최대 15,000자로 제한
   
5. Gemini AI 프롬프트
   """
   당신은 최고의 디지털 마케팅 전략가입니다.
   아래 웹사이트 텍스트를 분석하여:
   - business_summary: 100자 이내 비즈니스 요약
   - recommended_keywords: 최대 20개의 핵심 키워드
   - recommended_categories: 최대 5개의 카테고리
   
   JSON 형식으로만 반환하세요.
   """
   
6. Gemini 응답 파싱 및 검증
   - JSON 추출 (코드블록 제거)
   - 개수 제한 적용 (키워드 20개, 카테고리 5개)
   
7. 데이터베이스 저장
   ├─ advertiser_reviews: website_analysis 업데이트
   ├─ advertiser_keywords: 20개 삽입 (source='ai_suggested')
   └─ advertiser_categories: 5개 삽입 (source='ai_suggested')
   
8. 상태 변경: approval_status = 'pending'
```

#### 📈 실제 테스트 결과 (Nike 웹사이트)

**입력**:
```json
{
  "advertiser_id": 1,
  "url": "https://www.nike.com/kr/"
}
```

**AI 분석 결과**:
```json
{
  "business_summary": "글로벌 스포츠 브랜드 나이키의 공식 온라인 스토어",
  "recommended_keywords": [
    "나이키", "Nike", "러닝화", "운동화", "스포츠 의류",
    "축구화", "농구화", "페가수스", "보메로", "에어 포스 1",
    "에어 조던", "나이키 에어", "트레이닝복", "축구복",
    "러닝 재킷", "스포츠 신발", "나이키 공식", "한정판",
    "스니커즈", "퍼포먼스"
  ],
  "recommended_categories": [
    "스포츠 용품 쇼핑몰",
    "러닝 및 퍼포먼스 의류",
    "운동화/스니커즈",
    "피트니스 및 웰니스",
    "글로벌 스포츠 브랜드"
  ]
}
```

**데이터베이스 저장 결과**:
```sql
-- advertiser_keywords 테이블
SELECT keyword FROM advertiser_keywords 
WHERE advertiser_id = 1 AND source = 'ai_suggested';
-- 결과: 20개 키워드 저장 완료 ✅

-- advertiser_categories 테이블
SELECT category_path FROM advertiser_categories 
WHERE advertiser_id = 1 AND source = 'ai_suggested';
-- 결과: 5개 카테고리 저장 완료 ✅
```

#### ⚡ 성능 지표

| 단계 | 소요 시간 |
|------|----------|
| 웹 스크래핑 (Playwright) | 2~3초 |
| AI 분석 (Gemini) | 5~10초 |
| 데이터베이스 저장 | 0.5초 |
| **총 소요 시간** | **7~13초** |

**안정성**:
- ✅ 타임아웃 설정: 10초 (Gemini)
- ✅ 에러 처리: 실패 시 상태 복원
- ✅ 백그라운드 처리: 사용자 대기 불필요

#### 🌐 API 엔드포인트

**1. 분석 시작**
```python
POST http://localhost:8009/analyze
Content-Type: application/json

{
  "advertiser_id": 1,
  "url": "https://www.nike.com/kr/"
}

# 응답 (즉시)
{
  "message": "Analysis started in the background.",
  "advertiser_id": 1,
  "url": "https://www.nike.com/kr/"
}
```

**2. 상태 조회**
```python
GET http://localhost:8009/status/1

# 응답
{
  "advertiser_id": 1,
  "approval_status": "pending",           # pending_analysis → pending
  "review_status": "pending",
  "website_analysis": "글로벌 스포츠 브랜드...",
  "ai_suggested_keywords": 20,
  "ai_suggested_categories": 5
}
```

**3. 헬스 체크**
```python
GET http://localhost:8009/health

# 응답
{
  "status": "ok",
  "service": "website-analysis-service"
}
```

#### 🎨 프론트엔드 통합

**광고주 대시보드**:
```tsx
// 분석 상태 배너 표시
<AnalysisStatusBanner 
  status="pending_analysis"  // AI 분석 중
/>

// 완료 후 제안 검토 버튼
<Button onClick={() => router.push('/advertiser/review-suggestions')}>
  AI 제안 검토하기
</Button>
```

**제안 검토 페이지** (`/advertiser/review-suggestions`):
```tsx
// AI 추천 키워드 표시 (20개)
<KeywordList keywords={aiSuggestedKeywords} source="ai" />

// AI 추천 카테고리 표시 (5개)
<CategoryList categories={aiSuggestedCategories} source="ai" />

// 승인 버튼
<Button onClick={handleConfirm}>
  AI 제안 승인 및 심사 요청
</Button>
```

#### 🔒 보안 및 검증

**입력 검증**:
- URL 형식 검증
- advertiser_id 존재 여부 확인

**안전 설정** (Gemini):
```python
safety_settings = [
  {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, 
   "threshold": HarmBlockThreshold.BLOCK_NONE},
  {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, 
   "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
]
```

**에러 처리**:
```python
try:
    scraped_text = await scrape_website_text(url)
    if not scraped_text:
        # 스크래핑 실패 → 상태 복원
        await database.execute(
            "UPDATE advertisers SET approval_status = 'pending'"
        )
except Exception as e:
    logger.error(f"분석 중 예외 발생: {e}")
    # 에러 메시지 저장
    await database.execute(
        "UPDATE advertiser_reviews SET website_analysis = :error"
    )
```

#### 📊 데이터베이스 스키마

**advertiser_keywords** (AI 추천 키워드)
```sql
CREATE TABLE advertiser_keywords (
    id SERIAL PRIMARY KEY,
    advertiser_id INT REFERENCES advertisers(id),
    keyword VARCHAR(100),
    source VARCHAR(20),              -- 'ai_suggested' / 'manual'
    match_type VARCHAR(20),          -- 'broad' / 'exact'
    priority INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_advertiser_keywords_source 
ON advertiser_keywords(advertiser_id, source);
```

**advertiser_categories** (AI 추천 카테고리)
```sql
CREATE TABLE advertiser_categories (
    id SERIAL PRIMARY KEY,
    advertiser_id INT REFERENCES advertisers(id),
    category_path VARCHAR(200),
    source VARCHAR(20),              -- 'ai_suggested' / 'manual'
    category_level INT DEFAULT 1,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**advertiser_reviews** (AI 분석 결과)
```sql
CREATE TABLE advertiser_reviews (
    id SERIAL PRIMARY KEY,
    advertiser_id INT REFERENCES advertisers(id),
    website_analysis TEXT,           -- AI 비즈니스 요약
    review_status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 🔄 전체 플로우

```
┌─────────────────────────────────────────────────────────┐
│ 1. 광고주 회원가입                                        │
│    - 이메일, 비밀번호, 회사명, 웹사이트 URL               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Website Analysis Service (자동 실행)                  │
│    - 상태: pending_analysis                              │
│    - 백그라운드: Playwright + Gemini AI                  │
│    - 소요 시간: 7~13초                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. AI 분석 완료                                          │
│    - 키워드 20개 저장 (advertiser_keywords)              │
│    - 카테고리 5개 저장 (advertiser_categories)           │
│    - 비즈니스 요약 저장 (advertiser_reviews)             │
│    - 상태: pending                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. 광고주 제안 검토 (/advertiser/review-suggestions)     │
│    - AI 추천 키워드 20개 표시                             │
│    - AI 추천 카테고리 5개 표시                            │
│    - 수정 가능                                           │
│    - 승인 버튼 클릭                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. 관리자 심사 (/admin/advertiser-review)                │
│    - AI 분석 결과 검토                                    │
│    - 키워드/카테고리 최종 승인                            │
│    - 상태: approved / rejected                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 6. 자동입찰 시작 가능                                     │
│    - 승인된 키워드로 입찰 시작                             │
│    - Auction Service에서 매칭                            │
└─────────────────────────────────────────────────────────┘
```

#### 🎯 실제 사용 시나리오

**시나리오 1: 성공적인 온보딩**
```
1. 광고주: "나이키" 회사로 가입
2. URL: https://www.nike.com/kr/ 입력
3. AI 분석 (10초 대기)
4. 결과: 키워드 20개 + 카테고리 5개 생성
5. 광고주: AI 제안 검토 후 승인
6. 관리자: 최종 승인
7. ✅ 입찰 시작!
```

**시나리오 2: 스크래핑 실패**
```
1. 광고주: URL 입력 (잘못된 URL)
2. Playwright 접근 실패
3. 에러: "웹사이트 분석 실패: 사이트 접근 불가"
4. ⚠️ 관리자가 수동으로 키워드 입력 필요
```

**시나리오 3: AI 타임아웃**
```
1. 광고주: 복잡한 웹사이트 URL 입력
2. Gemini API 10초 초과
3. 에러: "웹사이트 분석 실패: AI 분석 오류"
4. ⚠️ 재시도 또는 수동 입력
```

#### 📝 로그 예시

**성공적인 분석**:
```
2025-10-19 10:22:45 - INFO - 🔍 [1] 웹사이트 분석 시작: https://www.nike.com/kr/
2025-10-19 10:22:55 - INFO - ✨ [1] 전체 분석 프로세스 완료
```

**실패 케이스**:
```
2025-10-19 10:22:45 - INFO - 🔍 [1] 웹사이트 분석 시작: https://invalid.com
2025-10-19 10:22:50 - ERROR - ❌ Error calling/parsing Gemini API: ...
2025-10-19 10:22:50 - ERROR - 💥 [1] 분석 중 예외 발생: ...
```

### AI 시스템 최적화

**문제 해결 과정** (2025-10-19):

1. **모델 이름 오류**
   - 문제: `gemini-1.5-pro`, `gemini-pro` → 404 에러
   - 원인: Google이 모델 네이밍 규칙 변경
   - 해결: `models/gemini-flash-latest` 사용

2. **타임아웃 최적화**
   - 초기: 4초 (너무 짧음 → AI 항상 실패)
   - 시도1: 2초 (여전히 짧음)
   - 최종: 10초 + 로딩 UI (품질 우선, UX 확보)

3. **사용자 경험 개선**
   - 문제: 사용자가 기다리는 동안 불안함
   - 해결: 명확한 로딩 메시지 + 예상 시간 표시
   - 결과: 사용자가 안심하고 기다릴 수 있음

---

## 🎯 2단계 하이브리드 SLA 시스템 (핵심)

### 왜 2단계 평가가 필요한가?

**문제점**: 광고주 사이트는 다른 도메인이라 체류 시간 직접 측정 불가 (Cross-Origin)

**해결책**: 사용자가 정산 확인을 위해 반드시 복귀한다는 점을 활용

### 구현 상세

#### 프론트엔드

**useSlaTracker.ts** - 단순화된 SLA 추적
```typescript
interface SlaMetrics {
  v_atf: number;           // 화면 표시 여부 (부정 방지)
  clicked: boolean;        // 클릭 여부 (핵심)
  t_dwell_on_ad_site: 0;   // 복귀 시 측정 (1차에서는 0)
}

// 무한 루프 수정: onComplete를 ref로 관리
const onCompleteRef = useRef(onComplete);
useEffect(() => {
  // SLA 추적
}, [tradeId]); // onComplete 제거!
```

**ReturnTracker.tsx** - 복귀 감지 컴포넌트
```typescript
useEffect(() => {
  document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible') {
      const data = localStorage.getItem('ad_return_tracker');
      if (data) {
        const {trade_id, click_time} = JSON.parse(data);
        const dwell_time = (Date.now() - click_time) / 1000;
        
        // 2차 평가 API 호출
        await fetch('/api/verify-return', {
          method: 'POST',
          body: JSON.stringify({trade_id, dwell_time})
        });
        
        localStorage.removeItem('ad_return_tracker');
      }
    }
  });
}, []);
```

#### 백엔드

**Verification Service** - 2개의 평가 엔드포인트

**1차 평가**: `/verify-delivery`
```python
# v_atf, clicked만 검증
if not clicked:
    decision = "FAILED"
elif v_atf < 0.3:
    decision = "FAILED"  # 봇
else:
    decision = "PENDING_RETURN"  # 복귀 대기
```

**2차 평가**: `/verify-return` ⭐ 신규
```python
# 체류 시간 기반 최종 판정
if dwell_time >= 10:
    decision = "PASSED"
elif dwell_time >= 5:
    decision = "PARTIAL"
else:
    decision = "PARTIAL"

# Settlement Service 호출
await call_settlement_service(trade_id, decision, dwell_time)
```

### 데이터베이스 스키마

**delivery_metrics** 테이블
```sql
trade_id VARCHAR(255) PRIMARY KEY,
v_atf FLOAT DEFAULT 0,
clicked BOOLEAN DEFAULT FALSE,        -- ⭐ 신규
t_dwell_on_ad_site FLOAT DEFAULT 0,   -- ⭐ 신규
created_at TIMESTAMP DEFAULT NOW()
```

**transactions** 테이블 상태
```sql
'PENDING_VERIFICATION'  -- 검증 대기
'PENDING_RETURN'        -- 복귀 대기 ⭐ 신규
'PASSED'                -- 전액 정산 ⭐ 신규
'PARTIAL'               -- 부분 정산 ⭐ 신규
'FAILED'                -- 정산 실패
```

---

## 🎨 주요 기능 상세

### 📱 프론트엔드 UI/UX

#### 1. 메인 페이지 (/) - Intent Exchange

**주요 컴포넌트**:

**SearchInput.tsx**
- 검색창: 의도 입력
- 디바운싱: 입력 후 1초 대기
- AI 분석 자동 시작
- AI 로딩 UI: "🤖 AI가 검색어 가치를 분석하고 있습니다..."

**QualityAdvisor.tsx** ⭐ AI 분석 결과 표시
```
┌─────────────────────────────────────┐
│ 📊 Quality Assessment              │
├─────────────────────────────────────┤
│  [원형 차트]                        │
│     95 points                       │
│     Grade: A                        │
│                                     │
│  ✓ Commercial Value: HIGH           │
│                                     │
│  💡 Improvement Suggestions:        │
│  • Include specific product name    │
│  • Add price comparison signal      │
│                                     │
│  🔖 Detected Keywords:              │
│  [나이키] [에어맥스] [운동화]        │
└─────────────────────────────────────┘
```

**AuctionStatus.tsx**
- 광고 목록
- 입찰가순 정렬
- SLA 추적 자동 시작

#### 2. How It Works 페이지 (/how-it-works) ⭐

**사용자별 맞춤 설명**:
- 로그인 유형 자동 감지 (localStorage)
- user: 수익 관점
- advertiser: 지불/환불 관점
- 비로그인: 중립 설명

**5단계 시각화**:
```
1. Listing (자동 등록)
  ↓
2. Bidding (실시간 입찰)
  ↓
3. Execution (투명 실행)
  ↓
4. Verification (2단계 SLA)
  ↓
5. Settlement (자동 정산)
```

#### 3. 사용자 대시보드 (/dashboard)

**EarningsSummary.tsx**
```
┌─────────────────────┐
│ 오늘 수익: ₩1,240   │
│ 오늘 입찰: 15건     │
│ 성공률: 87%         │
│ 평균 품질: 82점     │
│ 총 수익: ₩24,500    │
└─────────────────────┘
```

**QualityHistory.tsx**
- 품질 점수 그래프
- 기간별 트렌드

**TransactionHistory.tsx**
- 실시간 거래 내역
- 정산 상태 표시

**SubmissionLimitCard.tsx**
- 일일 제출 한도
- 남은 검색 횟수

#### 4. 광고주 대시보드 (/advertiser/dashboard)

**BiddingSummary.tsx**
```
┌─────────────────────┐
│ 총 입찰: 145건      │
│ 성공 입찰: 12건     │
│ 총 지출: ₩32,400    │
│ 평균 입찰가: ₩2,700 │
└─────────────────────┘
```

**BudgetStatus.tsx**
- 일일 예산 사용량
- 예산 소진 경고

**AnalysisStatusBanner.tsx** ⭐
- AI 분석 상태
- pending_analysis → pending → approved

**AutoBidToggle.tsx**
- 자동입찰 ON/OFF
- 실시간 활성화

#### 5. AI 제안 검토 (/advertiser/review-suggestions)

**KeywordManager.tsx**
- AI 추천 키워드 20개
- 수정/삭제 가능

**CategorySelector.tsx**
- AI 추천 카테고리 5개
- 승인 버튼

---

### 🔐 보안 및 인증

#### JWT 기반 인증
```
로그인
  ↓
JWT 토큰 발급
  - payload: {user_id, email, userType}
  - 만료: 30분
  ↓
localStorage 저장
  - token
  - userType (user/advertiser)
  ↓
모든 API 요청
  - Authorization: Bearer {token}
```

#### 사용자 유형별 접근 제어
- user: /dashboard, / (Exchange)
- advertiser: /advertiser/*
- admin: /admin/*

---

### 🎯 실시간 기능

#### WebSocket (향후 개선 예정)
- 현재: 폴링
- 계획: 실시간 알림

#### API 프록시 패턴
```
app/api/* → API Gateway → 마이크로서비스
```
- CORS 해결
- 일관된 인증
- 에러 처리 통합

---

## 🚀 빠른 시작

### Docker로 실행

```bash
# 1. 클론
git clone https://github.com/action5861/gatekeeper.git
cd gatekeeper

# 2. 환경 변수 설정
cp env.example .env
# .env 편집: JWT_SECRET_KEY, GEMINI_API_KEY 필수!

# 3. Docker Compose 실행
docker-compose up --build

# 4. 데이터베이스 마이그레이션
docker exec postgres-db psql -U admin -d search_exchange_db -c "
  ALTER TABLE delivery_metrics 
  ADD COLUMN IF NOT EXISTS clicked BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS t_dwell_on_ad_site FLOAT DEFAULT 0;
"

# 5. 접속
# http://localhost:3000 (사용자)
# http://localhost:3000/advertiser/dashboard (광고주)
# http://localhost:3000/admin/login (관리자)
```

### 필수 환경 변수

```bash
# .env 파일
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-32-chars-minimum
GEMINI_API_KEY=your_gemini_api_key_here  # ⭐ 필수!
DATABASE_URL=postgresql://admin:password@localhost:5433/search_exchange_db
```

**Gemini API 키 발급**:
1. https://aistudio.google.com/app/apikey 접속
2. "Create API Key" 클릭
3. 생성된 키를 `.env`에 추가

### 로컬 개발 (Frontend만)

```bash
npm install
npm run dev
# http://localhost:3000
```

---

## 📡 API 엔드포인트

### 사용자 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auth/register` | POST | 회원가입 |
| `/api/auth/login` | POST | 로그인 |
| `/api/evaluate-quality` | POST | 품질 평가 (AI) ⭐ |
| `/api/search` | POST | 광고 검색 |
| `/api/track-click` | POST | 광고 클릭 (거래 등록) |
| `/api/verify-delivery` | POST | 1차 SLA 평가 |
| `/api/verify-return` | POST | 2차 SLA 평가 |
| `/api/track-redirect` | GET | 리다이렉트 추적 |
| `/api/user/dashboard` | GET | 대시보드 데이터 |

### 광고주 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/advertiser/register` | POST | 광고주 가입 |
| `/api/advertiser/login` | POST | 광고주 로그인 |
| `/api/advertiser/dashboard` | GET | 대시보드 |
| `/api/advertiser/auto-bidding` | GET/PUT | 자동입찰 설정 |
| `/api/advertiser/auto-bid/optimize` | POST | 입찰 최적화 |
| `/api/advertiser/ai-suggestions` | GET | AI 웹사이트 분석 결과 ⭐ |
| `/api/advertiser/confirm-suggestions` | POST | AI 제안 승인 ⭐ |

### 관리자 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/admin/login` | POST | 관리자 로그인 |
| `/api/admin/advertiser-review` | GET | 심사 목록 |
| `/api/admin/advertiser-review/[id]` | PUT | 심사 결과 |

---

## 🧪 테스트 가이드

### AI 분석 테스트

**검색어 AI 분석**:
```bash
# 1. 사용자로 로그인
# 2. 메인 페이지에서 검색어 입력
#    예: "나이키 에어맥스 270 블랙 구매"
# 3. 로딩 UI 확인 (약 5초)
# 4. AI 분석 결과 확인
#    - 점수: 95/100
#    - 상업적 의도: 1.00
#    - 구체성: 0.95
```

**광고주 웹사이트 AI 분석**:
```bash
# 1. 광고주로 가입
# 2. 웹사이트 URL 입력 (예: https://www.nike.com/kr/)
# 3. AI 분석 대기 (약 10초)
# 4. 추천 키워드/카테고리 확인
# 5. 승인하여 키워드 등록
```

### E2E 테스트 시나리오

**시나리오 1: PASSED (전액 정산)**
```
1. 검색: "남성 청바지 추천"
2. AI 분석: 점수 75점, 상업적 의도 0.90
3. 광고 클릭 → 광고주 사이트 이동
4. 광고주 사이트에서 15초 탐색
5. 우리 사이트로 복귀
6. ✅ PASSED, 200원 전액 정산
```

**시나리오 2: PARTIAL (부분 정산)**
```
1. 검색: "겨울 코트"
2. AI 분석: 점수 80점
3. 광고 클릭 → 광고주 사이트 이동
4. 광고주 사이트에서 7초 탐색 후 복귀
5. ⚠️ PARTIAL, 150원 부분 정산
```

**시나리오 3: AI 타임아웃**
```
1. 검색: "노트북"
2. AI 분석 시도 (10초 대기)
3. AI 타임아웃 → Legacy 분석으로 폴백
4. 점수 20점 (Legacy 결과)
5. 정상 진행
```

### 자동 테스트 실행

```bash
# 전체 시스템 헬스체크
python test_health_all.py

# AI 품질 평가 테스트
python test_services.py

# 대시보드 데이터 검증
python test_dashboard_data.py

# E2E 플로우 테스트
python test_final.py
```

### 실제 작동 로그 확인

```javascript
// 기대되는 로그 (정상 작동 시)
🤖 AI가 검색어 가치를 분석하고 있습니다...
✅ AI 분석 완료: 나이키 에어맥스... (고품질 결과)
✅ [STEP 3] Click tracked: 200원 reward
💾 Saved return tracker: {trade_id: 'xxx', click_time: 1760355528028}
🖱️ Ad clicked!
👁️ Above The Fold: true
📊 SLA Metrics: {v_atf: 1, clicked: true, t_dwell_on_ad_site: 0}
✅ 1차 평가: PENDING_RETURN

// 복귀 시
👁️ [Return Tracker] Tab became visible
🔙 User returned! Dwell Time: 84.22s
✅ 2nd evaluation: PASSED
🎉 전액 정산 완료!
```

---

## 🚨 문제 해결

### AI 분석 문제

**증상**: AI 분석이 항상 실패함
```bash
# Analysis Service 로그 확인
docker logs analysis-service --tail 50

# 기대되는 로그
✓ AI 분석 완료: 나이키... (고품질 결과)

# 에러 로그
⚠ AI 타임아웃 (10초 초과) → Legacy 사용
❌ AI 분석 실패: 404 models/gemini-1.5-pro is not found
```

**해결**:
1. Gemini API 키 확인
2. 모델 이름 확인 (`models/gemini-flash-latest`)
3. 타임아웃 설정 확인 (10초)

**Website Analysis Service 문제**:
```bash
# 로그 확인
docker logs website-analysis-service --tail 50

# Gemini 설정 확인
[Gemini] KEY_SET=True, MODEL=models/gemini-flash-latest

# 재시작
docker-compose restart website-analysis-service
```

### SLA 검증 문제

```bash
# Verification Service 로그 확인
docker logs verification-service --tail 50

# API Gateway 라우팅 확인
docker logs api-gateway --tail 50

# 데이터 확인
docker exec postgres-db psql -U admin -d search_exchange_db -c "
  SELECT trade_id, clicked, t_dwell_on_ad_site, created_at 
  FROM delivery_metrics 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

### 서비스 재시작

```bash
# 특정 서비스만
docker-compose restart analysis-service
docker-compose restart website-analysis-service
docker-compose restart verification-service

# 전체 재빌드
docker-compose up --build
```

---

## 📊 데이터베이스 스키마

### 핵심 테이블

**users**
```sql
id SERIAL PRIMARY KEY,
email VARCHAR(255) UNIQUE,
username VARCHAR(50) UNIQUE,
password_hash VARCHAR(255),
total_earnings DECIMAL(10,2) DEFAULT 0,    -- Settlement Service가 업데이트
quality_score INT DEFAULT 70,
daily_limit INT DEFAULT 5
```

**search_queries** ⭐ AI 분석 데이터
```sql
id SERIAL PRIMARY KEY,
user_id INT REFERENCES users(id),
query_text VARCHAR(200),
quality_score INT,
commercial_value VARCHAR(20),               -- low/medium/high
keywords TEXT,                              -- JSON 배열
suggestions TEXT,                           -- JSON 배열
ai_analysis_data TEXT,                      -- ⭐ AI 상세 분석 (JSON)
created_at TIMESTAMP DEFAULT NOW()
```

**transactions**
```sql
id VARCHAR(255) PRIMARY KEY,               -- trade_id
user_id INT REFERENCES users(id),
search_id VARCHAR(255),
bid_id VARCHAR(255),
primary_reward DECIMAL(10,2),
status VARCHAR(50) DEFAULT 'PENDING_VERIFICATION',
created_at TIMESTAMP DEFAULT NOW()
```

**delivery_metrics**
```sql
trade_id VARCHAR(255) PRIMARY KEY,
v_atf FLOAT DEFAULT 0,
clicked BOOLEAN DEFAULT FALSE,
t_dwell_on_ad_site FLOAT DEFAULT 0,
created_at TIMESTAMP DEFAULT NOW()
```

**advertiser_keywords** ⭐ AI 추천 키워드
```sql
id SERIAL PRIMARY KEY,
advertiser_id INT REFERENCES advertisers(id),
keyword VARCHAR(100),
source VARCHAR(20),                         -- 'ai_suggested' / 'manual'
match_type VARCHAR(20),
priority INT DEFAULT 1
```

**advertiser_categories** ⭐ AI 추천 카테고리
```sql
id SERIAL PRIMARY KEY,
advertiser_id INT REFERENCES advertisers(id),
category_path VARCHAR(200),
source VARCHAR(20),                         -- 'ai_suggested' / 'manual'
category_level INT DEFAULT 1,
is_primary BOOLEAN DEFAULT FALSE
```

**advertiser_reviews** ⭐ AI 분석 결과
```sql
id SERIAL PRIMARY KEY,
advertiser_id INT REFERENCES advertisers(id),
website_analysis TEXT,                      -- AI 비즈니스 요약
review_status VARCHAR(20) DEFAULT 'pending',
admin_notes TEXT,
created_at TIMESTAMP DEFAULT NOW()
```

---

## 📈 주요 성과

### AI 분석 정확도
- **검색어 분석**: 5개 테스트 중 3개 완벽 일치 (60%)
- **웹사이트 분석**: Nike 웹사이트 20개 키워드 + 5개 카테고리 정확 생성
- **응답 시간**: 평균 4.5~5초 (안정적)

### 측정 정확도
- **이전**: t_dwell_on_ad_site = 0 (측정 실패)
- **현재**: 84.22초 (정확한 측정)

### 사용자 경험
- **이전**: 3초 카운트다운 대기
- **현재**: 즉시 광고주 사이트 이동
- **AI 분석**: 명확한 로딩 메시지로 안심 대기

### 시스템 안정성
- **이전**: 무한 루프 + Cross-origin 에러
- **현재**: 안정적 작동
- **AI 폴백**: 타임아웃 시 자동 Legacy 전환

### 광고 품질
- **이전**: 클릭하면 오히려 손해
- **현재**: 체류 시간 = 진짜 관심도

---

## 📊 개발 히스토리

### 2025-10-19: Gemini AI 최적화 및 로딩 UI 개선 ⭐

**완료된 작업**:

1. **Gemini API 연동 테스트 및 수정**
   - ✅ 모델 이름 수정: `gemini-1.5-pro` → `models/gemini-flash-latest`
   - ✅ Website Analysis Service: 광고주 웹사이트 자동 분석
   - ✅ Analysis Service: 검색어 상업적 가치 AI 분석
   - ✅ 실제 테스트: Nike 웹사이트 분석 성공

2. **타임아웃 최적화**
   - 문제: 4초 타임아웃 → AI 항상 실패 (실제 소요 4.5~5초)
   - 시도1: 2초 → 여전히 실패
   - 최종: 10초 + 로딩 UI (품질 우선, UX 확보)

3. **로딩 UI 개선**
   - 프론트엔드에 명확한 로딩 메시지 추가
   - "🤖 AI가 검색어 가치를 분석하고 있습니다..."
   - "상업적 의도, 구체성, 구매 단계를 평가 중입니다 (약 5~10초 소요)"
   - 애니메이션 점 추가

4. **테스트 결과**
   - Website Analysis: Nike → 키워드 20개 + 카테고리 5개 생성
   - Analysis Service: 5개 검색어 분석 성공
   - AI 정확도: 5개 중 3개 완벽 일치

**기술적 해결**:
- `google-generativeai` SDK 버전 호환성 해결
- 모델 네이밍 규칙 변경 대응
- 타임아웃 전략 최적화

**파일 변경**:
- `services/website-analysis-service/main.py` - 모델 이름 수정
- `services/analysis-service/ai_analyzer.py` - 모델 이름 수정
- `services/analysis-service/main.py` - 타임아웃 10초, 로그 개선
- `app/page.tsx` - 로딩 UI 개선
- `docker-compose.yml` - Gemini 설정 추가
- `README.md` - AI 분석 섹션 추가

### 2025-10-13: 2단계 하이브리드 SLA 시스템 완성

**문제 해결**:
1. ✅ 무한 루프 버그 수정 (onComplete ref 관리)
2. ✅ Cross-origin 제약 우회 (visibilitychange 활용)
3. ✅ 역설적 평가 기준 개선 (클릭 = 가치)
4. ✅ UX 개선 (즉시 리다이렉트)

**추가된 파일**:
- `app/components/ReturnTracker.tsx` - 복귀 감지
- `app/api/verify-return/route.ts` - 2차 평가 API
- `database/migration_add_clicked_to_delivery_metrics.sql`

**수정된 파일**:
- `app/lib/hooks/useSlaTracker.ts` - 단순화
- `app/layout.tsx` - ReturnTracker 추가
- `app/page.tsx` - localStorage 저장
- `app/api/track-redirect/route.ts` - 즉시 리다이렉트
- `services/verification-service/main.py` - 2단계 평가 로직
- `services/api-gateway/main.py` - 라우팅 추가

**측정 결과**:
- ✅ t_dwell_on_ad_site: 0초 → 84.22초 (성공)
- ✅ 무한 루프: 발생 → 해결
- ✅ UX: 3초 대기 → 즉시 이동

### 2025-10-12: SLA 검증 기반 정산 시스템 도입

**아키텍처 변경**:
- "클릭 즉시 정산" → "SLA 검증 후 정산"
- User Service → Settlement Service로 정산 로직 분리

**추가된 서비스**:
- Settlement Service (포트 8008)
- Verification Service 확장 (/verify-delivery)

**데이터베이스**:
- `delivery_metrics` 테이블 생성
- `settlements` 테이블 생성
- `transactions.status` 확장

### 2025-09-20: AI 품질 평가 시스템 도입

**Gemini API 연동**:
- Google Gemini 1.5 Flash 모델 (초기)
- 하이브리드 분석 (AI + 레거시)
- 실시간 품질 점수 (0-100점)

**광고주 키워드 매칭**:
- 토큰 기반 매칭 알고리즘
- 카테고리 기반 폴백
- 동적 입찰가 계산

---

## 🛠️ 프로젝트 구조

```
gatekeeper/
├── app/                                    # Next.js (App Router)
│   ├── (auth)/login, register              # 인증
│   ├── admin/                              # 관리자
│   ├── advertiser/                         # 광고주
│   │   ├── dashboard/                      # 대시보드
│   │   ├── auto-bidding/                   # 자동입찰
│   │   └── review-suggestions/             # AI 제안 검토 ⭐
│   ├── dashboard/                          # 사용자 대시보드
│   ├── api/                                # API 프록시
│   │   ├── evaluate-quality/               # AI 품질 평가 ⭐
│   │   ├── track-click/                    # 클릭 추적
│   │   ├── verify-delivery/                # 1차 SLA 평가
│   │   ├── verify-return/                  # 2차 SLA 평가
│   │   ├── track-redirect/                 # 리다이렉트
│   │   └── advertiser/
│   │       ├── ai-suggestions/             # AI 제안 조회 ⭐
│   │       └── confirm-suggestions/        # AI 제안 승인 ⭐
│   ├── components/
│   │   ├── ReturnTracker.tsx               # 복귀 감지
│   │   ├── main/
│   │   │   ├── SearchInput.tsx             # 검색 입력 (로딩 UI) ⭐
│   │   │   ├── QualityAdvisor.tsx          # AI 분석 결과 표시 ⭐
│   │   │   └── AuctionStatus.tsx
│   │   ├── dashboard/
│   │   ├── admin/
│   │   └── advertiser/
│   │       ├── AnalysisStatusBanner.tsx    # AI 분석 상태 ⭐
│   │       └── AutoBidAnalytics.tsx
│   ├── lib/
│   │   ├── hooks/
│   │   │   ├── useSlaTracker.ts            # SLA 추적
│   │   │   ├── useAnalysisStatus.ts        # AI 분석 상태 ⭐
│   │   │   ├── useDashboardData.ts
│   │   │   └── useDebounce.ts
│   │   └── auth.ts, types.ts, utils.ts
│   └── layout.tsx, page.tsx
├── services/                               # Python Microservices
│   ├── api-gateway/                        # 8000
│   ├── analysis-service/                   # 8001 (검색어 AI 분석) ⭐
│   │   ├── main.py                         # FastAPI 앱
│   │   ├── ai_analyzer.py                  # Gemini API 연동 ⭐
│   │   ├── legacy_analyzer.py              # 레거시 분석
│   │   └── requirements.txt
│   ├── auction-service/                    # 8002
│   ├── verification-service/               # 8004 (2단계 평가)
│   ├── user-service/                       # 8005
│   ├── quality-service/                    # 8006
│   ├── advertiser-service/                 # 8007
│   ├── settlement-service/                 # 8008
│   └── website-analysis-service/           # 8009 (웹사이트 AI 분석) ⭐
│       ├── main.py                         # FastAPI 앱
│       ├── database.py                     # DB 연결
│       ├── requirements.txt                # Playwright, Gemini
│       └── Dockerfile
├── database/
│   ├── init.sql
│   ├── migration_add_sla_tables.sql
│   ├── migration_add_clicked_to_delivery_metrics.sql
│   ├── migration_add_ai_analysis_data.sql  # ⭐ AI 분석 데이터
│   ├── migration_add_ai_onboarding_features.sql  # ⭐ 광고주 AI
│   └── run_*.sh, run_*.bat
└── docker-compose.yml
```

---

## 🔧 개발 환경 설정

### 환경 변수 (.env)

```bash
# JWT 보안
JWT_SECRET_KEY=your-production-secret-key-32-chars-minimum
JWT_ISSUER=digisafe-api
JWT_AUDIENCE=digisafe-client

# AI 서비스 ⭐ 필수!
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=models/gemini-flash-latest

# 데이터베이스
DATABASE_URL=postgresql://admin:password@localhost:5433/search_exchange_db

# 서비스 URL (Docker에서 자동 설정)
API_GATEWAY_URL=http://api-gateway:8000
ANALYSIS_SERVICE_URL=http://analysis-service:8001
AUCTION_SERVICE_URL=http://auction-service:8002
VERIFICATION_SERVICE_URL=http://verification-service:8004
USER_SERVICE_URL=http://user-service:8005
QUALITY_SERVICE_URL=http://quality-service:8006
ADVERTISER_SERVICE_URL=http://advertiser-service:8007
SETTLEMENT_SERVICE_URL=http://settlement-service:8003
WEBSITE_ANALYSIS_SERVICE_URL=http://website-analysis-service:8009
```

### 로컬 개발 (개별 서비스)

```bash
# Frontend
npm install
npm run dev

# Backend 서비스 (예: analysis-service)
cd services/analysis-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

### 데이터베이스 점검 SQL

운영/QA 환경에서 연결된 데이터베이스와 스키마를 빠르게 확인하려면 다음 쿼리를 실행하세요.

```sql
SELECT current_database(), current_schema();
SELECT * FROM auto_bid_settings WHERE advertiser_id = 9;
```

### 예산 설정 스모크 테스트

자동입찰 예산 플로우를 빠르게 검증하려면 루트의 `scripts/smoke_budget.sh`를 사용하세요.

```bash
TOKEN="<JWT_TOKEN>" ./scripts/smoke_budget.sh
```

환경 변수로 `API_BASE`, `AUCTION_BASE`, `ADVERTISER_ID`, `DAILY_BUDGET`, `MAX_BID_PER_KEYWORD`, `MIN_QUALITY_SCORE`를 재정의할 수 있습니다. 마지막 단계 이후에는 auction-service 로그에서 `_reserve_budget_tx` 호출 여부를 확인하세요.

---

## 📋 체크리스트

### 배포 전 확인사항

- [ ] 모든 서비스 헬스체크 통과
- [ ] 데이터베이스 마이그레이션 완료
- [ ] **환경 변수 설정 (JWT_SECRET_KEY, GEMINI_API_KEY)** ⭐ 필수
- [ ] Gemini API 연결 테스트 성공
- [ ] AI 분석 타임아웃 10초 설정
- [ ] 로딩 UI 정상 표시
- [ ] SLA 2단계 평가 정상 작동
- [ ] 광고주 키워드 매칭 확인
- [ ] 일일 제출 한도 정상 작동

### 테스트 체크리스트

- [ ] 회원가입/로그인 (사용자, 광고주, 관리자)
- [ ] **AI 품질 평가 (Gemini)** ⭐
- [ ] **AI 웹사이트 분석 (광고주)** ⭐
- [ ] 역경매 및 입찰
- [ ] 광고 클릭 → 1차 평가 → PENDING_RETURN
- [ ] 광고주 사이트 탐색 → 복귀 → 2차 평가 → PASSED
- [ ] 정산 완료 (Settlement Service)
- [ ] 대시보드 실시간 업데이트

---

## 🎯 향후 개선 방향

### 단기 (1개월)
- [ ] AI 분석 캐싱 (반복 검색어 즉시 응답)
- [ ] Gemini 2.0 Flash Lite 테스트 (더 빠른 응답)
- [ ] 복귀 시 축하 모달 표시
- [ ] 대기 중인 정산 목록 표시

### 중기 (3개월)
- [ ] ML 기반 봇 감지
- [ ] WebSocket 실시간 알림
- [ ] 광고주 성과 리포트 강화
- [ ] 모바일 반응형 개선

### 장기 (6개월)
- [ ] 광고주 Postback URL 연동
- [ ] 실제 전환(구매) 추적
- [ ] 블록체인 정산 투명성
- [ ] 다국어 AI 분석 지원

---

## 🤝 기여하기

1. Fork the Project
2. Create Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit Changes (`git commit -m 'Add NewFeature'`)
4. Push to Branch (`git push origin feature/NewFeature`)
5. Open Pull Request

---

## 📄 라이선스

MIT License

## 📞 연락처

GitHub: [https://github.com/action5861/gatekeeper](https://github.com/action5861/gatekeeper)

---

**Last Updated**: 2025-10-19  
**Major Changes**: 
- ⭐ **How It Works 페이지 개선**: 사용자/광고주별 맞춤 설명 구현
- ⭐ **프론트엔드 UI/UX 상세 설명**: 모든 페이지 컴포넌트 및 기능 문서화
- ⭐ **사용자 여정 섹션 추가**: 사용자/광고주/관리자 전체 프로세스 설명
- ⭐ Gemini AI 완전 통합 (검색어 + 웹사이트 분석)
- ⭐ AI 분석 타임아웃 최적화 (10초) + 로딩 UI 개선
- ⭐ 모델 업데이트 (models/gemini-flash-latest)
- 2단계 하이브리드 SLA 평가 모델 (광고주 사이트 체류 시간 정확 측정)
