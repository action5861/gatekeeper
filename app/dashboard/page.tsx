// [LIVE] 실제 데이터 주입으로 수정
'use client'
import Header from '@/components/Header'
import EarningsSummary from '@/components/dashboard/EarningsSummary'
import QualityHistory from '@/components/dashboard/QualityHistory'
import RealtimeStats from '@/components/dashboard/RealtimeStats'
import SubmissionLimitCard from '@/components/dashboard/SubmissionLimitCard'
import { TransactionHistory } from '@/components/dashboard/TransactionHistory'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { DashboardSkeleton } from '@/components/ui/Skeleton'
import { useDashboardData } from '@/lib/hooks/useDashboardData'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function Dashboard() {
  const { transactions, isLoading, error, summary, qualitySeries, realtime, refetch } = useDashboardData()
  const router = useRouter()
  const [shouldRedirect, setShouldRedirect] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
    const type = localStorage.getItem('userType')
    if (type === 'advertiser') {
      setShouldRedirect(true)
      router.replace('/advertiser/dashboard')
    }
  }, [router])

  useEffect(() => {
    if (error?.message === 'advertiser_redirect') {
      setShouldRedirect(true)
      router.replace('/advertiser/dashboard')
    }
  }, [error, router])

  if (shouldRedirect || error?.message === 'advertiser_redirect') {
    return <DashboardSkeleton />
  }

  if (isLoading) return <DashboardSkeleton />

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-red-400">
            <p>Error loading dashboard: {error.message}</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-100 mb-2">Dashboard</h1>
            <p className="text-slate-400">Track your earnings and quality performance</p>
          </div>
          <button 
            onClick={refetch}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            새로고침
          </button>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Earnings Summary */}
          <div className="animate-fadeInUp">
            <ErrorBoundary>
              <EarningsSummary
                todayRewards={summary?.today.rewards ?? 0}
                todayBids={summary?.today.bids ?? 0}
                todayBidValue={summary?.today.bidValue ?? 0}
                successRate={summary?.successRate ?? 0}
                avgQualityScore={summary?.avgQualityScore ?? 0}
                totalEarnings={summary?.totalEarnings ?? 0}
              />
            </ErrorBoundary>
          </div>

          {/* Quality History */}
          <div className="animate-fadeInUp animation-delay-200">
            <ErrorBoundary>
              <QualityHistory series={qualitySeries ?? []} />
            </ErrorBoundary>
          </div>

          {/* Submission Limit Card – 기존 로직 유지(별도 API면 여기에 주입 가능) */}
          <div className="animate-fadeInUp animation-delay-400">
            <ErrorBoundary>
              <SubmissionLimitCard />
            </ErrorBoundary>
          </div>
        </div>

        <ErrorBoundary>
          <RealtimeStats recentQueries={realtime?.recentQueries ?? 0} recentBids={realtime?.recentBids ?? 0} />
        </ErrorBoundary>

        <div className="mt-8 animate-fadeInUp animation-delay-900">
          <ErrorBoundary>
            {transactions && <TransactionHistory initialTransactions={transactions} />}
          </ErrorBoundary>
        </div>
      </main>
    </div>
  )
} 