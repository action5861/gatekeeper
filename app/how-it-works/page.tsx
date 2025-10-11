// How It Works page

'use client'

import { Library, ShieldCheck, Lock, ArrowRight } from 'lucide-react'
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
            How Intendex Works: The Intent Exchange
          </h1>
          <p className="text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto">
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
                1. Step One: Listing Your Intent
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                When you perform a search, your intent is privately and automatically listed on our exchange as a tradable &apos;Intent Lot&apos;. This is not your personal data; it is a temporary, one-time access right to your session.
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
                3. Step Three: Execution
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                The highest bid wins the auction transparently. The winning advertiser is granted exclusive access to your session for a contracted period (e.g., 15, 30, or 60 seconds), free from competing ads.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
              <h3 className="text-xl font-bold mb-4 text-yellow-400">
                4. Step Four: Verification
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                Our automated system verifies the delivery in real-time. We measure key Service Level Agreement (SLA) metrics like visibility, user focus, and duration to ensure the quality promised to the advertiser was delivered.
              </p>
            </div>

            {/* Step 5 */}
            <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
              <h3 className="text-xl font-bold mb-4 text-red-400">
                5. Step Five: Settlement
              </h3>
              <p className="text-lg text-slate-300 leading-relaxed">
                Based on the verification results (PASSED, PARTIAL, or FAILED), payment is automatically calculated and settled to your account. If the quality conditions aren&apos;t met, the advertiser is refunded. This is settlement, not a reward.
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
