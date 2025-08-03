'use client'

import Header from '@/components/Header'
import ReviewStatus from '@/components/advertiser/ReviewStatus'
import AccountSettings from '@/components/dashboard/AccountSettings'
import BiddingSummary from '@/components/dashboard/BiddingSummary'
import MyBids from '@/components/dashboard/MyBids'
import PerformanceHistory from '@/components/dashboard/PerformanceHistory'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface DashboardData {
    biddingSummary: {
        totalBids: number
        successfulBids: number
        totalSpent: number
        averageBidAmount: number
    }
    performanceHistory: Array<{
        name: string
        score: number
    }>
    recentBids: Array<{
        id: string
        auctionId: string
        amount: number
        timestamp: string
        status: 'active' | 'won' | 'lost' | 'pending'
        highestBid?: number
        myBid: number
    }>
}

export default function AdvertiserDashboard() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [reviewStatus, setReviewStatus] = useState<string>('pending')
    const [showDashboard, setShowDashboard] = useState(false)
    const router = useRouter()

    const fetchDashboardData = async () => {
        try {
            const token = localStorage.getItem('token')
            if (!token) {
                router.push('/login')
                return
            }

            const response = await fetch('/api/advertiser/dashboard', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('token')
                    localStorage.removeItem('userType')
                    router.push('/login')
                    return
                }
                throw new Error('Failed to fetch dashboard data')
            }

            const data = await response.json()
            setDashboardData(data)

            // 심사 상태에 따라 대시보드 표시 여부 결정
            if (data.review_status === 'approved') {
                setShowDashboard(true)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchDashboardData()
    }, [])

    const handleReviewStatusChange = (status: string) => {
        setReviewStatus(status)
        if (status === 'approved') {
            setShowDashboard(true)
        } else {
            setShowDashboard(false)
        }
    }

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
                    <h1 className="text-3xl font-bold text-slate-100 mb-2">Advertiser Dashboard</h1>
                    <p className="text-slate-400">Manage your bidding campaigns and track performance</p>
                </div>

                {/* Review Status - Always show first */}
                <div className="mb-8 animate-fadeInUp">
                    <ReviewStatus onStatusChange={handleReviewStatusChange} />
                </div>

                {/* Conditional Dashboard Content */}
                {showDashboard ? (
                    <>
                        {/* Dashboard Grid */}
                        <div className="grid lg:grid-cols-3 gap-8">
                            {/* Bidding Summary */}
                            <div className="animate-fadeInUp">
                                <BiddingSummary biddingSummary={dashboardData?.biddingSummary} />
                            </div>

                            {/* Performance History */}
                            <div className="animate-fadeInUp animation-delay-200">
                                <PerformanceHistory performanceHistory={dashboardData?.performanceHistory} />
                            </div>

                            {/* Account Settings */}
                            <div className="animate-fadeInUp animation-delay-400">
                                <AccountSettings />
                            </div>
                        </div>

                        {/* Additional Stats */}
                        <div className="mt-8 grid md:grid-cols-3 gap-6">
                            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-600">
                                <h3 className="text-lg font-semibold text-slate-100 mb-2">Active Campaigns</h3>
                                <p className="text-3xl font-bold text-blue-400">12</p>
                                <p className="text-sm text-slate-400 mt-1">Currently running</p>
                            </div>

                            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-700">
                                <h3 className="text-lg font-semibold text-slate-100 mb-2">Click Rate</h3>
                                <p className="text-3xl font-bold text-green-400">3.2%</p>
                                <p className="text-sm text-slate-400 mt-1">Average CTR</p>
                            </div>

                            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-800">
                                <h3 className="text-lg font-semibold text-slate-100 mb-2">Conversion Rate</h3>
                                <p className="text-3xl font-bold text-yellow-400">1.8%</p>
                                <p className="text-sm text-slate-400 mt-1">Avg conversion</p>
                            </div>
                        </div>

                        {/* My Bids */}
                        <div className="mt-8 animate-fadeInUp animation-delay-900">
                            <MyBids recentBids={dashboardData?.recentBids} />
                        </div>
                    </>
                ) : (
                    /* 심사 대기 중일 때 표시할 내용 */
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Clock className="w-8 h-8 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-300 mb-2">
                            심사 완료 대기 중
                        </h3>
                        <p className="text-slate-400 mb-6">
                            심사가 완료되면 광고 등록 및 대시보드 기능을 이용할 수 있습니다.
                        </p>
                        <div className="bg-slate-800/50 rounded-lg p-6 max-w-md mx-auto">
                            <h4 className="text-sm font-medium text-slate-300 mb-3">심사 완료 후 이용 가능한 기능</h4>
                            <ul className="text-sm text-slate-400 space-y-2">
                                <li className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                                    <span>광고 등록 및 입찰</span>
                                </li>
                                <li className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                    <span>실시간 성과 모니터링</span>
                                </li>
                                <li className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                                    <span>입찰 내역 및 통계</span>
                                </li>
                                <li className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                                    <span>계정 설정 및 관리</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
} 