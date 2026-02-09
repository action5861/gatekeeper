// How It Works page

'use client'

import Header from '@/components/Header'
import { ArrowRight, Library, Lock, ShieldCheck } from 'lucide-react'
import Link from 'next/link'

export default function HowItWorks() {
    return (
        <div className="min-h-screen bg-slate-900">
            <Header />

            {/* Improved Hero Section */}
            <section className="relative pt-20 pb-8 text-center overflow-hidden">
                {/* 배경 효과 */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-500/10 rounded-full blur-[100px] -z-10" />

                <div className="max-w-4xl mx-auto px-4">
                    {/* 1. 상단 라벨 (Badge) */}
                    <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-6">
                        <span className="flex w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse" />
                        Intendex 이용 가이드
                    </div>

                    {/* 2. 메인 타이틀 (가독성 강화) */}
                    <h1 className="text-4xl md:text-5xl lg:text-5xl font-extrabold text-white tracking-tight mb-6">
                        검색 의도로 수익을 만드는 4단계
                    </h1>

                    {/* 3. 설명 텍스트 (폭 제한 및 가독성 조정) */}
                    <p className="text-lg md:text-xl text-slate-300 leading-relaxed max-w-2xl mx-auto mb-6">
                        검색하고, 방문하고, 돌아오세요. 그것만 하면 현금이 쌓입니다.
                    </p>

                    {/* 4. 프로세스 요약 (시각적 흐름) */}
                    <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 text-sm md:text-base font-semibold text-slate-400">
                        <div className="flex items-center gap-2 text-blue-400 bg-blue-400/10 px-4 py-2 rounded-full border border-blue-400/20">
                            <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs">1</span>
                            자동 상장
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-600" />
                        <div className="flex items-center gap-2 text-green-400 bg-green-400/10 px-4 py-2 rounded-full border border-green-400/20">
                            <span className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">2</span>
                            실시간 입찰
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-600" />
                        <div className="flex items-center gap-2 text-purple-400 bg-purple-400/10 px-4 py-2 rounded-full border border-purple-400/20">
                            <span className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center text-white text-xs">3</span>
                            검증 및 체류
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-600" />
                        <div className="flex items-center gap-2 text-yellow-400 bg-yellow-400/10 px-4 py-2 rounded-full border border-yellow-400/20">
                            <span className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center text-slate-900 text-xs">4</span>
                            복귀 및 정산
                        </div>
                    </div>
                </div>
            </section>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-4 pt-8 pb-16">

                {/* The 4 Steps Section */}
                <section className="mb-16">
                    <div className="space-y-8">
                        {/* Step 1 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-blue-400">
                                STEP 1. 자동 상장 (Listing)
                            </h3>
                            <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                평소처럼 검색하세요. Intendex가 당신의 검색어 중 가치 있는 것을 찾아 <strong className="text-blue-300">&apos;검색어 매물&apos;</strong>로 자동 상장합니다.
                            </p>
                            <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-600/30">
                                <p className="text-base text-blue-300 font-semibold">
                                    💡 안심하세요: 개인정보를 파는 것이 아닙니다. 광고주가 들어올 수 있는 <strong>&apos;세션 접근권(시간)&apos;</strong>만 안전하게 거래됩니다.
                                </p>
                            </div>
                        </div>

                        {/* Step 2 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-green-400">
                                STEP 2. 실시간 입찰 (Bidding)
                            </h3>
                            <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                광고주들이 당신의 검색 의도를 사기 위해 경쟁합니다. 가장 높은 가격을 부른 광고주가 즉시 낙찰됩니다.
                            </p>
                            <div className="bg-green-900/20 rounded-lg p-4 border border-green-600/30">
                                <p className="text-base text-green-300 font-semibold">
                                    [예시] A광고주(500P) vs B광고주(700P) 경쟁 → <strong className="text-green-200">700P 낙찰!</strong>
                                </p>
                            </div>
                        </div>

                        {/* Step 3 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-yellow-400">
                                STEP 3. 검증 및 체류 (Verification) ⭐
                            </h3>
                            <p className="text-lg text-slate-300 leading-relaxed mb-6">
                                수익을 확정 짓는 가장 중요한 단계입니다. 낙찰된 광고주 사이트를 방문하여 둘러보세요. 공정한 거래를 위해 <strong className="text-yellow-300">&apos;최소한의 시간&apos;</strong>이 필요합니다.
                            </p>

                            <div className="bg-yellow-900/20 rounded-lg p-4 border border-yellow-600/30 mb-4">
                                <ul className="text-sm text-slate-300 space-y-3">
                                    <li className="flex items-center gap-3">
                                        <span className="text-green-400 font-bold text-base">20초 이상:</span>
                                        <span className="text-base">100% 전액 지급 💰 <span className="text-green-300">(완벽한 거래!)</span></span>
                                    </li>
                                    <li className="flex items-center gap-3">
                                        <span className="text-yellow-400 font-bold text-base">10~20초:</span>
                                        <span className="text-base">50~75% 부분 지급 <span className="text-yellow-300">(조금 아쉬워요)</span></span>
                                    </li>
                                    <li className="flex items-center gap-3">
                                        <span className="text-red-400 font-bold text-base">10초 미만:</span>
                                        <span className="text-base">지급 불가 <span className="text-red-300">(너무 짧아요)</span></span>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        {/* Step 4 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-purple-400">
                                STEP 4. 복귀 및 정산 (Settlement)
                            </h3>
                            <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                검색이 끝나셨나요? 반드시 Intendex 탭으로 돌아오세요. 돌아오는 순간, 체류 시간을 확인하고 지갑에 정산금이 <strong className="text-purple-300">&apos;띠링!&apos;</strong> 하고 입금됩니다.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Core Principles Section */}
                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-center mb-12 text-slate-100">
                        핵심 원칙
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Column 1 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-blue-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <Library className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                완전한 투명성
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                모든 입찰, 체결가, 정산 기록을 공개합니다. 블랙박스 없이 운영하여 모두에게 공정한 시장을 보장합니다.
                            </p>
                        </div>

                        {/* Column 2 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-green-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <ShieldCheck className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                증명 기반 가치
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                검증된 성과만 거래합니다. 단순 클릭이 아니라, &apos;실제 체류&apos;가 검증되어야 돈이 지급됩니다.
                            </p>
                        </div>

                        {/* Column 3 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-purple-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <Lock className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                철저한 익명성
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                데이터를 판매하지 않습니다. 임시적, 세션 기반 접근권만 거래하여 개인정보가 항상 보호됩니다.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Final CTA Section */}
                <section className="text-center">
                    <h2 className="text-3xl font-bold mb-6 text-slate-100">
                        Intendex에 참여할 준비가 되셨나요?
                    </h2>
                    <p className="text-xl text-slate-300 mb-8">
                        검색 의도의 가치를 투명하게 평가받는 새로운 방식을 경험하세요.
                    </p>
                    <Link
                        href="/register"
                        className="inline-flex items-center space-x-3 px-8 py-4 text-lg bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-bold rounded-xl transition-all duration-200 transform hover:scale-105"
                    >
                        <span>시작하기</span>
                        <ArrowRight className="w-5 h-5" />
                    </Link>
                </section>
            </main>

            {/* Footer */}
            <footer className="mt-16 text-center text-slate-400 py-8">
                <p className="text-sm mb-2">
                    © 2025 Intendex. All rights reserved.
                </p>
                <p className="text-xs text-slate-500 font-semibold">
                    의도가 곧 접근권. 증명으로 정산.
                </p>
            </footer>
        </div>
    )
}
