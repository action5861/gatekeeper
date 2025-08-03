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

### API Gateway

AWS API Gateway를 통해 모든 마이크로서비스의 요청을 중앙에서 관리합니다:

- `/api/search` → Analysis Service + Auction Service
- `/api/auction/*` → Auction Service
- `/api/reward` → Payment Service
- `/api/verify` → Verification Service
- `/api/user/*` → User Service

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
│   └── quality-service/          # 품질 관리 서비스
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

### 7. 대시보드 시스템 (Enhanced)
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
