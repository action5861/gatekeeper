'use client'

import {
    AlertCircle,
    ArrowDownRight,
    ArrowUpRight,
    BarChart3,
    Building2,
    Calendar,
    ChevronLeft,
    ChevronRight,
    DollarSign,
    Percent,
    RefreshCw,
    TrendingUp,
    Users
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'

interface PlatformSettlementSummary {
    total_count: number
    total_amount: number
    advertiser_count: number
    advertiser_amount: number
    platform_count: number
    platform_amount: number
    platform_ratio: number
}

interface DailySettlement {
    date: string
    platform_count: number
    platform_amount: number
    advertiser_count: number
    advertiser_amount: number
}

interface UserPlatformSettlement {
    user_id: number
    username: string
    email: string
    platform_count: number
    platform_amount: number
    last_settlement_date: string | null
}

interface StatsData {
    summary: PlatformSettlementSummary
    daily_trend: DailySettlement[]
    top_users: UserPlatformSettlement[]
    period: string
}

interface UsersData {
    users: UserPlatformSettlement[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export default function PlatformSettlementsPage() {
    const [statsData, setStatsData] = useState<StatsData | null>(null)
    const [usersData, setUsersData] = useState<UsersData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [period, setPeriod] = useState<'day' | 'week' | 'month'>('week')
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [activeTab, setActiveTab] = useState<'overview' | 'users'>('overview')
    const router = useRouter()

    const fetchStats = useCallback(async () => {
        const token = localStorage.getItem('adminToken')
        if (!token) {
            router.push('/admin/login')
            return
        }

        try {
            const response = await fetch(
                `/api/admin/platform-settlements?period=${period}&endpoint=stats`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            )

            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    localStorage.removeItem('adminToken')
                    router.push('/admin/login')
                    return
                }
                throw new Error('통계 데이터를 불러오는데 실패했습니다.')
            }

            const result = await response.json()
            if (result.success) {
                setStatsData(result.data)
            } else {
                throw new Error(result.error || '데이터 로드 실패')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '알 수 없는 오류')
        }
    }, [period, router])

    const fetchUsers = useCallback(async (page: number = 1) => {
        const token = localStorage.getItem('adminToken')
        if (!token) {
            router.push('/admin/login')
            return
        }

        try {
            const response = await fetch(
                `/api/admin/platform-settlements?period=${period}&endpoint=users&page=${page}&pageSize=20`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            )

            if (!response.ok) {
                throw new Error('사용자 데이터를 불러오는데 실패했습니다.')
            }

            const result = await response.json()
            if (result.success) {
                setUsersData(result.data)
            }
        } catch (err) {
            console.error('Users fetch error:', err)
        }
    }, [period, router])

    const handleRefresh = async () => {
        setIsRefreshing(true)
        setError(null)
        await Promise.all([fetchStats(), fetchUsers(currentPage)])
        setIsRefreshing(false)
    }

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true)
            setError(null)
            await Promise.all([fetchStats(), fetchUsers(1)])
            setIsLoading(false)
        }
        loadData()
    }, [period, fetchStats, fetchUsers])

    const handlePageChange = (page: number) => {
        setCurrentPage(page)
        fetchUsers(page)
    }

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
    }

    const formatDateTime = (dateStr: string | null) => {
        if (!dateStr) return '-'
        const date = new Date(dateStr)
        return date.toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    // 최대 높이 계산 (차트용)
    const maxDailyCount = statsData?.daily_trend
        ? Math.max(...statsData.daily_trend.map(d => d.platform_count + d.advertiser_count), 1)
        : 1

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                    <p className="text-slate-300">플랫폼 정산 데이터 로딩 중...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-900">
            {/* 헤더 */}
            <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-4">
                            <Link
                                href="/admin/advertiser-analytics"
                                className="text-slate-400 hover:text-white transition-colors"
                            >
                                <Building2 className="w-6 h-6" />
                            </Link>
                            <div>
                                <h1 className="text-xl font-bold text-white">플랫폼 정산 현황</h1>
                                <p className="text-sm text-slate-400">매칭 실패 시 플랫폼 200원 정산 내역</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            {/* 기간 선택 */}
                            <div className="flex items-center space-x-2 bg-slate-700 rounded-lg p-1">
                                {(['day', 'week', 'month'] as const).map((p) => (
                                    <button
                                        key={p}
                                        onClick={() => setPeriod(p)}
                                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                            period === p
                                                ? 'bg-blue-600 text-white'
                                                : 'text-slate-400 hover:text-white'
                                        }`}
                                    >
                                        {p === 'day' ? '오늘' : p === 'week' ? '1주' : '1달'}
                                    </button>
                                ))}
                            </div>
                            <button
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                                className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                            >
                                <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 p-4 bg-red-900/30 border border-red-500/50 rounded-lg flex items-center space-x-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <p className="text-red-300">{error}</p>
                    </div>
                )}

                {statsData && (
                    <>
                        {/* 요약 카드 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                            {/* 총 정산 건수 */}
                            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="p-2 bg-blue-500/20 rounded-lg">
                                        <BarChart3 className="w-6 h-6 text-blue-400" />
                                    </div>
                                </div>
                                <p className="text-sm text-slate-400 mb-1">총 정산 건수</p>
                                <p className="text-3xl font-bold text-white">
                                    {statsData.summary.total_count.toLocaleString()}
                                </p>
                                <div className="mt-2 flex items-center text-sm">
                                    <span className="text-green-400">광고주: {statsData.summary.advertiser_count.toLocaleString()}</span>
                                    <span className="text-slate-500 mx-2">|</span>
                                    <span className="text-yellow-400">플랫폼: {statsData.summary.platform_count.toLocaleString()}</span>
                                </div>
                            </div>

                            {/* 총 정산 금액 */}
                            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="p-2 bg-green-500/20 rounded-lg">
                                        <DollarSign className="w-6 h-6 text-green-400" />
                                    </div>
                                </div>
                                <p className="text-sm text-slate-400 mb-1">총 정산 금액</p>
                                <p className="text-3xl font-bold text-white">
                                    {statsData.summary.total_amount.toLocaleString()} P
                                </p>
                                <div className="mt-2 flex items-center text-sm">
                                    <span className="text-green-400">{statsData.summary.advertiser_amount.toLocaleString()} P</span>
                                    <span className="text-slate-500 mx-2">|</span>
                                    <span className="text-yellow-400">{statsData.summary.platform_amount.toLocaleString()} P</span>
                                </div>
                            </div>

                            {/* 플랫폼 정산 건수 */}
                            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="p-2 bg-yellow-500/20 rounded-lg">
                                        <Building2 className="w-6 h-6 text-yellow-400" />
                                    </div>
                                </div>
                                <p className="text-sm text-slate-400 mb-1">플랫폼 정산 (매칭 실패)</p>
                                <p className="text-3xl font-bold text-yellow-400">
                                    {statsData.summary.platform_count.toLocaleString()} 건
                                </p>
                                <p className="mt-2 text-sm text-slate-400">
                                    총 {statsData.summary.platform_amount.toLocaleString()} P 지급
                                </p>
                            </div>

                            {/* 매칭 실패율 */}
                            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="p-2 bg-red-500/20 rounded-lg">
                                        <Percent className="w-6 h-6 text-red-400" />
                                    </div>
                                </div>
                                <p className="text-sm text-slate-400 mb-1">매칭 실패율</p>
                                <p className="text-3xl font-bold text-white">
                                    {statsData.summary.platform_ratio}%
                                </p>
                                <div className="mt-2">
                                    <div className="w-full bg-slate-700 rounded-full h-2">
                                        <div
                                            className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
                                            style={{ width: `${Math.min(statsData.summary.platform_ratio, 100)}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 탭 네비게이션 */}
                        <div className="flex space-x-4 mb-6 border-b border-slate-700">
                            <button
                                onClick={() => setActiveTab('overview')}
                                className={`pb-3 px-1 font-medium transition-colors ${
                                    activeTab === 'overview'
                                        ? 'text-blue-400 border-b-2 border-blue-400'
                                        : 'text-slate-400 hover:text-white'
                                }`}
                            >
                                <div className="flex items-center space-x-2">
                                    <TrendingUp className="w-4 h-4" />
                                    <span>일별 추이</span>
                                </div>
                            </button>
                            <button
                                onClick={() => setActiveTab('users')}
                                className={`pb-3 px-1 font-medium transition-colors ${
                                    activeTab === 'users'
                                        ? 'text-blue-400 border-b-2 border-blue-400'
                                        : 'text-slate-400 hover:text-white'
                                }`}
                            >
                                <div className="flex items-center space-x-2">
                                    <Users className="w-4 h-4" />
                                    <span>사용자별 내역</span>
                                </div>
                            </button>
                        </div>

                        {/* 일별 추이 차트 */}
                        {activeTab === 'overview' && (
                            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-8">
                                <h3 className="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
                                    <Calendar className="w-5 h-5 text-blue-400" />
                                    <span>일별 정산 추이</span>
                                </h3>
                                
                                {statsData.daily_trend.length === 0 ? (
                                    <div className="text-center py-12">
                                        <BarChart3 className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                                        <p className="text-slate-400">해당 기간에 데이터가 없습니다.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {/* 범례 */}
                                        <div className="flex items-center justify-end space-x-6 text-sm">
                                            <div className="flex items-center space-x-2">
                                                <div className="w-3 h-3 bg-green-500 rounded" />
                                                <span className="text-slate-400">광고주 정산</span>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                                <div className="w-3 h-3 bg-yellow-500 rounded" />
                                                <span className="text-slate-400">플랫폼 정산</span>
                                            </div>
                                        </div>

                                        {/* 차트 */}
                                        <div className="flex items-end space-x-2 h-48 overflow-x-auto pb-4">
                                            {[...statsData.daily_trend].reverse().map((day, idx) => {
                                                const totalHeight = ((day.platform_count + day.advertiser_count) / maxDailyCount) * 100
                                                const platformHeight = (day.platform_count / (day.platform_count + day.advertiser_count || 1)) * totalHeight
                                                const advertiserHeight = totalHeight - platformHeight

                                                return (
                                                    <div key={idx} className="flex flex-col items-center min-w-[40px] group">
                                                        <div className="flex flex-col-reverse w-8 h-40 relative">
                                                            {/* 광고주 정산 (아래) */}
                                                            <div
                                                                className="w-full bg-green-500 rounded-t transition-all duration-300"
                                                                style={{ height: `${advertiserHeight}%` }}
                                                            />
                                                            {/* 플랫폼 정산 (위) */}
                                                            <div
                                                                className="w-full bg-yellow-500 transition-all duration-300"
                                                                style={{ height: `${platformHeight}%` }}
                                                            />
                                                            
                                                            {/* 툴팁 */}
                                                            <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 bg-slate-700 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                                                <p>광고주: {day.advertiser_count}건 ({day.advertiser_amount.toLocaleString()}P)</p>
                                                                <p>플랫폼: {day.platform_count}건 ({day.platform_amount.toLocaleString()}P)</p>
                                                            </div>
                                                        </div>
                                                        <span className="text-xs text-slate-500 mt-2">{formatDate(day.date)}</span>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 사용자별 내역 */}
                        {activeTab === 'users' && (
                            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                                <div className="p-4 border-b border-slate-700">
                                    <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                                        <Users className="w-5 h-5 text-blue-400" />
                                        <span>사용자별 플랫폼 정산 내역</span>
                                    </h3>
                                    <p className="text-sm text-slate-400 mt-1">
                                        매칭 실패 시 플랫폼 200원을 받은 사용자 목록
                                    </p>
                                </div>

                                {/* 테이블 */}
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-slate-700/50">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                                                    사용자
                                                </th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                                                    플랫폼 정산 횟수
                                                </th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                                                    총 금액
                                                </th>
                                                <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                                                    마지막 정산
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-700">
                                            {(usersData?.users || statsData.top_users).map((user, idx) => (
                                                <tr key={user.user_id} className="hover:bg-slate-700/30 transition-colors">
                                                    <td className="px-4 py-4">
                                                        <div className="flex items-center space-x-3">
                                                            <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center text-sm font-medium text-white">
                                                                {idx + 1 + (usersData ? (usersData.page - 1) * usersData.page_size : 0)}
                                                            </div>
                                                            <div>
                                                                <p className="text-white font-medium">{user.username}</p>
                                                                <p className="text-slate-400 text-sm">{user.email}</p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-4 text-right">
                                                        <span className="text-yellow-400 font-semibold">
                                                            {user.platform_count.toLocaleString()} 회
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-4 text-right">
                                                        <span className="text-white font-semibold">
                                                            {user.platform_amount.toLocaleString()} P
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-4 text-right text-slate-400 text-sm">
                                                        {formatDateTime(user.last_settlement_date)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* 페이지네이션 */}
                                {usersData && usersData.total_pages > 1 && (
                                    <div className="p-4 border-t border-slate-700 flex items-center justify-between">
                                        <p className="text-sm text-slate-400">
                                            총 {usersData.total.toLocaleString()}명 중 {((usersData.page - 1) * usersData.page_size) + 1}-
                                            {Math.min(usersData.page * usersData.page_size, usersData.total)}명 표시
                                        </p>
                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => handlePageChange(currentPage - 1)}
                                                disabled={currentPage === 1}
                                                className="p-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                <ChevronLeft className="w-5 h-5" />
                                            </button>
                                            <span className="text-slate-300">
                                                {currentPage} / {usersData.total_pages}
                                            </span>
                                            <button
                                                onClick={() => handlePageChange(currentPage + 1)}
                                                disabled={currentPage === usersData.total_pages}
                                                className="p-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                <ChevronRight className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {(usersData?.users.length === 0 && statsData.top_users.length === 0) && (
                                    <div className="p-12 text-center">
                                        <Users className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                                        <p className="text-slate-400">해당 기간에 플랫폼 정산 내역이 없습니다.</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    )
}

