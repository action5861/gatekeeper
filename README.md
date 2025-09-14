
## 🏗️ 아키텍처

이 프로젝트는 **마이크로서비스 아키텍처(MSA)**로 설계되었습니다.

### 서비스 구성

| 서비스 | 포트 | 역할 | 기술 스택 |
|--------|------|------|-----------|
| **Frontend** | 3000 | Next.js 프론트엔드 | Next.js 14, TypeScript, React 18 |
| **API Gateway** | 8000 | 서비스 간 통신 관리 | FastAPI, Python |
| **Analysis Service** | 8001 | 데이터 가치 평가 및 품질 분석 | FastAPI, Python |
| **Auction Service** | 8002 | 역경매 생성 및 입찰 처리 | FastAPI, Python |
| **Payment Service** | 8003 | 보상 지급 및 거래 내역 | FastAPI, Python |
| **Verification Service** | 8004 | 2차 보상 검증 | FastAPI, Python |
| **User Service** | 8005 | 사용자 데이터 관리 | FastAPI, Python |
| **Quality Service** | 8006 | 동적 제출 한도 관리 | FastAPI, Python |
| **Advertiser Service** | 8007 | 광고주 관리 및 자동입찰 | FastAPI, Python |
| **Database** | 5433 | PostgreSQL 데이터베이스 | PostgreSQL 15 |

### API Gateway 및 라우팅

#### Next.js API Routes (프론트엔드 프록시)
- `/api/search` → Analysis Service + Auction Service
- `/api/auction/*` → Auction Service
- `/api/auth/*` → User Service (인증)
- `/api/user/*` → User Service (사용자 데이터)
- `/api/advertiser/*` → Advertiser Service
- `/api/admin/*` → Advertiser Service (관리자 기능)
- `/api/track-click` → 클릭 추적 및 보상 지급
- `/api/evaluate-quality` → 품질 평가
- `/api/verify` → Verification Service

#### Python API Gateway (포트 8000)
- 모든 마이크로서비스 간 통신을 중앙에서 관리
- JWT 토큰 검증 및 라우팅
- 로드 밸런싱 및 에러 처리

## 🚀 빠른 시작

### 로컬 개발 환경

1. **저장소 클론**
   ```bash
   git clone https://github.com/action5861/gatekeeper.git
   cd gatekeeper
   ```

2. **Docker Compose로 모든 서비스 실행**
   ```bash
   docker-compose up --build
   ```

3. **개별 서비스 실행 (선택사항)**
   ```bash
   # Frontend만 실행
   npm run dev
   
   # 개별 마이크로서비스 실행
   cd services/analysis-service && python main.py
   cd services/auction-service && python main.py
   # ... 기타 서비스들
   ```

### 프로덕션 배포

1. **Terraform으로 AWS 인프라 배포**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # terraform.tfvars 파일에서 VPC ID와 서브넷 ID 설정
   terraform init
   terraform plan
   terraform apply
   ```

2. **환경 변수 설정**
   ```bash
   export ANALYSIS_SERVICE_URL=http://your-alb-dns:8001
   export AUCTION_SERVICE_URL=http://your-alb-dns:8002
   export PAYMENT_SERVICE_URL=http://your-alb-dns:8003
   export VERIFICATION_SERVICE_URL=http://your-alb-dns:8004
   export USER_SERVICE_URL=http://your-alb-dns:8005
   export QUALITY_SERVICE_URL=http://your-alb-dns:8006
   export ADVERTISER_SERVICE_URL=http://your-alb-dns:8007
   ```

## 📁 프로젝트 구조

```
gatekeeper/
├── app/                          # Next.js 프론트엔드 (App Router)
│   ├── (auth)/                   # 인증 관련 페이지 그룹
│   │   ├── login/page.tsx        # 로그인 페이지
│   │   └── register/page.tsx     # 회원가입 페이지
│   ├── admin/                    # 관리자 페이지
│   │   ├── login/page.tsx        # 관리자 로그인
│   │   └── advertiser-review/page.tsx # 광고주 심사 관리
│   ├── advertiser/               # 광고주 페이지
│   │   ├── dashboard/page.tsx    # 광고주 대시보드
│   │   └── auto-bidding/page.tsx # 자동입찰 관리
│   ├── api/                      # API 프록시 엔드포인트
│   │   ├── admin/                # 관리자 API
│   │   │   ├── login/route.ts    # 관리자 로그인 API
│   │   │   └── advertiser-review/ # 광고주 심사 API
│   │   ├── advertiser/           # 광고주 API
│   │   │   ├── dashboard/        # 광고주 대시보드 API
│   │   │   ├── auto-bid/         # 자동입찰 API
│   │   │   ├── bid-history/      # 입찰 이력 API
│   │   │   └── review-status/    # 심사 상태 API
│   │   ├── auction/              # 경매 API
│   │   │   ├── [searchId]/       # 검색별 경매 API
│   │   │   └── select/           # 입찰 선택 API
│   │   ├── auth/                 # 인증 API
│   │   │   ├── login/route.ts    # 로그인 API
│   │   │   └── register/route.ts # 회원가입 API
│   │   ├── click/                # 클릭 추적 API
│   │   │   ├── [searchId]/[bidId]/ # 검색별 클릭 통계
│   │   │   └── route.ts          # 클릭 API
│   │   ├── track-click/route.ts  # 클릭 추적 및 보상 지급
│   │   ├── evaluate-quality/route.ts # 품질 평가 API
│   │   ├── search/route.ts       # 검색 API
│   │   ├── user/                 # 사용자 API
│   │   │   ├── dashboard/        # 사용자 대시보드 API
│   │   │   ├── quality-score/    # 품질 점수 API
│   │   │   └── submission/       # 제출 관리 API
│   │   └── verify/route.ts       # 검증 API
│   ├── components/               # React 컴포넌트
│   │   ├── admin/                # 관리자 컴포넌트
│   │   │   ├── AdvertiserReviewCard.tsx
│   │   │   ├── KeywordEditor.tsx
│   │   │   └── CategorySelector.tsx
│   │   ├── advertiser/           # 광고주 컴포넌트
│   │   │   ├── AutoBidAnalytics.tsx
│   │   │   ├── BidHistory.tsx
│   │   │   └── KeywordManager.tsx
│   │   ├── dashboard/            # 대시보드 컴포넌트
│   │   │   ├── EarningsSummary.tsx
│   │   │   ├── QualityHistory.tsx
│   │   │   ├── SubmissionLimitCard.tsx
│   │   │   └── TransactionHistory.tsx
│   │   ├── main/                 # 메인 페이지 컴포넌트
│   │   │   ├── SearchInput.tsx
│   │   │   ├── AuctionStatus.tsx
│   │   │   └── QualityAdvisor.tsx
│   │   ├── ui/                   # 공통 UI 컴포넌트
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ErrorFallback.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   └── RewardModal.tsx
│   │   ├── AuthForm.tsx          # 인증 폼 컴포넌트
│   │   └── Header.tsx            # 헤더 컴포넌트
│   ├── dashboard/page.tsx        # 사용자 대시보드 페이지
│   ├── lib/                      # 공통 라이브러리
│   │   ├── hooks/                # 커스텀 훅
│   │   │   ├── useDashboardData.ts
│   │   │   └── useDebounce.ts
│   │   ├── utils/                # 유틸리티
│   │   │   └── errorMonitor.ts
│   │   ├── actions.ts            # 서버 액션
│   │   ├── admin-auth.ts         # 관리자 인증
│   │   ├── auth.ts               # 사용자 인증
│   │   ├── database.ts           # 데이터베이스 연결
│   │   ├── types.ts              # 타입 정의
│   │   └── utils.ts              # 공통 유틸리티
│   ├── providers.tsx             # React Query Provider
│   ├── layout.tsx                # 전역 레이아웃
│   └── page.tsx                  # 메인 페이지
├── services/                     # 마이크로서비스 (Python FastAPI)
│   ├── api-gateway/              # API 게이트웨이
│   │   ├── main.py               # 게이트웨이 메인
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── analysis-service/         # 데이터 분석 서비스 (포트 8001)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── auction-service/          # 경매 서비스 (포트 8002)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── utils/                # 유틸리티 모듈
│   │   │   ├── sign.py
│   │   │   └── __init__.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── payment-service/          # 결제 서비스 (포트 8003)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── verification-service/     # 검증 서비스 (포트 8004)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── utils/                # 유틸리티 모듈
│   │   │   ├── sign.py
│   │   │   └── __init__.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── user-service/             # 사용자 서비스 (포트 8005)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── update_passwords.py   # 비밀번호 업데이트 스크립트
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── quality-service/          # 품질 관리 서비스 (포트 8006)
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── advertiser-service/       # 광고주 서비스 (포트 8007)
│       ├── main.py
│       ├── database.py
│       ├── auto_bid_optimizer.py # 자동입찰 최적화 모듈
│       ├── Dockerfile
│       └── requirements.txt
├── database/                     # 데이터베이스 스키마 및 마이그레이션
│   ├── init.sql                  # 초기 데이터베이스 설정
│   ├── migration_add_transaction_columns.sql      # 트랜잭션 테이블 컬럼 추가
│   ├── migration_add_transaction_constraints.sql  # 유니크 제약조건 추가
│   ├── migration_click_tracking.sql               # 클릭 추적 테이블
│   ├── migration_correct_daily_submissions.sql    # Daily submissions 보정
│   ├── run_migration.sh          # 마이그레이션 실행 스크립트 (Linux/Mac)
│   ├── run_migration.bat         # 마이그레이션 실행 스크립트 (Windows)
│   ├── run_correction_migration.sh # 보정 마이그레이션 (Linux/Mac)
│   └── run_correction_migration.bat # 보정 마이그레이션 (Windows)
├── terraform/                    # AWS 인프라 코드 (IaC)
│   ├── main.tf                   # 메인 인프라 정의
│   ├── variables.tf              # 변수 정의
│   └── terraform.tfvars.example  # 변수 예시 파일
├── public/                       # 정적 파일
│   ├── favicon.ico
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── test_*.py                     # 테스트 스크립트들 (6개 파일)
├── setup_services.bat           # 서비스 설정 스크립트 (Windows)
├── setup_services.sh            # 서비스 설정 스크립트 (Linux/Mac)
├── start-dev.bat                # 개발 환경 시작 (Windows)
├── docker-compose.yml           # 로컬 개발 환경
├── Dockerfile                   # 프로덕션 Docker 이미지
├── Dockerfile.dev               # 개발용 Docker 이미지
├── package.json                 # Node.js 의존성
├── next.config.ts               # Next.js 설정
├── tsconfig.json                # TypeScript 설정
├── env.example                  # 환경 변수 예시
├── VERIFICATION_CHECKLIST.md    # 검증 체크리스트
├── SECURITY_UPGRADE_REPORT.md   # 보안 강화 보고서
├── PYTHON_SETUP_README.md       # Python 설정 가이드
└── README.md                    # 프로젝트 문서
```

## 🔧 주요 기능

### 1. 데이터 가치 평가 (Analysis Service)
- 검색어의 구체성 분석
- 상업적 가치 점수 계산
- 품질 개선 제안 제공

### 2. 역경매 시스템 (Auction Service)
- 실시간 역경매 생성
- 다중 플랫폼 입찰 처리
- 경매 상태 관리

### 3. 보상 시스템 (Payment Service)
- 1차/2차 보상 지급
- 거래 내역 관리
- 결제 처리

### 4. 검증 시스템 (Verification Service)
- 2차 보상 증빙 검증
- OCR 기반 문서 분석
- 검증 결과 관리

### 5. 사용자 관리 (User Service)
- 사용자 대시보드
- 수익 통계
- 품질 이력 관리

### 6. 품질 관리 (Quality Service)
- 동적 제출 한도 계산
- 품질 점수 기반 제한 관리

### 7. 광고주 관리 (Advertiser Service)
- 광고주 회원가입 및 인증
- 자동입찰 시스템
- 머신러닝 기반 입찰 최적화
- 광고주 대시보드 및 성과 분석

### 8. 관리자 시스템 (Admin Panel)
- **관리자 인증**: JWT 기반 관리자 로그인 시스템
- **광고주 심사**: 광고주 회원가입 승인/거절 관리
- **심사 상태 관리**: 대기/승인/거절 상태별 조회 및 업데이트
- **데이터 수정**: 광고주 키워드 및 카테고리 수정 권한
- **심사 메모**: 관리자별 심사 의견 및 권고 입찰가 설정

### 9. 클릭 추적 및 보상 시스템 (Enhanced)
- **실시간 클릭 추적**: 사용자별 광고 클릭 패턴 분석
- **멱등성 보장**: 중복 클릭 방지 및 데이터 정합성 유지
- **일일 한도 관리**: 품질 점수 기반 동적 제출 한도 적용
- **보상 차등화**: 입찰 광고와 폴백 광고별 차등 보상 지급

### 10. 대시보드 시스템 (Enhanced)
- **실시간 데이터 연동**: 모든 통계가 실제 DB 데이터 기반
- **에러 처리**: 네트워크 에러, 로딩 실패 등에 대한 재시도 버튼
- **로딩 상태**: Skeleton UI와 독립적 로딩 스피너
- **실시간 업데이트**: React Query를 통한 캐싱 및 백그라운드 업데이트
- **에러 모니터링**: 자동 에러 로깅 및 복구 메커니즘

## 🛠️ 기술 스택

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **React 18**
- **Tailwind CSS**
- **React Query** (데이터 페칭 및 캐싱)
- **Lucide React** (아이콘)
- **Recharts** (차트 라이브러리)

### Backend (Microservices)
- **FastAPI** (Python)
- **Pydantic** (데이터 검증)
- **Uvicorn** (ASGI 서버)

### Infrastructure
- **AWS API Gateway** (API 관리)
- **AWS Application Load Balancer** (로드 밸런싱)
- **Terraform** (인프라 코드)
- **Docker** (컨테이너화)

## 🔒 보안

- 모든 API 요청에 CSRF 토큰 포함
- 입력 데이터 검증 및 sanitization
- XSS 방지를 위한 출력 이스케이핑
- 적절한 인증 및 권한 검사

## 📊 성능 최적화

- Next.js Image 컴포넌트 사용
- 코드 스플리팅 및 동적 임포트
- 폰트 최적화 (next/font)
- 불필요한 리렌더링 방지
- React Query를 통한 데이터 캐싱
- 백그라운드 데이터 갱신
- 낙관적 업데이트

## 🛡️ 에러 처리 및 모니터링

### 에러 처리
- **ErrorBoundary**: 컴포넌트 레벨 에러 캐치
- **재시도 메커니즘**: 네트워크 에러 시 자동 재시도
- **Fallback UI**: 에러 상태에 대한 사용자 친화적 UI
- **부분적 로딩**: 일부 데이터 실패 시에도 다른 섹션 정상 표시

### 로딩 상태
- **Skeleton UI**: 로딩 중 콘텐츠 구조 미리보기
- **독립적 로딩**: 각 섹션별 개별 로딩 상태
- **점진적 로딩**: 중요한 데이터부터 우선 표시

### 에러 모니터링
- **자동 로깅**: 모든 에러의 자동 수집 및 분류
- **에러 분류**: 네트워크, 런타임, 인증 등 유형별 분류
- **심각도 평가**: 에러의 중요도에 따른 우선순위 설정
- **사용자별 추적**: 개별 사용자의 에러 패턴 분석

## 📈 대시보드 시스템 개선사항

### 실시간 데이터 연동
- **수익 요약**: 이번달/지난달 수익 비교 및 성장률 계산
- **품질 이력**: 실제 품질 점수 기반 4주간 추이 차트
- **제출 한도**: 실시간 사용량 및 품질 점수 기반 한도 표시
- **통계 데이터**: 월간 검색 횟수, 성공률, 평균 품질 점수

### 사용자 경험 개선
- **React Query**: 캐싱 및 백그라운드 데이터 갱신
- **실시간 업데이트**: 30초마다 자동 데이터 갱신
- **탭 포커스**: 브라우저 탭 활성화 시 데이터 갱신
- **낙관적 업데이트**: 사용자 액션에 대한 즉각적인 UI 반영

### 안정성 향상
- **에러 격리**: 한 컴포넌트의 에러가 전체 대시보드에 영향 없음
- **자동 복구**: 네트워크 복구 시 자동 데이터 갱신
- **에러 히스토리**: 로컬 스토리지에 에러 기록 저장
- **성능 최적화**: 불필요한 API 호출 방지 및 효율적인 캐싱

## 🆕 최신 업데이트 (2025-01-20)

### ✅ 회원가입 시스템 완전 수정 및 에러 해결 (2025-09-14)

#### **광고주 회원가입 시스템 완전 개선**
- **문제**: 422 Unprocessable Entity 오류로 광고주 회원가입 실패
- **원인**: Next.js API 라우트의 Zod 스키마가 백엔드 Pydantic 모델과 불일치
- **해결**: 
  - Zod 스키마를 백엔드 규칙과 완벽 동기화
  - `username` 필드 자동 생성 (이메일 → username 변환)
  - 백엔드가 기대하는 필드명으로 데이터 변환 (`companyName` → `company_name`, `businessSetup` → `business_setup`)
  - API 라우팅 수정 (광고주는 `/api/advertiser/register`로, 일반 사용자는 `/api/auth/register`로)

#### **일반 사용자 회원가입 시스템 개선**
- **문제**: 일반 사용자도 `companyName`, `businessSetup` 필드 요구로 인한 422 오류
- **해결**: 
  - 조건부 Zod 스키마 적용 (`z.discriminatedUnion` 사용)
  - 광고주용/일반 사용자용 스키마 분리
  - userType에 따른 데이터 처리 로직 분기

#### **어드민 승인 시스템 완전 수정**
- **문제**: 403 Forbidden 오류로 광고주 승인 불가
- **원인**: 
  1. JWT 검증 시 `issuer`/`audience` 클레임 미확인
  2. PUT/PATCH 요청 시 Authorization 헤더 누락
- **해결**:
  - JWT 검증에 `issuer`/`audience` 클레임 확인 추가
  - PUT/PATCH 요청에 Authorization 헤더 전달 추가
  - 어드민 인증 완전 수정

#### **기술적 개선사항**
- **의존성 추가**: `zod` 패키지 설치
- **아이콘 수정**: `Switch` → `ToggleLeft`로 변경 (lucide-react 호환성)
- **에러 처리 강화**: 백엔드 에러 메시지를 프론트엔드로 완전 전달
- **자동 로그인 방지**: 회원가입 후 의도치 않은 로그인 시도 차단

#### **주요 수정 파일들**
```
app/api/auth/register/route.ts          # 회원가입 API 완전 수정
app/lib/admin-auth.ts                   # 어드민 JWT 검증 수정
app/api/admin/advertiser-review/route.ts # 어드민 API 헤더 전달 수정
app/components/AuthForm.tsx             # 자동 로그인 방지 로직 추가
app/components/advertiser/AutoBidToggle.tsx # 아이콘 수정
```

#### **에러 해결 과정 및 실수 방지 가이드**

##### **1. 422 Unprocessable Entity 오류 해결**
```typescript
// ❌ 잘못된 방법 (기존)
const ClientSchema = z.object({
  userType: z.enum(['advertiser', 'user']),
  email: z.string().email(),
  password: z.string().min(8),
  companyName: z.string().min(1), // 모든 사용자에게 필수
  businessSetup: BusinessSetupSchema, // 모든 사용자에게 필수
});

// ✅ 올바른 방법 (수정 후)
const AdvertiserSchema = BaseSchema.extend({
  userType: z.literal('advertiser'),
  companyName: z.string().min(1, { message: "회사명은 필수입니다." }).max(100),
  businessSetup: BusinessSetupSchema,
});

const UserSchema = BaseSchema.extend({
  userType: z.literal('user'),
  username: z.string().min(1, { message: "사용자명은 필수입니다." }).max(50),
});

const ClientSchema = z.discriminatedUnion('userType', [
  AdvertiserSchema,
  UserSchema,
]);
```

##### **2. 백엔드 데이터 구조 맞추기**
```typescript
// ❌ 잘못된 방법 (기존)
const backendPayload = {
  ...clientData,
  username: clientData.email, // 백엔드 규칙 위반
};

// ✅ 올바른 방법 (수정 후)
const backendPayload = {
  username: emailUsername, // 이메일 기반 username 생성
  email: clientData.email,
  password: clientData.password,
  company_name: clientData.companyName, // snake_case 변환
  business_setup: { // snake_case 변환
    ...clientData.businessSetup,
    categories: numericCategories, // string → number 변환
  },
};
```

##### **3. API 라우팅 수정**
```typescript
// ❌ 잘못된 방법 (기존)
const response = await fetch(`${process.env.API_GATEWAY_URL}/api/auth/register`, {
  // 모든 요청이 user-service로만 라우팅됨
});

// ✅ 올바른 방법 (수정 후)
const endpoint = clientData.userType === 'advertiser' 
  ? '/api/advertiser/register'  // 광고주는 advertiser-service로
  : '/api/auth/register';       // 일반 사용자는 user-service로

const response = await fetch(`${process.env.API_GATEWAY_URL}${endpoint}`, {
  // userType에 따른 올바른 라우팅
});
```

##### **4. JWT 검증 수정**
```typescript
// ❌ 잘못된 방법 (기존)
const { payload } = await jwtVerify(token, SECRET_KEY)
// issuer/audience 클레임 확인 안함

// ✅ 올바른 방법 (수정 후)
const issuer = process.env.JWT_ISSUER || 'digisafe-api'
const audience = process.env.JWT_AUDIENCE || 'digisafe-client'

const { payload } = await jwtVerify(token, SECRET_KEY, {
  issuer: issuer,
  audience: audience
})
```

##### **5. Authorization 헤더 전달**
```typescript
// ❌ 잘못된 방법 (기존)
const response = await fetch(`${advertiserServiceUrl}/admin/update-review`, {
  method: 'PUT',
  // Authorization 헤더 누락
});

// ✅ 올바른 방법 (수정 후)
const authHeader = request.headers.get('authorization')
const response = await fetch(`${advertiserServiceUrl}/admin/update-review`, {
  method: 'PUT',
  headers: {
    'Authorization': authHeader || '',
    'Content-Type': 'application/json'
  }
});
```

#### **실수 방지를 위한 체크리스트**

##### **회원가입 시스템 개발 시**
- [ ] **Zod 스키마**: 백엔드 Pydantic 모델과 완전 일치하는지 확인
- [ ] **필드명 변환**: camelCase → snake_case 변환 로직 포함
- [ ] **조건부 검증**: userType에 따른 다른 스키마 적용
- [ ] **API 라우팅**: userType에 따른 올바른 엔드포인트 선택
- [ ] **username 생성**: 이메일 기반 username 변환 로직 포함

##### **어드민 시스템 개발 시**
- [ ] **JWT 검증**: issuer/audience 클레임 확인 포함
- [ ] **헤더 전달**: 모든 API 요청에 Authorization 헤더 전달
- [ ] **에러 처리**: 백엔드 에러 메시지를 프론트엔드로 전달
- [ ] **자동 로그인 방지**: 회원가입 후 localStorage 정리

##### **Docker 빌드 시**
- [ ] **의존성 확인**: 새로운 패키지 설치 후 Docker 재빌드
- [ ] **아이콘 호환성**: lucide-react 버전에 맞는 아이콘 사용
- [ ] **빌드 로그 확인**: 컴파일 오류나 경고 메시지 확인
- [ ] **로컬 테스트**: Docker 빌드 전 로컬에서 `npm run build` 테스트

##### **에러 디버깅 시**
- [ ] **브라우저 콘솔**: 상세한 에러 메시지 확인
- [ ] **네트워크 탭**: API 요청/응답 헤더 및 본문 확인
- [ ] **백엔드 로그**: Docker 로그에서 실제 오류 원인 파악
- [ ] **데이터베이스**: 중복 데이터나 제약 조건 위반 확인

## 🆕 최신 업데이트 (2025-01-20)

### ✅ 새로운 API 엔드포인트 및 기능 추가

#### **클릭 추적 및 보상 시스템**
- **`/api/track-click`**: 광고 클릭 추적 및 보상 지급 API
  - 사용자 인증 기반 클릭 추적
  - 일일 제출 한도 검증 및 차감
  - 입찰 광고/폴백 광고 구분 처리
  - 멱등성 보장으로 중복 클릭 방지

#### **관리자 시스템 강화**
- **`/api/admin/login`**: 관리자 로그인 시스템
- **`/api/admin/advertiser-review`**: 광고주 심사 관리
  - 심사 대기/승인/거절 상태별 조회
  - 광고주 데이터 수정 (키워드, 카테고리)
  - 심사 결과 업데이트 및 메모 관리

#### **품질 평가 시스템**
- **`/api/evaluate-quality`**: 검색어 품질 평가 API
- **`/api/click/[searchId]`**: 검색별 클릭 통계 API

### ✅ 데이터베이스 마이그레이션 및 스키마 개선

#### **Transactions 테이블 강화**
- **누락된 컬럼 추가**: `search_id`, `bid_id`, `ad_type` 컬럼 추가
- **유니크 제약조건**: 일일 중복 트랜잭션 방지
- **트랜잭션 날짜 관리**: 자동 날짜 설정 트리거 추가
- **성능 최적화**: 인덱스 추가로 쿼리 성능 향상

#### **Daily Submissions 정합성 보장**
- **트랜잭션 기준 사용량 계산**: 실제 거래 건수 기반 정확한 사용량 표시
- **멱등성 보장**: 동일한 (user_id, search_id, bid_id) 조합 중복 방지
- **자동 보정 시스템**: 데이터 불일치 시 자동 수정

### ✅ Advertiser Service 추가 및 최적화

#### **새로운 서비스 추가**
- **Advertiser Service (포트 8007)**: 광고주 관리 및 자동입찰 시스템
- **머신러닝 기반 입찰 최적화**: AutoBidOptimizer를 통한 지능형 입찰가 계산
- **광고주 대시보드**: 실시간 성과 분석 및 통계 제공
- **자동입찰 시스템**: 품질 점수, 경쟁 상황, 예산 등을 고려한 자동 입찰

#### **주요 기능**
- **광고주 회원가입/로그인**: JWT 기반 인증 시스템
- **비즈니스 설정**: 키워드, 카테고리, 예산 설정
- **심사 시스템**: 관리자 승인 기반 광고주 활성화
- **성과 분석**: 키워드별, 시간대별 입찰 성과 분석
- **최적화 제안**: AI 기반 입찰 전략 개선 제안

#### **기술적 개선사항**
- **타입 안전성**: 모든 Record 타입 에러 해결
- **비동기 데이터베이스**: `postgresql+asyncpg://` 드라이버 사용
- **JWT 통일**: 게이트웨이와 동일한 시크릿 키 사용
- **환경변수 최적화**: 모든 서비스 URL 및 설정 통합

#### **환경변수 설정 개선**
```bash
# JWT 보안 (게이트웨이와 통일)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum
JWT_ISSUER=digisafe-api
JWT_AUDIENCE=digisafe-client

# 데이터베이스 (비동기 드라이버)
DATABASE_URL=postgresql+asyncpg://admin:your_secure_password_123@localhost:5433/search_exchange_db

# 모든 서비스 URL (게이트웨이용)
ADVERTISER_SERVICE_URL=http://localhost:8007
ANALYSIS_SERVICE_URL=http://localhost:8001
VERIFICATION_SERVICE_URL=http://localhost:8004
```

#### **코드 품질 향상**
- **에러 처리**: Record 타입을 dict로 변환하여 안전한 데이터 접근
- **보안 강화**: 하드코딩된 시크릿 키 제거
- **메모리 효율성**: 불필요한 import 제거로 19.4% 코드 라인 감소
- **런타임 안정성**: 모든 타입 에러 해결

## 📊 데이터베이스 마이그레이션 가이드

### 마이그레이션 파일들
- **`migration_add_transaction_columns.sql`**: transactions 테이블 누락 컬럼 추가
- **`migration_add_transaction_constraints.sql`**: 유니크 제약조건 및 트리거 추가
- **`migration_correct_daily_submissions.sql`**: daily_submissions 데이터 정합성 보정
- **`migration_click_tracking.sql`**: 클릭 추적 테이블 추가

### 마이그레이션 실행 방법

#### Windows 사용자
```bash
cd database
run_migration.bat                    # 기본 마이그레이션
run_correction_migration.bat         # 데이터 보정 마이그레이션
```

#### Linux/macOS 사용자
```bash
cd database
./run_migration.sh                   # 기본 마이그레이션
./run_correction_migration.sh        # 데이터 보정 마이그레이션
```

### 마이그레이션 검증
```sql
-- Transactions 테이블 컬럼 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'transactions' 
AND column_name IN ('search_id', 'bid_id', 'ad_type');

-- Daily Submissions 정합성 확인
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
  SELECT user_id, COUNT(*)::int AS tx_count
  FROM transactions
  WHERE created_at::date = CURRENT_DATE
  GROUP BY user_id
) tx ON ds.user_id = tx.user_id
WHERE ds.submission_date = CURRENT_DATE;
```

## 🔧 최근 해결된 문제점들

### ✅ 데이터 흐름 연결 완료
- **검색 → 데이터 저장**: 검색할 때마다 `search_queries` 테이블에 자동 저장
- **품질 점수 이력**: 검색 시 품질 점수가 `user_quality_history` 테이블에 주차별 저장
- **일일 제출 현황**: 검색할 때마다 `daily_submissions` 테이블에 제출 횟수 업데이트
- **경매 상태 관리**: 입찰 선택 시 경매 상태를 'completed'로 자동 업데이트

### ✅ 실시간 통계 계산
- **Quality History**: 실제 품질 점수 기반 4주간 추이 차트 표시
- **Daily Submission Limit**: 품질 점수에 따른 동적 제출 한도 계산 및 표시
- **Total Searches**: 이번달 실제 검색 횟수 카운트
- **Success Rate**: 완료된 경매 대비 전체 경매 비율 계산
- **Avg Quality Score**: 실제 검색 쿼리의 평균 품질 점수 계산

### ✅ 인증 시스템 강화
- **JWT 토큰 검증**: 모든 API 요청에 사용자 인증 필수
- **개인화된 데이터**: 사용자별 고유한 대시보드 데이터 제공
- **보안 강화**: 인증되지 않은 요청 차단

### ✅ 자동 데이터 갱신
- **검색 완료 시**: 대시보드 통계 자동 갱신
- **경매 완료 시**: 수익 및 거래 내역 자동 업데이트
- **이벤트 기반 갱신**: 사용자 액션에 따른 즉시 데이터 반영

## 🧪 테스트 및 검증 가이드

### Daily 사용량 통일 검증 체크리스트

#### 1. 환경 설정 확인
- [ ] `.env` 파일에 `DEFAULT_DAILY_LIMIT=5` 설정 확인
- [ ] 데이터베이스 마이그레이션 실행 완료
  - [ ] `migration_add_transaction_constraints.sql` 실행
  - [ ] `migration_correct_daily_submissions.sql` 실행

#### 2. 로그인 → 대시보드 확인
- [ ] 로그인 성공
- [ ] `/dashboard` 접근 시 Today's Usage가 `0/5`로 표시
- [ ] 검색만 여러 번 해도 사용량 변동 없음 (0/5 유지)

#### 3. 광고 클릭 → 보상 지급 테스트
- [ ] 검색 후 입찰 광고 클릭
- [ ] 네트워크 탭에서 `/api/user/earnings` 1회만 호출 확인
- [ ] 대시보드 Today's Usage가 `1/5`로 갱신
- [ ] 거래 1건 생성 확인

#### 4. 중복 클릭 방지 테스트
- [ ] 동일한 광고를 빠르게 여러 번 클릭
- [ ] `/api/user/earnings`에서 멱등성 응답 확인
- [ ] 사용량이 중복으로 증가하지 않음

#### 5. 일일 한도 초과 테스트
- [ ] 5번째 광고 클릭까지 정상 작동
- [ ] 6번째 광고 클릭 시 HTTP 429 에러 반환
- [ ] 에러 메시지: "일일 제출 한도(5회)를 초과했습니다"

### 주요 테스트 스크립트들

#### 시스템 통합 테스트
```bash
# 전체 API 통합 테스트
python test_api.py

# 최종 통합 테스트 (사용자 등록 → 로그인 → 수익 테스트)
python test_final.py

# 모든 서비스 헬스체크
python test_health_all.py
```

#### 특화 테스트
```bash
# 대시보드 데이터 검증 (README에서 언급됨)
python test_dashboard_data.py

# 품질 서비스 base_limit 계산 테스트
python test_base_limit.py

# 비밀번호 해시 검증 테스트
python test_password.py
```

### Advertiser Service 테스트
```bash
# Advertiser Service 디렉토리로 이동
cd services/advertiser-service

# 가상환경 활성화
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/Mac

# 환경변수 설정
$env:JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum"
$env:DATABASE_URL="postgresql+asyncpg://admin:your_secure_password_123@localhost:5433/search_exchange_db"

# 서비스 실행
python main.py

# API 테스트
curl http://localhost:8007/health
curl http://localhost:8007/business-categories
```

### 수동 테스트 시나리오

#### 기본 사용자 플로우
1. **로그인**: 사용자 계정으로 로그인
2. **검색**: 메인 페이지에서 검색어 입력 및 제출
3. **대시보드 확인**: 대시보드에서 다음 항목들이 실시간 업데이트되는지 확인:
   - Quality History 차트
   - Daily Submission Limit
   - Total Searches 카운트
   - Success Rate 퍼센트
   - Avg Quality Score
4. **입찰 선택**: 경매에서 입찰 선택 후 거래 내역 확인
5. **실시간 갱신**: 30초 후 자동 데이터 갱신 확인

#### 관리자 시스템 테스트
1. **관리자 로그인**: `/admin/login`에서 관리자 계정으로 로그인
2. **광고주 심사**: `/admin/advertiser-review`에서 대기 중인 광고주 조회
3. **심사 처리**: 광고주 승인/거절 및 메모 작성
4. **데이터 수정**: 광고주 키워드 및 카테고리 수정 테스트

#### 클릭 추적 시스템 테스트
1. **검색 후 클릭**: 검색 결과에서 광고 클릭
2. **API 호출 확인**: `/api/track-click` API 정상 호출 확인
3. **보상 지급**: `/api/user/earnings`를 통한 보상 지급 확인
4. **사용량 업데이트**: 대시보드에서 Today's Usage 증가 확인

### Advertiser Service 테스트 시나리오
1. **서비스 실행**: Advertiser Service가 포트 8007에서 정상 실행되는지 확인
2. **Health Check**: `GET /health` 엔드포인트로 서비스 상태 확인
3. **비즈니스 카테고리**: `GET /business-categories`로 카테고리 목록 조회
4. **광고주 회원가입**: `POST /register`로 새 광고주 등록
5. **로그인**: `POST /login`으로 JWT 토큰 발급
6. **대시보드**: `GET /dashboard`로 광고주 대시보드 데이터 확인
7. **자동입찰 최적화**: `POST /auto-bid/optimize`로 입찰가 최적화 테스트
8. **API 문서**: `http://localhost:8007/docs`로 Swagger UI 확인

## 🚨 문제 해결 가이드

### 자주 발생하는 문제들

#### 1. 데이터베이스 연결 오류
```bash
# Docker 컨테이너 상태 확인
docker ps | grep postgres-db

# 데이터베이스 재시작
docker-compose restart postgres-db

# 연결 테스트
docker exec -it postgres-db psql -U postgres -d postgres -c "SELECT 1;"
```

#### 2. Daily 사용량 불일치 문제
```bash
# 보정 마이그레이션 실행
cd database
./run_correction_migration.sh  # Linux/Mac
run_correction_migration.bat   # Windows
```

#### 3. 서비스 간 연결 문제
```bash
# 모든 서비스 상태 확인
docker-compose ps

# 서비스 로그 확인
docker-compose logs -f user-service
docker-compose logs -f advertiser-service

# 환경 변수 확인
cat .env | grep SERVICE_URL
```

#### 4. 마이그레이션 실행 오류
```bash
# Docker 상태 확인 후 마이그레이션 재실행
docker-compose up -d
cd database
./run_migration.sh
```

### 성능 최적화 팁

#### 데이터베이스 최적화
- 정기적인 `VACUUM` 및 `ANALYZE` 실행
- 인덱스 사용률 모니터링
- 쿼리 성능 분석

#### 애플리케이션 최적화
- React Query 캐시 설정 조정
- 이미지 최적화 및 압축
- 번들 크기 최적화

## 📚 추가 문서

- **`VERIFICATION_CHECKLIST.md`**: Daily 사용량 통일 검증 상세 가이드
- **`SECURITY_UPGRADE_REPORT.md`**: 보안 강화 보고서
- **`PYTHON_SETUP_README.md`**: Python 마이크로서비스 설정 가이드

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 링크: [https://github.com/action5861/gatekeeper](https://github.com/action5861/gatekeeper)