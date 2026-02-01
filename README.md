# Intendex - Real-time Intent Exchange Platform

검색 의도를 실시간으로 거래하는 세계 최초의 인텐트 거래소

> "List what you're searching for. Advertisers bid in real-time. Get settled when SLA is verified—or they get refunded."

---

## 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [시스템 아키텍처](#️-시스템-아키텍처)
3. [사용자 여정](#-사용자-여정)
4. [핵심 비즈니스 플로우](#-핵심-비즈니스-플로우)
5. [AI 분석 시스템](#-ai-분석-시스템-gemini)
6. [2단계 하이브리드 SLA 시스템](#-2단계-하이브리드-sla-시스템-핵심)
7. [선형 보상 시스템](#-선형-보상-시스템)
8. [주요 기능 상세](#-주요-기능-상세)
9. [빠른 시작](#-빠른-시작)
10. [API 엔드포인트](#-api-엔드포인트)
11. [데이터베이스 스키마](#-데이터베이스-스키마)
12. [테스트 가이드](#-테스트-가이드)
13. [문제 해결](#-문제-해결)
14. [만 명 규모 수용 가능성](#-만-명-규모-수용-가능성-2025-02-기준)
15. [개발 히스토리](#-개발-히스토리)

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

1. **검색 의도는 자산**: 당신의 "무엇을 할려고 하는 생각이나 계획"이 실제 자산이 됩니다.
2. **AI 기반 평가**: Google Gemini가 검색어 가치를 실시간 평가
3. **선형 보상 시스템**: 체류 시간에 비례한 공정한 보상 (10초~20초 구간에서 50%~100%)
4. **자동화**: AI가 광고주 키워드를 자동 추천, 광고주는 파라미터만 설정

---

## 🏗️ 시스템 아키텍처

### 마이크로서비스 구성

| 서비스 | 포트(외부:내부) | 역할 | 상태 |
|--------|----------------|------|------|
| **Frontend** | 3000:3000 | Next.js 15 프론트엔드 | ✅ |
| **API Gateway** | 8000:8000 | 서비스 간 통신 관리 | ✅ |
| **Analysis Service** | 8001:8001 | 검색어 AI 품질 평가 (Gemini) | ✅ |
| **Auction Service** | 8002:8002 | 역경매 및 입찰 처리 | ✅ |
| **Payment Service** | 8003:8003 | 레거시 보상 시스템 | ⚠️ Deprecated |
| **Verification Service** | 8004:8004 | 2단계 SLA 검증 | ✅ |
| **User Service** | 8005:8005 | 사용자 및 거래 등록 | ✅ |
| **Quality Service** | 8006:8006 | 동적 제출 한도 | ✅ |
| **Advertiser Service** | 8007:8007 | 광고주 및 자동입찰 | ✅ |
| **Settlement Service** | 8008:8003 | SLA 기반 정산 + 출금 | ✅ |
| **Website Analysis Service** | 8009:8009 | 광고주 웹사이트 AI 분석 (Gemini) | ✅ |
| **PostgreSQL** | 5433:5432 | 데이터베이스 | ✅ |
| **pgAdmin** | 5050:80 | 데이터베이스 관리 도구 | ✅ |

### 기술 스택

**Frontend**
- Next.js 15.4.2 (App Router)
- TypeScript 5
- React 19.1.0
- Tailwind CSS 4
- TanStack Query 5.59
- Framer Motion 12.23
- Recharts 3.1
- Lucide React 0.525
- jose (JWT), zod (Validation)

**Backend**
- FastAPI (Python 3.11)
- PostgreSQL 15 (with pg_trgm extension)
- **Google Gemini (`models/gemini-flash-latest`)** ⭐
- AsyncPG, Pydantic, Uvicorn
- structlog (구조적 로깅)
- Playwright (웹 스크래핑)

**AI/ML**
- **Google Gemini API** - 검색어 상업적 가치 분석
- **Google Gemini API** - 광고주 웹사이트 자동 분석
- BeautifulSoup4 - HTML 파싱

**Infrastructure**
- Docker, Docker Compose
- Terraform (AWS)

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
  - 광고주 키워드 매칭 (pg_trgm 기반)
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
  - >= 20초 → PASSED (100%)
  - > 10초 & < 20초 → PARTIAL (선형 보상: 50%~100%)
  - <= 10초 → FAILED (0%)
  ↓
💰 자동 정산 완료
  - 잔고 업데이트
  - 대시보드에 즉시 반영
```

#### 5️⃣ 대시보드 확인 및 출금
```
/dashboard 접속
├─ 오늘 수익: ₩1,240
├─ 오늘 입찰: 15건
├─ 성공률: 87%
├─ 평균 품질: 82점
├─ 거래 내역 (실시간 업데이트)
└─ 출금 요청 (최소 10,000 Points)
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
   │ Website Analysis Service 실행   │
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
  - KST 기준 일일 경계 정책
```

#### 5️⃣ 성과 모니터링
```
/advertiser/dashboard 접속
├─ 오늘 지출: ₩32,400
├─ 오늘 클릭: 12건
├─ 전환율: 8.3% (12클릭/145노출)
├─ 평균 CPC: ₩2,700
├─ 입찰 내역 (실시간)
└─ 정산 영수증 조회 (PDF 다운로드)
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

3. /admin/advertiser-analytics 접속
   - 광고주별 성과 분석
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
  ├─ pg_trgm 기반 키워드 매칭 (유사도 검색)
  ├─ 실제 광고주 키워드 매칭
  ├─ 자동입찰 실행 (예산 예약-확정 트랜잭션)
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
최종 판정 (선형 보상 시스템)
  ├─ >= 20초 → PASSED (100%)
  ├─ > 10초 & < 20초 → PARTIAL (50%~100% 선형)
  └─ <= 10초 → FAILED (0%)
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

**저품질 검색어 개선 제안**:
- 30점 미만 또는 low 값이면 AI가 개선된 검색어 제안
- 각 제안 검색어도 Legacy 분석으로 빠르게 평가

### 2. Website Analysis Service (광고주 웹사이트 분석)

**목적**: 광고주 가입 시 웹사이트를 자동으로 분석하여 키워드/카테고리 추천

**분석 프로세스**:
```
1. 광고주 웹사이트 URL 입력
   
2. 상태 변경: approval_status = 'pending_analysis'

3. Playwright로 페이지 렌더링
   - 브라우저: Chromium (Headless)
   - 대기: networkidle → domcontentloaded → load (폴백 전략)
   - 타임아웃: 최대 60초
   
4. BeautifulSoup으로 텍스트 추출
   - 불필요한 태그 제거 (script, style, nav, footer, header)
   - 최대 15,000자로 제한
   
5. Gemini AI 분석
   - business_summary: 100자 이내 비즈니스 요약
   - recommended_keywords: 최대 20개 키워드
   - recommended_categories: 최대 5개 카테고리
   
6. 데이터베이스 저장
   - advertiser_reviews: website_analysis 업데이트
   - advertiser_keywords: 키워드 삽입 (source='ai_suggested')
   - advertiser_categories: 카테고리 삽입 (source='ai_suggested')
   
7. 상태 변경: approval_status = 'pending'
```

**성능 지표**:
| 단계 | 소요 시간 |
|------|----------|
| 웹 스크래핑 (Playwright) | 2~10초 |
| AI 분석 (Gemini) | 5~10초 |
| 데이터베이스 저장 | 0.5초 |
| **총 소요 시간** | **7~20초** |

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

**1차 평가**: `/verify-delivery`
```python
if not clicked:
    decision = "FAILED"
elif v_atf < 0.3:
    decision = "FAILED"  # 봇
else:
    decision = "PENDING_RETURN"  # 복귀 대기
```

**2차 평가**: `/verify-return`
```python
if dwell_time >= 20:
    decision = "PASSED"
elif dwell_time > 10:
    decision = "PARTIAL"
else:
    decision = "FAILED"

# Settlement Service 호출
await call_settlement_service(trade_id, decision, dwell_time)
```

---

## 📈 선형 보상 시스템

### 공식

체류 시간(10초~20초)에 비례하여 50%~100% 보상:

```
ratio = 0.5 + 0.5 * (dwell_time - 10) / (20 - 10)
payable_amount = primary_reward * ratio
```

### 예시

| 체류 시간 | 보상 비율 | 보상금액 (200원 기준) |
|----------|----------|---------------------|
| 10초 이하 | 0% | 0원 (FAILED) |
| 10초 | 50% | 100원 |
| 12초 | 60% | 120원 |
| 15초 | 75% | 150원 |
| 18초 | 90% | 180원 |
| 20초 이상 | 100% | 200원 (PASSED) |

### Settlement Service 구현

```python
if actual_dwell <= 10.0:
    ratio = 0.0  # FAILED
elif actual_dwell >= 20.0:
    ratio = 1.0  # PASSED (100%)
else:
    # 선형 보간: 10초=50%, 20초=100%
    ratio = 0.5 + 0.5 * (actual_dwell - 10.0) / (20.0 - 10.0)
    ratio = max(0.0, min(1.0, ratio))

payable_amount = float(trade["primary_reward"]) * ratio
```

---

## 🎨 주요 기능 상세

### 📱 프론트엔드 UI/UX

#### 1. 메인 페이지 (/) - Intent Exchange

**주요 컴포넌트**:

- **SearchInput.tsx**: 검색창, 디바운싱 1초, AI 분석 자동 시작
- **QualityAdvisor.tsx**: AI 분석 결과 표시 (점수, 상업적 가치, 개선 제안)
- **AuctionStatus.tsx**: 광고 목록, 입찰가순 정렬, SLA 추적 자동 시작

#### 2. 사용자 대시보드 (/dashboard)

**주요 컴포넌트**:
- **EarningsSummary.tsx**: 수익 요약
- **QualityHistory.tsx**: 품질 점수 그래프
- **TransactionHistory.tsx**: 실시간 거래 내역
- **SubmissionLimitCard.tsx**: 일일 제출 한도
- **WithdrawalModal.tsx**: 출금 요청 모달

#### 3. 광고주 대시보드 (/advertiser/dashboard)

**주요 컴포넌트**:
- **BiddingSummary.tsx**: 입찰 요약
- **BudgetStatus.tsx**: 예산 사용량
- **AnalysisStatusBanner.tsx**: AI 분석 상태
- **AutoBidToggle.tsx**: 자동입찰 ON/OFF
- **SettlementReceipt.tsx**: 정산 영수증 (PDF 다운로드)

#### 4. 자동입찰 페이지 (/advertiser/auto-bidding)

**주요 컴포넌트**:
- **AutoBidAnalytics.tsx**: 자동입찰 성능 분석
- **KeywordsCategoriesManager.tsx**: 키워드/카테고리 관리
- **BidHistory.tsx**: 입찰 내역

#### 5. How It Works 페이지 (/how-it-works)

- 로그인 유형 자동 감지 (localStorage)
- user: 수익 관점
- advertiser: 지불/환불 관점
- 비로그인: 중립 설명

---

## 🚀 빠른 시작

### Docker로 실행

```bash
# 1. 클론
git clone https://github.com/action5861/gatekeeper.git
cd gatekeeper

# 2. 환경 변수 설정
cp env.example .env
# .env 편집: GEMINI_API_KEY 필수!

# 3. Docker Compose 실행
docker-compose up --build

# 4. 데이터베이스 마이그레이션 (필요시)
docker exec postgres-db psql -U admin -d search_exchange_db -f /docker-entrypoint-initdb.d/init.sql

# 5. 접속
# http://localhost:3000 (사용자)
# http://localhost:3000/advertiser/dashboard (광고주)
# http://localhost:3000/admin/login (관리자)
# http://localhost:5050 (pgAdmin)
```

### 필수 환경 변수

```bash
# .env 파일
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-32-chars-minimum
GEMINI_API_KEY=your_gemini_api_key_here  # ⭐ 필수!
DATABASE_URL=postgresql://admin:your_secure_password_123@localhost:5433/search_exchange_db
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

### 인증 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auth/register` | POST | 회원가입 (user/advertiser) |
| `/api/auth/login` | POST | 로그인 |
| `/api/admin/login` | POST | 관리자 로그인 |

### 사용자 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/evaluate-quality` | POST | 품질 평가 (AI) ⭐ |
| `/api/search` | POST | 광고 검색 |
| `/api/track-click` | POST | 광고 클릭 (거래 등록) |
| `/api/track-redirect` | GET | 리다이렉트 추적 |
| `/api/verify-delivery` | POST | 1차 SLA 평가 |
| `/api/verify-return` | POST | 2차 SLA 평가 |
| `/api/user/dashboard` | GET | 대시보드 데이터 |
| `/api/user/quality-score` | GET | 품질 점수 조회 |
| `/api/user/submission` | GET | 제출 현황 조회 |

### 정산/출금 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/settlement/withdraw` | POST | 출금 요청 ⭐ |
| `/api/settlement/withdraw/history` | GET | 출금 내역 조회 ⭐ |

### 광고주 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/advertiser/dashboard` | GET | 대시보드 |
| `/api/advertiser/status` | GET | 상태 조회 |
| `/api/advertiser/auto-bidding` | GET/PUT | 자동입찰 설정 |
| `/api/advertiser/ai-suggestions` | GET | AI 웹사이트 분석 결과 ⭐ |
| `/api/advertiser/confirm-suggestions` | POST | AI 제안 승인 ⭐ |
| `/api/advertiser/settlement-receipt/[bidId]` | GET | 정산 영수증 조회 ⭐ |
| `/api/advertiser/bid-history` | GET | 입찰 내역 조회 |
| `/api/advertiser/keywords/[advertiserId]` | GET | 키워드 조회 |
| `/api/advertiser/categories/[advertiserId]` | GET | 카테고리 조회 |
| `/api/advertiser/analytics/auto-bidding` | GET | 자동입찰 분석 데이터 |

### 관리자 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/admin/advertiser-review` | GET | 심사 목록 |
| `/api/admin/advertiser-review/[id]` | PUT | 심사 결과 |
| `/api/admin/advertiser-analytics` | GET | 광고주 분석 |

### 경매 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auction/[searchId]` | GET | 경매 상태 조회 |
| `/api/auction/select` | POST | 입찰 선택 |
| `/api/auction/bid/[bidId]` | GET | 입찰 정보 조회 |

---

## 📊 데이터베이스 스키마

### 핵심 테이블

#### users
```sql
id SERIAL PRIMARY KEY,
username VARCHAR(50) UNIQUE NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
hashed_password VARCHAR(255) NOT NULL,
total_earnings DECIMAL(10,2) DEFAULT 0.00,
quality_score INTEGER DEFAULT 50,
submission_count INTEGER DEFAULT 0,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### advertisers
```sql
id SERIAL PRIMARY KEY,
username VARCHAR(50) UNIQUE NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
hashed_password VARCHAR(255) NOT NULL,
company_name VARCHAR(100) NOT NULL,
website_url VARCHAR(255),
daily_budget DECIMAL(10,2) DEFAULT 10000.00,
approval_status VARCHAR(20) DEFAULT 'pending',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### transactions
```sql
id VARCHAR(100) PRIMARY KEY,
user_id INTEGER REFERENCES users(id),
auction_id INTEGER REFERENCES auctions(id),
bid_id VARCHAR(100),
advertiser_id INTEGER REFERENCES advertisers(id),
query_text VARCHAR(500) NOT NULL,
buyer_name VARCHAR(100) NOT NULL,
primary_reward DECIMAL(10,2) NOT NULL,
secondary_reward DECIMAL(10,2),
settlement_decision VARCHAR(50),
amount DECIMAL(10,2),
source VARCHAR(20) DEFAULT 'ADVERTISER',
status VARCHAR(20) DEFAULT '1차 완료',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### delivery_metrics (SLA 지표)
```sql
id SERIAL PRIMARY KEY,
trade_id VARCHAR(255) UNIQUE NOT NULL,
v_atf FLOAT,
clicked BOOLEAN DEFAULT FALSE,
t_dwell_on_ad_site FLOAT DEFAULT 0,
created_at TIMESTAMPTZ DEFAULT NOW()
```

#### settlements (정산 결과)
```sql
id SERIAL PRIMARY KEY,
trade_id VARCHAR(255) NOT NULL,
verification_decision VARCHAR(50) NOT NULL,
payable_amount NUMERIC(10,2) NOT NULL,
dwell_time NUMERIC,
created_at TIMESTAMPTZ DEFAULT NOW()
```

#### withdrawal_requests (출금 요청)
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
user_id INTEGER REFERENCES users(id),
request_amount INTEGER NOT NULL,
tax_amount INTEGER NOT NULL,
final_amount INTEGER NOT NULL,
bank_name VARCHAR(100) NOT NULL,
account_number VARCHAR(100) NOT NULL,
account_holder VARCHAR(100) NOT NULL,
status VARCHAR(20) DEFAULT 'REQUESTED',
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
```

#### advertiser_keywords (AI 추천 키워드)
```sql
id SERIAL PRIMARY KEY,
advertiser_id INTEGER REFERENCES advertisers(id),
keyword VARCHAR(100) NOT NULL,
source VARCHAR(20),  -- 'ai_suggested' / 'manual'
match_type VARCHAR(20) DEFAULT 'broad',
priority INTEGER DEFAULT 1,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### advertiser_categories (AI 추천 카테고리)
```sql
id SERIAL PRIMARY KEY,
advertiser_id INTEGER REFERENCES advertisers(id),
category_path VARCHAR(200) NOT NULL,
source VARCHAR(20),  -- 'ai_suggested' / 'manual'
category_level INTEGER NOT NULL,
is_primary BOOLEAN DEFAULT FALSE,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### auto_bid_settings (자동입찰 설정)
```sql
id SERIAL PRIMARY KEY,
advertiser_id INTEGER REFERENCES advertisers(id) UNIQUE,
is_enabled BOOLEAN DEFAULT FALSE,
daily_budget DECIMAL(10,2) DEFAULT 10000.00,
max_bid_per_keyword INTEGER DEFAULT 3000,
min_quality_score INTEGER DEFAULT 50,
preferred_categories JSONB,
excluded_keywords TEXT[],
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### advertiser_daily_spend (일일 예산 추적)
```sql
advertiser_id INT,
spend_date DATE,
amount BIGINT,
PRIMARY KEY(advertiser_id, spend_date)
```

### 성능 최적화 인덱스

```sql
-- pg_trgm 확장 (유사도 검색)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN 인덱스 (키워드 유사도 검색)
CREATE INDEX idx_adv_kw_trgm ON advertiser_keywords 
USING gin (lower(keyword) gin_trgm_ops);

-- 표현식 인덱스 (정확 매칭)
CREATE INDEX idx_adv_kw_exact_expr ON advertiser_keywords 
((lower(replace(keyword, ' ', ''))));

-- 카테고리 검색 인덱스
CREATE INDEX idx_cat_name_trgm ON business_categories 
USING gin (lower(name) gin_trgm_ops);
```

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
4. 광고주 사이트에서 25초 탐색
5. 우리 사이트로 복귀
6. ✅ PASSED, 200원 전액 정산
```

**시나리오 2: PARTIAL (부분 정산 - 선형)**
```
1. 검색: "겨울 코트"
2. AI 분석: 점수 80점
3. 광고 클릭 → 광고주 사이트 이동
4. 광고주 사이트에서 15초 탐색 후 복귀
5. ⚠️ PARTIAL, 150원 부분 정산 (75%)
```

**시나리오 3: FAILED**
```
1. 검색: "노트북"
2. 광고 클릭 → 광고주 사이트 이동
3. 8초 후 즉시 복귀
4. ❌ FAILED, 0원 (10초 미만)
```

### 자동 테스트 실행

```bash
# 전체 시스템 헬스체크
python test_health_all.py

# AI 품질 평가 테스트
python test_services.py

# 선형 보상 시스템 테스트
python test_linear_reward.py
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

# Settlement Service 로그 확인
docker logs settlement-service --tail 50

# 데이터 확인
docker exec postgres-db psql -U admin -d search_exchange_db -c "
  SELECT trade_id, clicked, t_dwell_on_ad_site, created_at 
  FROM delivery_metrics 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

### 레이트리밋 문제

Auction Service는 10초당 최대 3회 요청 제한이 있습니다.
```
429 Too Many Requests
```

### 서비스 재시작

```bash
# 특정 서비스만
docker-compose restart analysis-service
docker-compose restart website-analysis-service
docker-compose restart verification-service
docker-compose restart settlement-service

# 전체 재빌드
docker-compose up --build
```

### 데이터베이스 점검

```sql
-- 연결 확인
SELECT current_database(), current_schema();

-- 자동입찰 설정 확인
SELECT * FROM auto_bid_settings WHERE advertiser_id = 9;

-- 정산 내역 확인
SELECT * FROM settlements ORDER BY created_at DESC LIMIT 10;
```

---

## 📈 주요 성과

### AI 분석 정확도
- **검색어 분석**: 5개 테스트 중 3개 완벽 일치 (60%)
- **웹사이트 분석**: Nike 웹사이트 20개 키워드 + 5개 카테고리 정확 생성
- **응답 시간**: 평균 4.5~5초 (안정적)

### Auction Service 성능
- **N+1 쿼리 문제**: 완전 해결 ✅
- **쿼리 성능**: 2.5초 → 0.3초 (8.3배 향상) ✅
- **데이터베이스 호출**: 15-20회 → 3-4회 (5배 감소) ✅
- **메모리 사용량**: 40% 감소 ✅
- **매칭 정확도**: 95% → 98% 향상 ✅

### 측정 정확도
- **이전**: t_dwell_on_ad_site = 0 (측정 실패)
- **현재**: 정확한 체류 시간 측정 (84.22초 등)

### 사용자 경험
- **이전**: 3초 카운트다운 대기
- **현재**: 즉시 광고주 사이트 이동
- **AI 분석**: 명확한 로딩 메시지로 안심 대기

### 시스템 안정성
- **이전**: 무한 루프 + Cross-origin 에러
- **현재**: 안정적 작동
- **AI 폴백**: 타임아웃 시 자동 Legacy 전환

---

## 📐 만 명 규모 수용 가능성 (2025-02 기준)

전체 코드베이스 기준으로 **약 1만 명 유저** 수준에서의 수용 가능성을 정리한 내용입니다.

### ✅ 현재 잘 맞춰진 부분

| 항목 | 설정 | 1만 명 관점 |
|------|------|-------------|
| **DB 연결 풀** | 8개 서비스 × `pool_size=5`, `max_overflow=10` | 기본 40연결, 피크 시 서비스당 최대 15 → **총 120연결 가능** |
| **Redis 캐싱** | Analysis(검색어), Website Analysis(URL) | 동일 검색어/URL 재요청 시 Gemini 생략 → 비용·지연 감소 |
| **일일 제출 한도** | 사용자당 5~15회/일 (품질 점수별) | 1만 명 × 15 = 15만 회/일 수준까지 제어 가능 |
| **경매 레이트리밋** | IP+쿼리당 10초에 3회 | 동일 검색어 스팸 방지, 정상 사용에는 여유 |
| **품질 평가 레이트리밋** | IP당 분당 100회 (프론트) | IP 단위 과부하 방지 |
| **Auction Gemini** | Semaphore(3) | 동시 3건으로 API 호출 제한 |
| **Website Analysis** | Semaphore(2) + 60초 타임아웃 | 동시 브라우저 2개, 무한 대기 방지 |

### ⚠️ 반드시 조정해야 할 부분

1. **PostgreSQL `max_connections`**
   - 기본값 **100**인데, 피크 시 8서비스 × 15 = **120** 연결 가능 → **100 초과 위험**.
   - **조치**: PostgreSQL 설정에서 `max_connections`를 **150 이상**으로 올리거나, `pool_size`/`max_overflow`를 줄여 합이 100 이하가 되도록 조정.

2. **서비스 단일 인스턴스**
   - API Gateway, Analysis, Auction, User 등 **모두 단일 프로세스**.
   - 1만 명 동시 접속·요청이 몰리면 한 서비스가 병목이 될 수 있음.
   - **조치**: 트래픽이 많은 서비스(API Gateway, Analysis, Auction 등)부터 **수평 확장(인스턴스 2대 이상)** 검토.

### 📊 부하 가정과 영향

- **일일 제출**: 1만 명 × 평균 10회 ≈ 10만 건/일 → 초당 평균 ~1.2건. 피크 10~50건/초 가정 시에도 DB 풀(5+10)로 처리 가능.
- **검색어 품질 평가**: Redis로 동일 검색어 반복 시 Gemini 호출 감소. 신규 검색어만 Gemini 호출 → 캐시 히트율이 높을수록 1만 명도 수용 가능.
- **광고주 웹사이트 분석**: 동시 2건만 실행. 1만 명 중 동시에 “분석 요청”하는 수가 적으면 문제 없고, 많으면 대기열(`/queue-status`)로 상태 확인 가능.

### 결론

- **DB `max_connections`만 150 이상(또는 풀 합 100 이하)으로 맞추면**, 나머지 현재 설계만으로도 **1만 명 규모는 “목표로 둘 만한” 수준**입니다.
- 다만 **동시 접속·요청이 매우 몰리는 피크**를 상정하면, **PostgreSQL 조정 + 주요 서비스 수평 확장**을 하면 더 안전합니다.
- **Gemini API 할당량**(분당/일당 요청 제한)은 Google 쿼터를 확인하고, Redis 캐시 히트율을 높이는 것이 1만 명 수용에 유리합니다.

---

## 📊 개발 히스토리

### 2026-02-01: Redis 캐싱, Website Analysis 최적화, DB Pool ⭐

**완료된 작업**:
1. **Redis 도입 (Analysis Service)**
   - ✅ 동일 검색어 AI 분석 결과 캐싱 (TTL 24시간)
   - ✅ Cache Hit 시 Gemini 호출 생략 → 속도·비용 절감
   - ✅ Redis 미연결 시 기존 Gemini Fallback 유지

2. **Website Analysis Service**
   - ✅ Redis 캐싱 (URL 기반, Cache First / Lock Later)
   - ✅ Semaphore로 동시 브라우저 분석 최대 2개 제한
   - ✅ `GET /queue-status` 대기열 상태 API 추가
   - ✅ 분석 타임아웃 60초 (`asyncio.wait_for`) 적용
   - ✅ 캐시 모듈명 `redis_cache.py`로 통일 (pyright 호환)

3. **DB 연결 풀 최적화 (8개 마이크로서비스)**
   - ✅ `pool_size=5`, `max_overflow=10`, `pool_recycle=1800` 적용
   - ✅ 8서비스 × 5 = 40연결 기본, 피크 시 +10까지 (DB 한도 100 이내)

4. **기타**
   - ✅ Analysis Service: Cache Miss 시 `📤 Cache Miss → Gemini API 호출` 로그 추가

### 2025-01-23: 출금 기능 및 정산 영수증 추가 ⭐

**완료된 작업**:
1. **출금 요청 기능**
   - ✅ `withdrawal_requests` 테이블 생성
   - ✅ 최소 출금 금액: 10,000 Points
   - ✅ 원자적 트랜잭션으로 잔고 차감 및 요청 기록
   - ✅ 출금 내역 조회 API

2. **정산 영수증 기능**
   - ✅ PDF 다운로드 지원
   - ✅ 정산 상세 정보 표시
   - ✅ 광고주용 영수증 생성

### 2025-01-XX: Auction Service 성능 최적화 ⭐

**완료된 작업**:
1. **N+1 쿼리 문제 완전 해결**
   - ✅ 배치 쿼리로 전환
   - ✅ 데이터베이스 호출 5배 감소
   - ✅ 쿼리 성능 8.3배 향상

2. **예산 관리 개선**
   - ✅ 예산 예약-확정 트랜잭션 통합
   - ✅ KST 기준 일일 경계 정책
   - ✅ 예산 누수 방지

3. **로깅 및 보안 강화**
   - ✅ 구조적 로깅 전환 (structlog)
   - ✅ 레이트리밋 추가 (10초에 최대 3회)
   - ✅ PostgreSQL pg_trgm 인덱스 최적화

### 2025-10-19: Gemini AI 최적화 및 로딩 UI 개선 ⭐

**완료된 작업**:
1. **Gemini API 연동**
   - ✅ 모델 이름 수정: `gemini-1.5-pro` → `models/gemini-flash-latest`
   - ✅ Website Analysis Service: 광고주 웹사이트 자동 분석
   - ✅ Analysis Service: 검색어 상업적 가치 AI 분석

2. **타임아웃 최적화**
   - 최종: 10초 + 로딩 UI (품질 우선, UX 확보)

3. **로딩 UI 개선**
   - 명확한 로딩 메시지 + 예상 시간 표시

### 2025-10-13: 2단계 하이브리드 SLA 시스템 완성

**문제 해결**:
1. ✅ 무한 루프 버그 수정 (onComplete ref 관리)
2. ✅ Cross-origin 제약 우회 (visibilitychange 활용)
3. ✅ 역설적 평가 기준 개선 (클릭 = 가치)
4. ✅ UX 개선 (즉시 리다이렉트)

### 2025-10-12: SLA 검증 기반 정산 시스템 도입

**아키텍처 변경**:
- "클릭 즉시 정산" → "SLA 검증 후 정산"
- User Service → Settlement Service로 정산 로직 분리
- 선형 보상 시스템 도입

---

## 🛠️ 프로젝트 구조

```
gatekeeper/
├── app/                                    # Next.js (App Router)
│   ├── (auth)/login, register              # 인증 페이지
│   ├── admin/                              # 관리자 페이지
│   │   ├── advertiser-analytics/           # 광고주 분석
│   │   ├── advertiser-review/              # 광고주 심사
│   │   └── login/                          # 관리자 로그인
│   ├── advertiser/                         # 광고주 페이지
│   │   ├── dashboard/                      # 대시보드
│   │   ├── auto-bidding/                   # 자동입찰
│   │   └── review-suggestions/             # AI 제안 검토
│   ├── dashboard/                          # 사용자 대시보드
│   ├── how-it-works/                       # 서비스 설명
│   ├── api/                                # API 프록시
│   │   ├── auth/                           # 인증 API
│   │   ├── advertiser/                     # 광고주 API
│   │   ├── admin/                          # 관리자 API
│   │   ├── auction/                        # 경매 API
│   │   ├── settlement/                     # 정산 API
│   │   │   └── withdraw/                   # 출금 API
│   │   ├── evaluate-quality/               # AI 품질 평가
│   │   ├── verify-delivery/                # 1차 SLA 평가
│   │   ├── verify-return/                  # 2차 SLA 평가
│   │   └── track-*/                        # 추적 API
│   ├── components/
│   │   ├── ReturnTracker.tsx               # 복귀 감지
│   │   ├── main/                           # 메인 페이지 컴포넌트
│   │   ├── dashboard/                      # 대시보드 컴포넌트
│   │   ├── advertiser/                     # 광고주 컴포넌트
│   │   ├── admin/                          # 관리자 컴포넌트
│   │   └── ui/                             # 공통 UI 컴포넌트
│   ├── lib/
│   │   ├── hooks/                          # 커스텀 훅
│   │   │   ├── useSlaTracker.ts            # SLA 추적
│   │   │   ├── useAnalysisStatus.ts        # AI 분석 상태
│   │   │   └── useDashboardData.ts         # 대시보드 데이터
│   │   ├── api/                            # API 유틸리티
│   │   └── types.ts, utils.ts, auth.ts     # 타입, 유틸, 인증
│   └── layout.tsx, page.tsx                # 루트 레이아웃
├── services/                               # Python Microservices
│   ├── api-gateway/                        # 8000
│   ├── analysis-service/                   # 8001 (검색어 AI 분석)
│   │   ├── main.py                         # FastAPI 앱
│   │   ├── ai_analyzer.py                  # Gemini API 연동
│   │   └── legacy_analyzer.py              # 레거시 분석
│   ├── auction_service/                    # 8002
│   │   ├── main.py                         # 경매 로직
│   │   ├── database.py                     # DB 연결
│   │   └── utils/sign.py                   # HMAC 서명
│   ├── verification-service/               # 8004 (2단계 평가)
│   ├── user-service/                       # 8005
│   ├── quality-service/                    # 8006
│   ├── advertiser-service/                 # 8007
│   │   ├── main.py                         # 광고주 로직
│   │   └── auto_bid_optimizer.py           # 자동입찰 최적화
│   ├── settlement-service/                 # 8008 (정산 + 출금)
│   ├── website-analysis-service/           # 8009 (웹사이트 AI 분석)
│   │   ├── main.py                         # Playwright + Gemini
│   │   └── database.py                     # DB 연결
│   └── shared/                             # 공유 모듈
│       └── limit_policy.py                 # 제출 한도 정책
├── database/
│   ├── init.sql                            # 초기 스키마
│   ├── migration_add_sla_tables.sql        # SLA 테이블
│   ├── migration_add_clicked_to_delivery_metrics.sql
│   ├── migration_add_ai_onboarding_features.sql
│   ├── migration_add_withdrawal_requests.sql
│   ├── migration_optimize_auction_performance.sql
│   └── run_*.sh, run_*.bat                 # 마이그레이션 스크립트
├── docker-compose.yml                      # 서비스 구성
├── Dockerfile                              # 프론트엔드 빌드
├── package.json                            # NPM 의존성
├── env.example                             # 환경변수 예시
└── terraform/                              # AWS 인프라
    ├── main.tf
    └── variables.tf
```

---

## 🔧 개발 환경 설정

### 환경 변수 (.env)

```bash
# JWT 보안
JWT_SECRET_KEY=your-production-secret-key-32-chars-minimum
JWT_ALG=HS256
JWT_ISSUER=digisafe-api
JWT_AUDIENCE=digisafe-client
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI 서비스 ⭐ 필수!
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=models/gemini-flash-latest

# 데이터베이스
DATABASE_URL=postgresql://admin:your_secure_password_123@localhost:5433/search_exchange_db

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

### 예산 설정 스모크 테스트

```bash
TOKEN="<JWT_TOKEN>" ./scripts/smoke_budget.sh
```

---

## 📋 체크리스트

### 배포 전 확인사항

- [ ] 모든 서비스 헬스체크 통과
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 환경 변수 설정 (JWT_SECRET_KEY, GEMINI_API_KEY)
- [ ] Gemini API 연결 테스트 성공
- [ ] AI 분석 타임아웃 10초 설정
- [ ] 선형 보상 시스템 정상 작동
- [ ] 출금 기능 정상 작동

### 테스트 체크리스트

- [ ] 회원가입/로그인 (사용자, 광고주, 관리자)
- [ ] AI 품질 평가 (Gemini)
- [ ] AI 웹사이트 분석 (광고주)
- [ ] 역경매 및 입찰
- [ ] 광고 클릭 → 1차 평가 → PENDING_RETURN
- [ ] 광고주 사이트 탐색 → 복귀 → 2차 평가 → PASSED/PARTIAL
- [ ] 선형 보상 정산 완료
- [ ] 출금 요청 및 내역 조회
- [ ] 대시보드 실시간 업데이트

---

## 🎯 향후 개선 방향

### 단기 (1개월)
- [ ] AI 분석 캐싱 (반복 검색어 즉시 응답)
- [ ] Gemini 2.0 Flash Lite 테스트
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

**Last Updated**: 2025-11-29
**Version**: 2.0.0

**Major Features**:
- ⭐ **선형 보상 시스템**: 체류 시간에 비례한 공정한 보상 (10초~20초: 50%~100%)
- ⭐ **출금 기능**: 최소 10,000 Points 출금 요청 및 내역 조회
- ⭐ **정산 영수증**: PDF 다운로드 지원
- ⭐ **Auction Service 성능 최적화**: N+1 쿼리 해결, 8.3배 성능 향상
- ⭐ **예산 관리 개선**: KST 기준 일일 경계, 원자적 트랜잭션 처리
- ⭐ **보안 강화**: 레이트리밋 추가, 구조적 로깅 전환
- ⭐ **Gemini AI 완전 통합**: 검색어 + 웹사이트 분석
- ⭐ **2단계 하이브리드 SLA**: 광고주 사이트 체류 시간 정확 측정
