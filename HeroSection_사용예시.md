# HeroSection 컴포넌트 사용 가이드

## 📦 컴포넌트 위치
`app/components/main/HeroSection.tsx`

## 🎨 디자인 특징

- **배경**: Deep Navy (`bg-slate-900`)
- **Primary Accent**: Neon Mint/Teal (`text-teal-400`, `#64ffda`와 유사)
- **폰트**: Inter (이미 layout.tsx에 설정됨)
- **반응형**: 모바일부터 데스크톱까지 완벽 지원

## 📝 구현된 요소

### 1. Badge (상단)
- 텍스트: "🌐 세계 최초 실시간 검색의도 자산거래 플랫폼"
- 스타일: 반투명 파란 배경, 둥근 모서리, 작은 텍스트

### 2. 메인 헤드라인 (3단 구조)
- **1줄**: "당신의 검색어는 이미 돈이었습니다." (흰색, medium, 3xl-5xl)
- **2줄**: "지금까지 플랫폼만 가져갔죠." (회색, light, 작게)
- **3줄**: "이제 그 돈을 당신이 가져가세요." (민트색, extrabold, 5xl-7xl)

### 3. 서브 헤드라인
- 텍스트: "검색어 올리는 순간 현금이 됩니다."
- 스타일: 중간 크기, 밝은 회색

### 4. 신뢰 표시
- 텍스트: "✅ AI 평가 | ✅ 광고주 실시간 입찰 | ✅ 100% 투명 정산"
- 스타일: 작은 텍스트, 회색, 반응형 레이아웃

## 🚀 사용 방법

### 기본 사용

```tsx
import HeroSection from '@/components/main/HeroSection'

export default function Home() {
  return (
    <div>
      <HeroSection />
      {/* 다른 컴포넌트들 */}
    </div>
  )
}
```

### 기존 page.tsx에 통합 예시

```tsx
// app/page.tsx
import HeroSection from '@/components/main/HeroSection'

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-900">
      <Header />
      <HeroSection />
      {/* 기존 검색 입력, 품질 평가 등의 컴포넌트들 */}
    </div>
  )
}
```

## 📱 반응형 브레이크포인트

- **모바일 (기본)**: 
  - Badge: `text-xs`
  - 헤드라인 1: `text-3xl`
  - 헤드라인 2: `text-xl`
  - 헤드라인 3: `text-4xl`
  - 서브 헤드라인: `text-lg`

- **태블릿 (sm)**: 
  - Badge: `text-sm`
  - 헤드라인 1: `text-4xl`
  - 헤드라인 2: `text-2xl`
  - 헤드라인 3: `text-5xl`
  - 서브 헤드라인: `text-xl`

- **데스크톱 (md, lg)**: 
  - 헤드라인 1: `text-5xl`
  - 헤드라인 2: `text-3xl`
  - 헤드라인 3: `text-6xl` / `text-7xl`
  - 서브 헤드라인: `text-2xl`

## 🎨 커스터마이징

### 색상 변경

컴포넌트 내부의 Tailwind 클래스를 수정하면 됩니다:

- 민트/틸 색상: `text-teal-400` → `text-emerald-400`, `text-cyan-400` 등
- 배경색: `bg-slate-900` → `bg-[#0a192f]` (정확한 색상 코드 사용 가능)
- 배지 배경: `bg-blue-950/40` → 원하는 색상으로 변경

### 간격 조정

- 요소 간 간격: `space-y-6 sm:space-y-8` 값 조정
- 패딩: `py-16 sm:py-20 lg:py-28` 값 조정

## ✅ 완료된 기능

- ✅ 정확한 텍스트 계층 구조
- ✅ 반응형 디자인 (모바일 우선)
- ✅ Deep Navy 배경
- ✅ Neon Mint/Teal 액센트 색상
- ✅ 적절한 간격과 리듬감
- ✅ Inter 폰트 (이미 설정됨)
- ✅ 접근성 고려 (시맨틱 HTML)

## 📋 체크리스트

- [x] Badge 구현
- [x] 3단 헤드라인 구조
- [x] 서브 헤드라인
- [x] 신뢰 표시
- [x] 반응형 디자인
- [x] 색상 스키마 준수
- [x] 폰트 설정 확인

