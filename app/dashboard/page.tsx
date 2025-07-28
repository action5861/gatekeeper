// 대시보드 페이지

'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import EarningsSummary from '@/components/dashboard/EarningsSummary'
import QualityHistory from '@/components/dashboard/QualityHistory'
import SubmissionLimitCard from '@/components/dashboard/SubmissionLimitCard'
import { TransactionHistory } from '@/components/dashboard/TransactionHistory'
import { Transaction } from '@/lib/types'

interface DashboardData {
  earnings: {
    total: number;
    primary: number;
    secondary: number;
  };
  qualityHistory: Array<{
    name: string;
    score: number;
  }>;
  submissionLimit: {
    level: 'Excellent' | 'Good' | 'Average' | 'Needs Improvement';
    dailyMax: number;
  };
  transactions: Transaction[];
}

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/user/dashboard')
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }
      const data = await response.json()
      setDashboardData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  // 보상 지급 후 대시보드 새로고침을 위한 이벤트 리스너
  useEffect(() => {
    const handleRewardUpdate = () => {
      fetchDashboardData()
    }

    // 커스텀 이벤트 리스너 등록
    window.addEventListener('reward-updated', handleRewardUpdate)

    return () => {
      window.removeEventListener('reward-updated', handleRewardUpdate)
    }
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
          </div>
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-red-400">
            <p>Error loading dashboard: {error}</p>
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
            <EarningsSummary earnings={dashboardData?.earnings} />
          </div>

          {/* Quality History */}
          <div className="animate-fadeInUp animation-delay-200">
            <QualityHistory />
          </div>

          {/* Submission Limit Card */}
          <div className="animate-fadeInUp animation-delay-400">
            {dashboardData?.submissionLimit && (
              <SubmissionLimitCard limitData={dashboardData.submissionLimit} />
            )}
          </div>
        </div>

        {/* Additional Stats */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-600">
            <h3 className="text-lg font-semibold text-slate-100 mb-2">Total Searches</h3>
            <p className="text-3xl font-bold text-blue-400">24</p>
            <p className="text-sm text-slate-400 mt-1">This month</p>
          </div>
          
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-700">
            <h3 className="text-lg font-semibold text-slate-100 mb-2">Success Rate</h3>
            <p className="text-3xl font-bold text-green-400">87%</p>
            <p className="text-sm text-slate-400 mt-1">Auction completion</p>
          </div>
          
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-800">
            <h3 className="text-lg font-semibold text-slate-100 mb-2">Avg Quality Score</h3>
            <p className="text-3xl font-bold text-yellow-400">72</p>
            <p className="text-sm text-slate-400 mt-1">Out of 100</p>
          </div>
        </div>

        {/* Transaction History */}
        <div className="mt-8 animate-fadeInUp animation-delay-900">
          {dashboardData?.transactions && (
            <TransactionHistory initialTransactions={dashboardData.transactions} />
          )}
        </div>
      </main>
    </div>
  )
} 