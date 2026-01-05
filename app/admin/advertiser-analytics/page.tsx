'use client'

import {
    AlertCircle,
    ArrowDownRight,
    ArrowUpRight,
    BarChart3,
    Building2,
    CheckCircle,
    Clock,
    DollarSign,
    MoreVertical,
    RefreshCw,
    Trash2,
    TrendingUp,
    Users
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'

interface AdvertiserData {
    advertiser_id: number
    company_name: string
    email: string
    website_url: string | null
    review_status: string
    daily_budget: number
    is_enabled: boolean
    created_at: string
    total_bids: number
    total_spend: number
    total_settlements: number
    total_payable: number
    success_rate: number
    avg_bid_price: number
    avg_dwell_time: number
    last_bid_date: string | null
    passed_count: number
    partial_count: number
    failed_count: number
}

interface Summary {
    total_advertisers: number
    active_advertisers: number
    pending_advertisers: number
    rejected_advertisers: number
    total_bids: number
    total_spend: number
    total_settlements: number
    avg_success_rate: number
    avg_bid_price: number
}

export default function AdvertiserAnalyticsPage() {
    const [advertisers, setAdvertisers] = useState<AdvertiserData[]>([])
    const [summary, setSummary] = useState<Summary | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week')
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [sortBy, setSortBy] = useState<'spend' | 'bids' | 'success' | 'name'>('spend')
    const [filterStatus, setFilterStatus] = useState<'all' | 'approved' | 'pending' | 'rejected'>('all')
    const [openMenuId, setOpenMenuId] = useState<number | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const router = useRouter()

    // 광고주 삭제 함수
    const handleDeleteAdvertiser = async (advertiserId: number, companyName: string) => {
        if (!confirm(`정말로 "${companyName}" 광고주를 삭제하시겠습니까?\n\n⚠️ 이 작업은 되돌릴 수 없으며, 관련된 모든 데이터가 삭제됩니다.`)) {
            return
        }

        const token = localStorage.getItem('adminToken')
        if (!token) {
            router.push('/admin/login')
            return
        }

        setIsDeleting(true)
        try {
            const response = await fetch(`/api/admin/advertiser-review/${advertiserId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.error || 'Failed to delete advertiser')
            }

            // 성공 시 목록에서 제거
            setAdvertisers(prev => prev.filter(adv => adv.advertiser_id !== advertiserId))
            alert(`"${companyName}" 광고주가 삭제되었습니다.`)
        } catch (err) {
            alert(err instanceof Error ? err.message : '삭제에 실패했습니다.')
        } finally {
            setIsDeleting(false)
            setOpenMenuId(null)
        }
    }

    const fetchAnalytics = useCallback(async () => {
        const token = localStorage.getItem('adminToken')
        if (!token) {
            router.push('/admin/login')
            return
        }

        try {
            const response = await fetch(`/api/admin/advertiser-analytics?timeRange=${timeRange}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            })

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('adminToken')
                    router.push('/admin/login')
                    return
                }
                throw new Error('Failed to fetch analytics')
            }

            const data = await response.json()
            setSummary(data.summary)
            setAdvertisers(data.advertisers || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [timeRange, router])

    useEffect(() => {
        fetchAnalytics()
    }, [fetchAnalytics])

    const handleRefresh = () => {
        setIsRefreshing(true)
        fetchAnalytics()
    }

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('ko-KR').format(num)
    }

    const formatDate = (dateString: string | null) => {
        if (!dateString) return '-'
        return new Date(dateString).toLocaleDateString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'approved':
                return <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">승인됨</span>
            case 'pending':
                return <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">대기중</span>
            case 'rejected':
                return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">거절됨</span>
            default:
                return <span className="px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400">{status}</span>
        }
    }

    const getSuccessRateColor = (rate: number) => {
        if (rate >= 70) return 'text-green-400'
        if (rate >= 40) return 'text-yellow-400'
        return 'text-red-400'
    }

    // 필터링 및 정렬
    const filteredAdvertisers = advertisers
        .filter(adv => filterStatus === 'all' || adv.review_status === filterStatus)
        .sort((a, b) => {
            switch (sortBy) {
                case 'spend':
                    return b.total_spend - a.total_spend
                case 'bids':
                    return b.total_bids - a.total_bids
                case 'success':
                    return b.success_rate - a.success_rate
                case 'name':
                    return a.company_name.localeCompare(b.company_name)
                default:
                    return 0
            }
        })

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-900">
            {/* Header */}
            <div className="bg-slate-800/50 border-b border-slate-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                <BarChart3 className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-100">광고주 현황 분석</h1>
                                <p className="text-slate-400">전체 광고주의 성과 및 정산 현황</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link
                                href="/admin/user-settlements"
                                className="px-4 py-2 text-green-400 hover:text-green-300 transition-colors"
                            >
                                사용자 정산
                            </Link>
                            <Link
                                href="/admin/platform-settlements"
                                className="px-4 py-2 text-yellow-400 hover:text-yellow-300 transition-colors"
                            >
                                플랫폼 정산
                            </Link>
                            <Link
                                href="/admin/advertiser-review"
                                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                            >
                                심사 관리
                            </Link>
                            <button
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                                className="flex items-center space-x-2 px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 disabled:opacity-50 transition-colors"
                            >
                                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                                <span>새로고침</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                            <AlertCircle className="w-5 h-5 text-red-400" />
                            <p className="text-red-400">{error}</p>
                        </div>
                    </div>
                )}

                {/* Summary Cards */}
                {summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
                        <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                    <Users className="w-5 h-5 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-100">{summary.total_advertisers}</p>
                                    <p className="text-xs text-slate-400">전체 광고주</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                                    <CheckCircle className="w-5 h-5 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-100">{summary.active_advertisers}</p>
                                    <p className="text-xs text-slate-400">활성 광고주</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                    <DollarSign className="w-5 h-5 text-purple-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-100">{formatNumber(summary.total_spend)}</p>
                                    <p className="text-xs text-slate-400">총 지출 (P)</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                                    <TrendingUp className="w-5 h-5 text-orange-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-100">{summary.total_bids}</p>
                                    <p className="text-xs text-slate-400">총 입찰 수</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                                    <BarChart3 className="w-5 h-5 text-cyan-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-100">{summary.avg_success_rate}%</p>
                                    <p className="text-xs text-slate-400">평균 성공률</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-4 mb-6">
                    {/* Time Range */}
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-400">기간:</span>
                        <div className="flex bg-slate-800 rounded-lg p-1">
                            {(['day', 'week', 'month'] as const).map((range) => (
                                <button
                                    key={range}
                                    onClick={() => setTimeRange(range)}
                                    className={`px-3 py-1 text-sm rounded-md transition-colors ${timeRange === range
                                        ? 'bg-blue-600 text-white'
                                        : 'text-slate-400 hover:text-white'
                                        }`}
                                >
                                    {range === 'day' ? '1일' : range === 'week' ? '1주' : '1개월'}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Status Filter */}
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-400">상태:</span>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value as typeof filterStatus)}
                            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">전체</option>
                            <option value="approved">승인됨</option>
                            <option value="pending">대기중</option>
                            <option value="rejected">거절됨</option>
                        </select>
                    </div>

                    {/* Sort */}
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-400">정렬:</span>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="spend">지출순</option>
                            <option value="bids">입찰수순</option>
                            <option value="success">성공률순</option>
                            <option value="name">이름순</option>
                        </select>
                    </div>
                </div>

                {/* Advertisers Table */}
                <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-slate-800/50 border-b border-slate-700">
                                    <th className="text-left px-6 py-4 text-sm font-medium text-slate-300">광고주</th>
                                    <th className="text-left px-4 py-4 text-sm font-medium text-slate-300">상태</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">일일예산</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">총 입찰</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">총 지출</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">정산 건수</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">성공률</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">평균 체류</th>
                                    <th className="text-right px-4 py-4 text-sm font-medium text-slate-300">최근 입찰</th>
                                    <th className="text-center px-4 py-4 text-sm font-medium text-slate-300">작업</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredAdvertisers.length === 0 ? (
                                    <tr>
                                        <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                                            광고주 데이터가 없습니다.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredAdvertisers.map((adv) => (
                                        <tr key={adv.advertiser_id} className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center space-x-3">
                                                    <div className="w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center">
                                                        <Building2 className="w-4 h-4 text-slate-400" />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-slate-100">{adv.company_name}</p>
                                                        <p className="text-xs text-slate-500">{adv.email}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4">
                                                {getStatusBadge(adv.review_status)}
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <span className="text-sm text-slate-300">{formatNumber(adv.daily_budget)}P</span>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <span className="text-sm text-slate-300">{formatNumber(adv.total_bids)}</span>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <span className="text-sm font-medium text-purple-400">{formatNumber(adv.total_spend)}P</span>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <div className="flex items-center justify-end space-x-2">
                                                    <span className="text-sm text-slate-300">{adv.total_settlements}</span>
                                                    {adv.total_settlements > 0 && (
                                                        <div className="flex text-xs">
                                                            <span className="text-green-400">{adv.passed_count}</span>
                                                            <span className="text-slate-500">/</span>
                                                            <span className="text-yellow-400">{adv.partial_count}</span>
                                                            <span className="text-slate-500">/</span>
                                                            <span className="text-red-400">{adv.failed_count}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <div className="flex items-center justify-end space-x-1">
                                                    <span className={`text-sm font-medium ${getSuccessRateColor(adv.success_rate)}`}>
                                                        {adv.success_rate}%
                                                    </span>
                                                    {adv.success_rate >= 50 ? (
                                                        <ArrowUpRight className="w-3 h-3 text-green-400" />
                                                    ) : adv.success_rate > 0 ? (
                                                        <ArrowDownRight className="w-3 h-3 text-red-400" />
                                                    ) : null}
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <div className="flex items-center justify-end space-x-1">
                                                    <Clock className="w-3 h-3 text-slate-500" />
                                                    <span className="text-sm text-slate-400">{adv.avg_dwell_time}s</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <span className="text-xs text-slate-500">{formatDate(adv.last_bid_date)}</span>
                                            </td>
                                            <td className="px-4 py-4 text-center relative">
                                                <div className="relative inline-block">
                                                    <button
                                                        onClick={() => setOpenMenuId(openMenuId === adv.advertiser_id ? null : adv.advertiser_id)}
                                                        className="p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-700 transition-colors"
                                                    >
                                                        <MoreVertical className="w-4 h-4" />
                                                    </button>
                                                    {openMenuId === adv.advertiser_id && (
                                                        <div className="absolute right-0 mt-1 w-36 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
                                                            <button
                                                                onClick={() => handleDeleteAdvertiser(adv.advertiser_id, adv.company_name)}
                                                                disabled={isDeleting}
                                                                className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                                <span>삭제</span>
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Legend */}
                <div className="mt-4 flex items-center justify-end space-x-6 text-xs text-slate-500">
                    <div className="flex items-center space-x-1">
                        <span className="w-2 h-2 rounded-full bg-green-400"></span>
                        <span>PASSED</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
                        <span>PARTIAL</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <span className="w-2 h-2 rounded-full bg-red-400"></span>
                        <span>FAILED</span>
                    </div>
                </div>
            </div>
        </div>
    )
}

