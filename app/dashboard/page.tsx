// 대시보드 페이지

'use client'

import Header from '@/components/Header'
import EarningsSummary from '@/components/dashboard/EarningsSummary'
import QualityHistory from '@/components/dashboard/QualityHistory'
import RealtimeStats from '@/components/dashboard/RealtimeStats'
import SubmissionLimitCard from '@/components/dashboard/SubmissionLimitCard'
import { TransactionHistory } from '@/components/dashboard/TransactionHistory'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { DashboardSkeleton } from '@/components/ui/Skeleton'
import { useTransactionData } from '@/lib/hooks/useDashboardData'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'



export default function Dashboard() {
  const { transactions, isLoading, error } = useTransactionData()
  const router = useRouter()

  // 인증 체크
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
    }
  }, [router])

  // 전체 로딩 상태
  if (isLoading) {
    return <DashboardSkeleton />
  }

  // 전체 에러 상태
  if (error) {
    return (
      <div className="min-h-screen bg-slate-900">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-red-400">
            <p>Error loading dashboard: {error instanceof Error ? error.message : 'An error occurred'}</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Dashboard</h1>
          <p className="text-slate-400">Track your earnings and quality performance</p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Earnings Summary */}
          <div className="animate-fadeInUp">
            <ErrorBoundary>
              <EarningsSummary />
            </ErrorBoundary>
          </div>

          {/* Quality History */}
          <div className="animate-fadeInUp animation-delay-200">
            <ErrorBoundary>
              <QualityHistory />
            </ErrorBoundary>
          </div>

          {/* Submission Limit Card */}
          <div className="animate-fadeInUp animation-delay-400">
            <ErrorBoundary>
              <SubmissionLimitCard />
            </ErrorBoundary>
          </div>
        </div>

        {/* Realtime Stats */}
        <ErrorBoundary>
          <RealtimeStats />
        </ErrorBoundary>

        {/* Transaction History */}
        <div className="mt-8 animate-fadeInUp animation-delay-900">
          <ErrorBoundary>
            {transactions && (
              <TransactionHistory initialTransactions={transactions} />
            )}
          </ErrorBoundary>
        </div>
      </main>
    </div>
  )
} 