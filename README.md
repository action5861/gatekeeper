# DigiSafe - Digital Asset Management Service

DigiSafe는 사용자의 중요한 정보를 안전하게 저장하고, 긴급 상황에서 지정된 제3자에게 접근을 제공하는 보안 디지털 자산 관리 서비스입니다.

## 🏗️ 아키텍처

이 프로젝트는 **마이크로서비스 아키텍처(MSA)**로 설계되었습니다.

### 서비스 구성

| 서비스 | 포트 | 역할 | 기술 스택 |
|--------|------|------|-----------|
| **Frontend** | 3000 | Next.js 프론트엔드 | Next.js, TypeScript, React |
| **Analysis Service** | 8001 | 데이터 가치 평가 | FastAPI, Python |
| **Auction Service** | 8002 | 역경매 생성 및 입찰 처리 | FastAPI, Python |
| **Payment Service** | 8003 | 보상 지급 및 거래 내역 | FastAPI, Python |
| **Verification Service** | 8004 | 2차 보상 검증 | FastAPI, Python |
| **User Service** | 8005 | 사용자 데이터 관리 | FastAPI, Python |
| **Quality Service** | 8006 | 동적 제출 한도 관리 | FastAPI, Python |
| **Advertiser Service** | 8007 | 광고주 관리 및 자동입찰 | FastAPI, Python |

### API Gateway

AWS API Gateway를 통해 모든 마이크로서비스의 요청을 중앙에서 관리합니다:

- `/api/search` → Analysis Service + Auction Service
- `/api/auction/*` → Auction Service
- `/api/reward` → Payment Service
- `/api/verify` → Verification Service
- `/api/user/*` → User Service
- `/api/advertiser/*` → Advertiser Service

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
├── app/                          # Next.js 프론트엔드
│   ├── api/                      # API 프록시 엔드포인트
│   │   ├── error-reporting/      # 에러 모니터링 API
│   │   └── user/                 # 사용자 관련 API
│   ├── components/               # React 컴포넌트
│   │   ├── dashboard/            # 대시보드 컴포넌트
│   │   └── ui/                   # 공통 UI 컴포넌트
│   │       ├── ErrorBoundary.tsx # 에러 처리 컴포넌트
│   │       ├── ErrorFallback.tsx # 에러 상태 UI
│   │       └── Skeleton.tsx      # 로딩 상태 UI
│   ├── dashboard/                # 대시보드 페이지
│   ├── lib/                      # 공통 라이브러리
│   │   ├── hooks/                # 커스텀 훅
│   │   │   └── useDashboardData.ts # 대시보드 데이터 훅
│   │   └── utils/                # 유틸리티
│   │       └── errorMonitor.ts   # 에러 모니터링
│   ├── providers.tsx             # React Query Provider
│   └── layout.tsx                # 전역 레이아웃
├── services/                     # 마이크로서비스
│   ├── analysis-service/         # 데이터 가치 평가 서비스
│   ├── auction-service/          # 역경매 서비스
│   ├── payment-service/          # 결제 서비스
│   ├── verification-service/     # 검증 서비스
│   ├── user-service/             # 사용자 서비스
│   ├── quality-service/          # 품질 관리 서비스
│   └── advertiser-service/       # 광고주 관리 서비스
├── database/                     # 데이터베이스 스키마
│   └── init.sql                  # 초기 데이터베이스 설정
├── terraform/                    # AWS 인프라 코드
│   ├── main.tf                   # API Gateway 및 ALB 설정
│   ├── variables.tf              # 변수 정의
│   └── terraform.tfvars.example  # 변수 예시
├── docker-compose.yml            # 로컬 개발 환경
└── README.md                     # 프로젝트 문서
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

### 8. 대시보드 시스템 (Enhanced)
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

## 🆕 최신 업데이트 (2025-09-05)

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

## 🧪 테스트 방법

### 대시보드 데이터 테스트
```bash
# 데이터베이스 연결 확인 및 데이터 테스트
python test_dashboard_data.py
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

### Advertiser Service 테스트 시나리오
1. **서비스 실행**: Advertiser Service가 포트 8007에서 정상 실행되는지 확인
2. **Health Check**: `GET /health` 엔드포인트로 서비스 상태 확인
3. **비즈니스 카테고리**: `GET /business-categories`로 카테고리 목록 조회
4. **광고주 회원가입**: `POST /register`로 새 광고주 등록
5. **로그인**: `POST /login`으로 JWT 토큰 발급
6. **대시보드**: `GET /dashboard`로 광고주 대시보드 데이터 확인
7. **자동입찰 최적화**: `POST /auto-bid/optimize`로 입찰가 최적화 테스트
8. **API 문서**: `http://localhost:8007/docs`로 Swagger UI 확인

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
