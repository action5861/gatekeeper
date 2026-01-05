'use client'

/**
 * Intendex Hero Section Component
 * 
 * Modern, premium typography using Pretendard font.
 * Optimized for Korean text with proper letter spacing and line breaking.
 * Professional design inspired by Toss and Apple style.
 */
export default function HeroSection() {
  return (
    <section className="relative w-full bg-[#0a192f] text-white border-b border-slate-800">
      <div className="flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 pt-8 sm:pt-12 pb-16 sm:pb-20">
        <div className="max-w-4xl mx-auto text-center">

          {/* Badge - Top */}
          <div className="inline-flex items-center justify-center px-4 py-1 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-full mb-4 break-keep">
            <span className="text-xs md:text-sm text-slate-300 tracking-tight">
              🌐 세계 최초 실시간 검색의도 자산거래 플랫폼
            </span>
          </div>

          {/* Headline Group - 3-Step Story with Premium Typography */}
          <div className="w-full max-w-4xl">
            {/* Line 1: Fact */}
            <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight tracking-tight break-keep">
              당신의 검색은 이미 돈이었습니다.
            </h1>

            {/* Line 2: Conflict - Whisper/Pause */}
            <p className="text-lg md:text-xl font-light text-slate-450 my-5 py-1.5 tracking-tight break-keep">
              지금까지 플랫폼(네이버,구글,메타..)만 챙겨갔습니다.
            </p>

            {/* Line 3: Solution - Climax */}
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black text-[#64ffda] leading-none tracking-tighter mb-5 break-keep">
              이제 그 돈을 당신이 되찾으세요.
            </h2>
          </div>

          {/* Sub-headline */}
          <p className="text-lg font-medium text-slate-300 mb-3 max-w-3xl mx-auto tracking-tight break-keep">
            검색어 올리는 순간 현금이 됩니다.
          </p>

          {/* Trust Indicators */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm md:text-base text-slate-400 font-medium tracking-tight break-keep">
            <span className="flex items-center gap-1.5">
              <span>✅</span>
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
