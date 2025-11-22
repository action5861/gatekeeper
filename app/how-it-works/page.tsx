// How It Works page

'use client'

import { ArrowRight, Library, Lock, ShieldCheck } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function HowItWorks() {
    const [userType, setUserType] = useState<'user' | 'advertiser' | null>(null)

    useEffect(() => {
        if (typeof window !== 'undefined') {
            const storedUserType = localStorage.getItem('userType')
            if (storedUserType === 'user' || storedUserType === 'advertiser') {
                setUserType(storedUserType)
            }
        }
    }, [])

    return (
        <div className="min-h-screen bg-slate-900">
            {/* Header */}
            <div className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                                <ArrowRight className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
                                Intendex
                            </h1>
                        </div>
                        <nav className="flex items-center space-x-1">
                            <Link
                                href="/"
                                className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 text-slate-300 hover:text-white hover:bg-slate-700"
                            >
                                <span className="font-medium">Exchange</span>
                            </Link>
                            <Link
                                href="/dashboard"
                                className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 text-slate-300 hover:text-white hover:bg-slate-700"
                            >
                                <span className="font-medium">Dashboard</span>
                            </Link>
                            <Link
                                href="/how-it-works"
                                className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 bg-blue-600 text-white shadow-lg"
                            >
                                <span className="font-medium">How It Works</span>
                            </Link>
                        </nav>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-4 py-16">
                {/* Header Section */}
                <section className="text-center mb-16">
                    <h1 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-green-400 to-purple-400 bg-clip-text text-transparent">
                        How Intendex Works: List. Price. Trade. Settle.
                    </h1>
                    {userType === 'user' ? (
                        <>
                            <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto mb-4">
                                Search with Intent. Earn Real Value.
                            </p>
                            <p className="text-lg text-slate-400 leading-relaxed max-w-3xl mx-auto">
                                Every time you search, Intendex automatically creates a listing for your intent. Advertisers bid in real-time, and you earn money when you engage with quality ads. It&apos;s that simple. Your search intent becomes valuable, transparent, and fair.
                            </p>
                        </>
                    ) : userType === 'advertiser' ? (
                        <>
                            <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto mb-4">
                                Target Intent. Pay for Proof.
                            </p>
                            <p className="text-lg text-slate-400 leading-relaxed max-w-3xl mx-auto">
                                Bid on high-quality user intent in real-time. Our SLA-verified settlement ensures you only pay for genuine engagement. Set your parameters, automate your bids, and get transparent, auditable results with fraud protection built in.
                            </p>
                        </>
                    ) : (
                        <>
                            <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto mb-4">
                                The world&apos;s first intent exchange with SLA-verified settlement
                            </p>
                            <p className="text-lg text-slate-400 leading-relaxed max-w-3xl mx-auto">
                                Intendex is not another ad network. We are the world&apos;s first exchange for user intent, operating on a transparent, verifiable, and fair transaction model. Here&apos;s how we turn your intent into value, step by step.
                            </p>
                        </>
                    )}
                </section>

                {/* Visual Flowchart Section */}
                <section className="mb-16">
                    <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                        <h2 className="text-2xl font-bold text-center mb-8 text-slate-100">
                            Transaction Flow
                        </h2>
                        <div className="flex flex-col md:flex-row items-center justify-center space-y-4 md:space-y-0 md:space-x-4">
                            {/* Step 1 */}
                            <div className="bg-blue-600/20 border border-blue-500/30 rounded-lg p-4 text-center min-w-[120px]">
                                <div className="text-blue-400 font-bold text-sm">1</div>
                                <div className="text-white font-semibold">Listing</div>
                            </div>

                            <ArrowRight className="text-slate-400 w-6 h-6 hidden md:block" />

                            {/* Step 2 */}
                            <div className="bg-green-600/20 border border-green-500/30 rounded-lg p-4 text-center min-w-[120px]">
                                <div className="text-green-400 font-bold text-sm">2</div>
                                <div className="text-white font-semibold">Bidding</div>
                            </div>

                            <ArrowRight className="text-slate-400 w-6 h-6 hidden md:block" />

                            {/* Step 3 */}
                            <div className="bg-purple-600/20 border border-purple-500/30 rounded-lg p-4 text-center min-w-[120px]">
                                <div className="text-purple-400 font-bold text-sm">3</div>
                                <div className="text-white font-semibold">Execution</div>
                            </div>

                            <ArrowRight className="text-slate-400 w-6 h-6 hidden md:block" />

                            {/* Step 4 */}
                            <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-4 text-center min-w-[120px]">
                                <div className="text-yellow-400 font-bold text-sm">4</div>
                                <div className="text-white font-semibold">Verification</div>
                            </div>

                            <ArrowRight className="text-slate-400 w-6 h-6 hidden md:block" />

                            {/* Step 5 */}
                            <div className="bg-red-600/20 border border-red-500/30 rounded-lg p-4 text-center min-w-[120px]">
                                <div className="text-red-400 font-bold text-sm">5</div>
                                <div className="text-white font-semibold">Settlement</div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* The 5 Steps Section */}
                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-center mb-12 text-slate-100">
                        The 5 Steps of a Transaction
                    </h2>

                    <div className="space-y-8">
                        {/* Step 1 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-blue-400">
                                1. Step One: Automatic Listing
                            </h3>
                            {userType === 'user' ? (
                                <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                    When you search, Intendex automatically creates an &apos;Intent Lot&apos;—a time-bound access right to your session (not your data). You do nothing; the listing happens instantly and securely.
                                </p>
                            ) : userType === 'advertiser' ? (
                                <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                    When users search with relevant intent matching your target keywords, an &apos;Intent Lot&apos; is automatically created. Your automated standing orders detect matching lots and prepare to bid.
                                </p>
                            ) : (
                                <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                    When you search, Intendex automatically creates an &apos;Intent Lot&apos;—a time-bound access right to your session (not your data). You do nothing; the listing happens instantly and securely.
                                </p>
                            )}
                            <p className="text-base text-blue-300 font-semibold">
                                Key: This is session-limited access, never data ownership transfer.
                            </p>
                        </div>

                        {/* Step 2 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-green-400">
                                2. Step Two: Real-time Bidding
                            </h3>
                            {userType === 'user' ? (
                                <p className="text-lg text-slate-300 leading-relaxed">
                                    Advertisers (Buyers) who have placed standing orders that match your intent&apos;s category and quality instantly bid in a real-time auction to gain access. You don&apos;t have to do anything—the market comes to you.
                                </p>
                            ) : userType === 'advertiser' ? (
                                <p className="text-lg text-slate-300 leading-relaxed">
                                    Your standing orders automatically bid in real-time auction when matching intent lots are detected. Set your parameters (keywords, quality threshold, max CPC) and let the system bid for you. You compete with other advertisers transparently.
                                </p>
                            ) : (
                                <p className="text-lg text-slate-300 leading-relaxed">
                                    Advertisers (Buyers) who have placed standing orders that match your intent&apos;s category and quality instantly bid in a real-time auction to gain access. You don&apos;t have to do anything—the market comes to you.
                                </p>
                            )}
                        </div>

                        {/* Step 3 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-purple-400">
                                3. Step Three: Transparent Execution
                            </h3>
                            {userType === 'user' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        The highest bid wins—and you see the exact execution price immediately. The winning advertiser gains exclusive access to your session for 15-60 seconds (no competing ads). All prices are publicly logged.
                                    </p>
                                    <p className="text-base text-purple-300 font-semibold">
                                        Example: If 3 advertisers bid 1,800P, 2,100P, and 2,400P—you get matched at 2,400P (minus platform fee).
                                    </p>
                                </>
                            ) : userType === 'advertiser' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        If you win the bid, you pay the second-highest bid price (Vickrey auction model). You get exclusive access to the user&apos;s session for 15-60 seconds with no competing ads. All execution prices are publicly logged for transparency.
                                    </p>
                                    <p className="text-base text-purple-300 font-semibold">
                                        Example: If you bid 2,400P and the next highest is 2,100P, you pay 2,100P (not your full bid). This incentivizes truthful bidding.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        The highest bid wins—and you see the exact execution price immediately. The winning advertiser gains exclusive access to your session for 15-60 seconds (no competing ads). All prices are publicly logged.
                                    </p>
                                    <p className="text-base text-purple-300 font-semibold">
                                        Example: If 3 advertisers bid 1,800P, 2,100P, and 2,400P—you get matched at 2,400P (minus platform fee).
                                    </p>
                                </>
                            )}
                        </div>

                        {/* Step 4 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-yellow-400">
                                4. Step Four: 2-Phase SLA Verification
                            </h3>
                            {userType === 'user' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-6">
                                        Our system verifies ad quality through a unique 2-phase hybrid model to ensure you earn fairly:
                                    </p>

                                    <div className="mb-6 bg-yellow-900/20 rounded-lg p-4 border border-yellow-600/30">
                                        <h4 className="font-bold text-yellow-300 mb-3">
                                            Phase 1: Immediate Verification (on click)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5">
                                            <li>• <strong className="text-yellow-200">V_atf</strong> (Visibility): Was the ad visible on screen?</li>
                                            <li>• <strong className="text-yellow-200">Clicked</strong>: Did you actually click the ad?</li>
                                        </ul>
                                        <p className="text-sm text-yellow-200 mt-3">
                                            ✅ If passed → Status: PENDING_RETURN (awaiting your return)
                                        </p>
                                        <p className="text-sm text-yellow-200">
                                            ❌ If failed (bot detected) → FAILED (no payment)
                                        </p>
                                    </div>

                                    <div className="bg-green-900/20 rounded-lg p-4 border border-green-600/30">
                                        <h4 className="font-bold text-green-300 mb-3">
                                            Phase 2: Final Verification (on your return)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5 mb-3">
                                            <li>• <strong className="text-green-200">Dwell Time</strong>: How long did you explore the advertiser&apos;s site?</li>
                                            <li className="text-xs text-slate-400 ml-4">Measured as: your return time - click time</li>
                                        </ul>
                                        <p className="text-sm text-green-200 mt-3 font-semibold">
                                            Final Decision:
                                        </p>
                                        <ul className="text-xs text-slate-300 space-y-1 ml-4">
                                            <li>• ≥10 seconds → PASSED (100% payout)</li>
                                            <li>• ≥5 seconds → PARTIAL (70% payout)</li>
                                            <li>• &lt;5 seconds → PARTIAL (50% payout)</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-yellow-300 font-semibold mt-4 italic">
                                        💡 Key insight: Users always return to check their earnings—that&apos;s when we accurately measure advertiser site dwell time.
                                    </p>
                                </>
                            ) : userType === 'advertiser' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-6">
                                        Our system verifies ad quality through a unique 2-phase hybrid model to protect you from fraud:
                                    </p>

                                    <div className="mb-6 bg-yellow-900/20 rounded-lg p-4 border border-yellow-600/30">
                                        <h4 className="font-bold text-yellow-300 mb-3">
                                            Phase 1: Immediate Verification (on click)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5">
                                            <li>• <strong className="text-yellow-200">V_atf</strong> (Visibility): Was your ad visible on screen?</li>
                                            <li>• <strong className="text-yellow-200">Clicked</strong>: Did the user actually click your ad?</li>
                                        </ul>
                                        <p className="text-sm text-yellow-200 mt-3">
                                            ✅ If passed → Status: PENDING_RETURN (awaiting user return)
                                        </p>
                                        <p className="text-sm text-yellow-200">
                                            ❌ If failed (bot detected) → FAILED (you get automatic refund)
                                        </p>
                                    </div>

                                    <div className="bg-green-900/20 rounded-lg p-4 border border-green-600/30">
                                        <h4 className="font-bold text-green-300 mb-3">
                                            Phase 2: Final Verification (on user return)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5 mb-3">
                                            <li>• <strong className="text-green-200">Dwell Time</strong>: How long did the user explore your site?</li>
                                            <li className="text-xs text-slate-400 ml-4">Measured as: user return time - click time</li>
                                        </ul>
                                        <p className="text-sm text-green-200 mt-3 font-semibold">
                                            Final Decision:
                                        </p>
                                        <ul className="text-xs text-slate-300 space-y-1 ml-4">
                                            <li>• ≥10 seconds → PASSED (you pay 100%)</li>
                                            <li>• ≥5 seconds → PARTIAL (you pay 70%)</li>
                                            <li>• &lt;5 seconds → PARTIAL (you pay 50%)</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-yellow-300 font-semibold mt-4 italic">
                                        💡 Key insight: Users always return to check their earnings—that&apos;s when we accurately measure dwell time and protect you from fake engagement.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-6">
                                        Our system verifies ad quality through a unique 2-phase hybrid model:
                                    </p>

                                    <div className="mb-6 bg-yellow-900/20 rounded-lg p-4 border border-yellow-600/30">
                                        <h4 className="font-bold text-yellow-300 mb-3">
                                            Phase 1: Immediate Verification (on click)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5">
                                            <li>• <strong className="text-yellow-200">V_atf</strong> (Visibility): Was the ad visible on screen?</li>
                                            <li>• <strong className="text-yellow-200">Clicked</strong>: Did you actually click the ad?</li>
                                        </ul>
                                        <p className="text-sm text-yellow-200 mt-3">
                                            ✅ If passed → Status: PENDING_RETURN (awaiting your return)
                                        </p>
                                        <p className="text-sm text-yellow-200">
                                            ❌ If failed (bot detected) → FAILED (no payment)
                                        </p>
                                    </div>

                                    <div className="bg-green-900/20 rounded-lg p-4 border border-green-600/30">
                                        <h4 className="font-bold text-green-300 mb-3">
                                            Phase 2: Final Verification (on your return)
                                        </h4>
                                        <ul className="text-sm text-slate-300 space-y-1.5 mb-3">
                                            <li>• <strong className="text-green-200">Dwell Time</strong>: How long did you explore the advertiser&apos;s site?</li>
                                            <li className="text-xs text-slate-400 ml-4">Measured as: your return time - click time</li>
                                        </ul>
                                        <p className="text-sm text-green-200 mt-3 font-semibold">
                                            Final Decision:
                                        </p>
                                        <ul className="text-xs text-slate-300 space-y-1 ml-4">
                                            <li>• ≥10 seconds → PASSED (100% payout)</li>
                                            <li>• ≥5 seconds → PARTIAL (70% payout)</li>
                                            <li>• &lt;5 seconds → PARTIAL (50% payout)</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-yellow-300 font-semibold mt-4 italic">
                                        💡 Key insight: Users always return to check their earnings—that&apos;s when we accurately measure advertiser site dwell time.
                                    </p>
                                </>
                            )}
                        </div>

                        {/* Step 5 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-red-400">
                                5. Step Five: Automatic Settlement
                            </h3>
                            {userType === 'user' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        Based on 2-phase verification, your earnings are calculated automatically:
                                    </p>

                                    <div className="space-y-3 mb-6">
                                        <div className="bg-green-900/20 rounded-lg p-3 border border-green-600/30">
                                            <p className="text-base font-bold text-green-300">
                                                ✅ PASSED (you earn 100%)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Ad clicked + visible + you stayed ≥10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-600/30">
                                            <p className="text-base font-bold text-yellow-300">
                                                ⚠️ PARTIAL (you earn 50-70%)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Ad clicked + visible + you stayed 5-10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-red-900/20 rounded-lg p-3 border border-red-600/30">
                                            <p className="text-base font-bold text-red-300">
                                                ❌ FAILED (no earnings)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Bot detected or no click → No payment to you
                                            </p>
                                        </div>
                                    </div>

                                    <div className="bg-slate-700/30 rounded-lg p-4 mb-4">
                                        <p className="text-base text-green-300 font-semibold mb-2">
                                            Example: 200P execution price
                                        </p>
                                        <ul className="text-sm text-slate-300 space-y-1">
                                            <li>• PASSED (10s+ dwell): You earn 200P</li>
                                            <li>• PARTIAL (7s dwell): You earn 140P (70%)</li>
                                            <li>• PARTIAL (3s dwell): You earn 100P (50%)</li>
                                            <li>• FAILED (no click): You earn 0P</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-green-300 font-semibold">
                                        💰 You earn more for longer engagement. Fair and transparent.
                                    </p>
                                </>
                            ) : userType === 'advertiser' ? (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        Based on 2-phase verification, your payment is calculated automatically:
                                    </p>

                                    <div className="space-y-3 mb-6">
                                        <div className="bg-green-900/20 rounded-lg p-3 border border-green-600/30">
                                            <p className="text-base font-bold text-green-300">
                                                ✅ PASSED (you pay 100%)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                User clicked + visible + user stayed ≥10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-600/30">
                                            <p className="text-base font-bold text-yellow-300">
                                                ⚠️ PARTIAL (you pay 50-70%)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                User clicked + visible + user stayed 5-10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-red-900/20 rounded-lg p-3 border border-red-600/30">
                                            <p className="text-base font-bold text-red-300">
                                                ❌ FAILED (automatic refund)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Bot detected or no click → Full refund to you
                                            </p>
                                        </div>
                                    </div>

                                    <div className="bg-slate-700/30 rounded-lg p-4 mb-4">
                                        <p className="text-base text-red-300 font-semibold mb-2">
                                            Example: 200P execution price
                                        </p>
                                        <ul className="text-sm text-slate-300 space-y-1">
                                            <li>• PASSED (10s+ dwell): You pay 200P</li>
                                            <li>• PARTIAL (7s dwell): You pay 140P (70%)</li>
                                            <li>• PARTIAL (3s dwell): You pay 100P (50%)</li>
                                            <li>• FAILED (no click): You pay 0P (refunded)</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-red-300 font-semibold">
                                        💡 You only pay for real engagement. Bot traffic = automatic refund.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                        Based on 2-phase verification, settlement is calculated automatically:
                                    </p>

                                    <div className="space-y-3 mb-6">
                                        <div className="bg-green-900/20 rounded-lg p-3 border border-green-600/30">
                                            <p className="text-base font-bold text-green-300">
                                                ✅ PASSED (100% payout)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Ad clicked + visible + advertiser site dwell ≥10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-600/30">
                                            <p className="text-base font-bold text-yellow-300">
                                                ⚠️ PARTIAL (50-70% payout)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                Ad clicked + visible + advertiser site dwell 5-10 seconds
                                            </p>
                                        </div>

                                        <div className="bg-red-900/20 rounded-lg p-3 border border-red-600/30">
                                            <p className="text-base font-bold text-red-300">
                                                ❌ FAILED (0% payout)
                                            </p>
                                            <p className="text-sm text-slate-300">
                                                No click or bot detected (ad not visible) → Advertiser gets refund
                                            </p>
                                        </div>
                                    </div>

                                    <div className="bg-slate-700/30 rounded-lg p-4 mb-4">
                                        <p className="text-base text-red-300 font-semibold mb-2">
                                            Example: 200P execution price
                                        </p>
                                        <ul className="text-sm text-slate-300 space-y-1">
                                            <li>• PASSED (10s+ dwell): 200P full payout</li>
                                            <li>• PARTIAL (7s dwell): 140P (70%)</li>
                                            <li>• PARTIAL (3s dwell): 100P (50%)</li>
                                            <li>• FAILED (no click): 0P + advertiser refunded</li>
                                        </ul>
                                    </div>

                                    <p className="text-sm text-red-300 font-semibold">
                                        🔐 All transactions are immutably logged for audit and dispute resolution.
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                </section>

                {/* Core Principles Section */}
                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-center mb-12 text-slate-100">
                        Our Core Principles
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Column 1 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-blue-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <Library className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                Total Transparency
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                Every bid, execution price, and settlement log is auditable. We operate without black boxes, ensuring a fair market for everyone.
                            </p>
                        </div>

                        {/* Column 2 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-green-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <ShieldCheck className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                Proof-Based Value
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                We trade in proven performance. If an ad&apos;s exposure isn&apos;t verified by our SLA, the transaction is adjusted or refunded. You only pay for what&apos;s verifiably delivered.
                            </p>
                        </div>

                        {/* Column 3 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700 text-center hover:border-purple-500/50 transition-all duration-300">
                            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-6">
                                <Lock className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 text-slate-100">
                                Privacy by Design
                            </h3>
                            <p className="text-slate-300 leading-relaxed">
                                We never sell your data. We only trade in temporary, session-based access rights, ensuring your privacy is always protected.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Final CTA Section */}
                <section className="text-center">
                    <h2 className="text-3xl font-bold mb-6 text-slate-100">
                        Ready to Join the Exchange?
                    </h2>
                    <p className="text-xl text-slate-300 mb-8">
                        Experience a new, transparent way to value your intent.
                    </p>
                    <Link
                        href="/register"
                        className="inline-flex items-center space-x-3 px-8 py-4 text-lg bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white font-bold rounded-xl transition-all duration-200 transform hover:scale-105"
                    >
                        <span>Get Started</span>
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
                    Intent as Access. Settlement by Proof.
                </p>
            </footer>
        </div>
    )
}
