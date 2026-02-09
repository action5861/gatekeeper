'use client'

/**
 * Intendex Hero Section Component
 * 
 * Modern, premium typography using SUIT Variable font.
 * Optimized for Korean text with proper letter spacing and line breaking.
 * Professional design inspired by Toss and Apple style.
 */
export default function HeroSection() {
  return (
    <section className="relative w-full bg-[#0a192f] text-white border-b border-slate-800">
      <div className="flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 pt-8 sm:pt-12 pb-6 sm:pb-8">
        <div className="max-w-4xl mx-auto text-center">

          {/* Badge - Top */}
          <div className="inline-flex items-center justify-center px-4 py-1 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-full mb-4 break-keep">
            <span className="text-xs md:text-sm text-slate-300 tracking-tight">
              세계 최초 실시간 검색 의도 거래 인프라
            </span>
          </div>

          {/* Headline Group */}
          <div className="w-full max-w-4xl">
            <h1 className="text-3xl md:text-6xl font-bold text-white leading-tight tracking-tight break-keep">
              AI가 데이터를 독점하는 시대,
              <br />
              검색은 새로운 기본소득입니다.
            </h1>



          </div>

          {/* 서브 헤드라인 아래 상세 설명 */}
          <p className="text-base md:text-lg font-normal text-slate-300 mt-8 mb-6 max-w-[850px] mx-auto leading-relaxed break-keep">
            Intendex는 사용자의 검색 의도(Intent)를 거래 가능한 자산으로 전환하고,
            <br className="hidden sm:block" />
            성과가 검증된 경우에만 광고주가 비용을 지불하는 투명한 정산 프로토콜입니다.
            <br className="hidden sm:block" />
            검색 한 번이 현금 보상으로 전환되는 새로운 경제를 경험하세요.
          </p>

          {/* Trust Indicators */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm md:text-base text-slate-400 font-medium tracking-tight break-keep">
            <span className="flex items-center gap-1.5">
              <span>🔍</span>
              <span>AI 평가</span>
            </span>
            <span className="hidden sm:inline text-slate-600">|</span>
            <span className="flex items-center gap-1.5">
              <span>✅</span>
              <span>광고주 실시간 입찰</span>
            </span>
            <span className="hidden sm:inline text-slate-600">|</span>
            <span className="flex items-center gap-1.5">
              <span>✅</span>
              <span>100% 투명 정산</span>
            </span>
          </div>

        </div>
      </div>
    </section>
  )
}
