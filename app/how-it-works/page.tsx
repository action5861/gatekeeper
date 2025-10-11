// How It Works page

'use client'

import { ArrowRight, Library, Lock, ShieldCheck } from 'lucide-react'
import Link from 'next/link'

export default function HowItWorks() {
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
                     <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto mb-4">
                         The world&apos;s first intent exchange with SLA-verified settlement
                     </p>
                     <p className="text-lg text-slate-400 leading-relaxed max-w-3xl mx-auto">
                         Intendex is not another ad network. We are the world&apos;s first exchange for user intent, operating on a transparent, verifiable, and fair transaction model. Here&apos;s how we turn your intent into value, step by step.
                     </p>
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
                             <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                 When you search, Intendex automatically creates an &apos;Intent Lot&apos;—a time-bound access right to your session (not your data). You do nothing; the listing happens instantly and securely.
                             </p>
                             <p className="text-base text-blue-300 font-semibold">
                                 Key: This is session-limited access, never data ownership transfer.
                             </p>
                         </div>

                        {/* Step 2 */}
                        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                            <h3 className="text-xl font-bold mb-4 text-green-400">
                                2. Step Two: Receiving Real-time Bids
                            </h3>
                            <p className="text-lg text-slate-300 leading-relaxed">
                                Advertisers (Buyers) who have placed standing orders that match your intent&apos;s category and quality instantly bid in a real-time auction to gain access. You don&apos;t have to do anything—the market comes to you.
                            </p>
                        </div>

                         {/* Step 3 */}
                         <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                             <h3 className="text-xl font-bold mb-4 text-purple-400">
                                 3. Step Three: Transparent Execution
                             </h3>
                             <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                 The highest bid wins—and you see the exact execution price immediately. The winning advertiser gains exclusive access to your session for 15-60 seconds (no competing ads). All prices are publicly logged.
                             </p>
                             <p className="text-base text-purple-300 font-semibold">
                                 Example: If 3 advertisers bid ₩1,800, ₩2,100, and ₩2,400—you get matched at ₩2,400 (minus platform fee).
                             </p>
                         </div>

                         {/* Step 4 */}
                         <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                             <h3 className="text-xl font-bold mb-4 text-yellow-400">
                                 4. Step Four: SLA Verification
                             </h3>
                             <p className="text-lg text-slate-300 leading-relaxed mb-4">
                                 Our SDK measures actual delivery quality in real-time:
                             </p>
                             <ul className="text-base text-slate-300 space-y-2 mb-4">
                                 <li>• <strong className="text-yellow-300">V_atf</strong> (Above-the-fold visibility): Was the ad actually visible?</li>
                                 <li>• <strong className="text-yellow-300">F_ratio</strong> (Focus): Did you switch tabs or get distracted?</li>
                                 <li>• <strong className="text-yellow-300">T_dwell</strong> (Dwell time): How long did you engage?</li>
                                 <li>• <strong className="text-yellow-300">X_ok</strong> (Exclusivity): Were competing ads blocked as promised?</li>
                             </ul>
                             <p className="text-base text-yellow-300 font-semibold">
                                 If metrics don&apos;t meet thresholds → Automatic adjustment or refund.
                             </p>
                         </div>

                         {/* Step 5 */}
                         <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
                             <h3 className="text-xl font-bold mb-4 text-red-400">
                                 5. Step Five: Automatic Settlement
                             </h3>
                             <div className="text-lg text-slate-300 leading-relaxed mb-4">
                                 <ul className="space-y-2 mb-4">
                                     <li>• <strong className="text-green-300">PASSED (100%)</strong>: All SLA metrics met → You receive full payment</li>
                                     <li>• <strong className="text-yellow-300">PARTIAL (40-70%)</strong>: Some metrics met → Prorated payment</li>
                                     <li>• <strong className="text-red-300">FAILED (0%)</strong>: Metrics not met → Advertiser gets full refund, you get ₩0</li>
                                 </ul>
                             </div>
                             <p className="text-base text-red-300 font-semibold mb-2">
                                 Example: ₩2,400 execution price
                             </p>
                             <ul className="text-sm text-slate-400 space-y-1 mb-4">
                                 <li>• Platform fee (15%): -₩360</li>
                                 <li>• Your settlement: ₩2,040 (if PASSED)</li>
                             </ul>
                             <p className="text-base text-red-300 font-semibold">
                                 All transactions are logged for audit and dispute resolution.
                             </p>
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
