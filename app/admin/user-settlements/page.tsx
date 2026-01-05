'use client'

import {
    AlertCircle,
    CheckCircle,
    ChevronLeft,
    ChevronRight,
    Clock,
    DollarSign,
    Download,
    Filter,
    RefreshCw,
    Search,
    TrendingUp,
    Users,
    Wallet,
    XCircle
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'

interface Summary {
    total_users: number
    total_earnings: number
    total_withdrawn: number
    pending_withdrawals: number
    active_users_today: number
    new_users_week: number
}

interface UserItem {
    user_id: number
    username: string
    email: string
    total_earnings: number
    quality_score: number
    created_at: string
    last_activity: string | null
    transaction_count: number
}

interface TransactionItem {
    id: string
    user_id: number
    username: string
    amount: number
    type: string
    status: string
    created_at: string
    buyer_name: string | null
}

interface WithdrawalItem {
    id: string
    user_id: number
    username: string
    email: string
    request_amount: number
    tax_amount: number
    final_amount: number
    bank_name: string
    account_number: string
    account_holder: string
    status: string
    created_at: string
}

type TabType = 'overview' | 'users' | 'transactions' | 'withdrawals'

export default function UserSettlementsPage() {
    const [summary, setSummary] = useState<Summary | null>(null)
    const [users, setUsers] = useState<UserItem[]>([])
    const [transactions, setTransactions] = useState<TransactionItem[]>([])
    const [withdrawals, setWithdrawals] = useState<WithdrawalItem[]>([])
    
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [activeTab, setActiveTab] = useState<TabType>('overview')
    const [isRefreshing, setIsRefreshing] = useState(false)
    
    // 페이지네이션
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal] = useState(0)
    
    // 필터
    const [searchQuery, setSearchQuery] = useState('')
    const [sortBy, setSortBy] = useState('earnings')
    const [typeFilter, setTypeFilter] = useState('')
    const [statusFilter, setStatusFilter] = useState('')
    
    // 처리 중 상태
    const [processingId, setProcessingId] = useState<string | null>(null)
    
    const router = useRouter()

    const getToken = () => localStorage.getItem('adminToken')

    const fetchSummary = useCallback(async () => {
        const token = getToken()
        if (!token) {
            router.push('/admin/login')
            return
        }

        try {
            const response = await fetch('/api/admin/user-settlements?endpoint=summary', {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('adminToken')
                    router.push('/admin/login')
                    return
                }
                throw new Error('요약 데이터 로드 실패')
            }

            const result = await response.json()
            if (result.success) {
                setSummary(result.data)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '알 수 없는 오류')
        }
    }, [router])

    const fetchUsers = useCallback(async (page: number = 1) => {
        const token = getToken()
        if (!token) return

        try {
            const params = new URLSearchParams({
                endpoint: 'users',
                page: String(page),
                pageSize: '20',
                sortBy,
                ...(searchQuery && { search: searchQuery })
            })

            const response = await fetch(`/api/admin/user-settlements?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (response.ok) {
                const result = await response.json()
                if (result.success) {
                    setUsers(result.data.users)
                    setTotalPages(result.data.total_pages)
                    setTotal(result.data.total)
                }
            }
        } catch (err) {
            console.error('Users fetch error:', err)
        }
    }, [sortBy, searchQuery])

    const fetchTransactions = useCallback(async (page: number = 1) => {
        const token = getToken()
        if (!token) return

        try {
            const params = new URLSearchParams({
                endpoint: 'transactions',
                page: String(page),
                pageSize: '20',
                ...(typeFilter && { typeFilter })
            })

            const response = await fetch(`/api/admin/user-settlements?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (response.ok) {
                const result = await response.json()
                if (result.success) {
                    setTransactions(result.data.transactions)
                    setTotalPages(result.data.total_pages)
                    setTotal(result.data.total)
                }
            }
        } catch (err) {
            console.error('Transactions fetch error:', err)
        }
    }, [typeFilter])

    const fetchWithdrawals = useCallback(async (page: number = 1) => {
        const token = getToken()
        if (!token) return

        try {
            const params = new URLSearchParams({
                endpoint: 'withdrawals',
                page: String(page),
                pageSize: '20',
                ...(statusFilter && { statusFilter })
            })

            const response = await fetch(`/api/admin/user-settlements?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (response.ok) {
                const result = await response.json()
                if (result.success) {
                    setWithdrawals(result.data.withdrawals)
                    setTotalPages(result.data.total_pages)
                    setTotal(result.data.total)
                }
            }
        } catch (err) {
            console.error('Withdrawals fetch error:', err)
        }
    }, [statusFilter])

    const handleWithdrawalAction = async (withdrawalId: string, action: 'approve' | 'reject') => {
        const token = getToken()
        if (!token) return

        setProcessingId(withdrawalId)

        try {
            const response = await fetch('/api/admin/user-settlements', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action, withdrawalId })
            })

            const result = await response.json()

            if (result.success) {
                alert(action === 'approve' ? '출금이 승인되었습니다.' : '출금이 거절되었습니다.')
                fetchWithdrawals(currentPage)
                fetchSummary()
            } else {
                alert(result.error || '처리 실패')
            }
        } catch (err) {
            alert('처리 중 오류가 발생했습니다.')
        } finally {
            setProcessingId(null)
        }
    }

    const handleRefresh = async () => {
        setIsRefreshing(true)
        setError(null)
        await fetchSummary()
        
        switch (activeTab) {
            case 'users':
                await fetchUsers(currentPage)
                break
            case 'transactions':
                await fetchTransactions(currentPage)
                break
            case 'withdrawals':
                await fetchWithdrawals(currentPage)
                break
        }
        
        setIsRefreshing(false)
    }

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true)
            await fetchSummary()
            setIsLoading(false)
        }
        loadData()
    }, [fetchSummary])

    useEffect(() => {
        setCurrentPage(1)
        switch (activeTab) {
            case 'users':
                fetchUsers(1)
                break
            case 'transactions':
                fetchTransactions(1)
                break
            case 'withdrawals':
                fetchWithdrawals(1)
                break
        }
    }, [activeTab, fetchUsers, fetchTransactions, fetchWithdrawals])

    const handlePageChange = (page: number) => {
        setCurrentPage(page)
        switch (activeTab) {
            case 'users':
                fetchUsers(page)
                break
            case 'transactions':
                fetchTransactions(page)
                break
            case 'withdrawals':
                fetchWithdrawals(page)
                break
        }
    }

    const formatDateTime = (dateStr: string | null) => {
        if (!dateStr) return '-'
        return new Date(dateStr).toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'COMPLETED':
                return <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">완료</span>
            case 'REQUESTED':
                return <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">대기중</span>
            case 'REJECTED':
                return <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">거절</span>
            default:
                return <span className="px-2 py-1 bg-slate-500/20 text-slate-400 rounded text-xs">{status}</span>
        }
    }

    const getTypeBadge = (type: string) => {
        switch (type) {
            case 'PLATFORM':
                return <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">플랫폼</span>
            case 'ADVERTISER':
                return <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">광고주</span>
            default:
                return <span className="px-2 py-1 bg-slate-500/20 text-slate-400 rounded text-xs">{type}</span>
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                    <p className="text-slate-300">사용자 정산 데이터 로딩 중...</p>
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
                                <Users className="w-6 h-6" />
                            </Link>
                            <div>
                                <h1 className="text-xl font-bold text-white">사용자 정산 관리</h1>
                                <p className="text-sm text-slate-400">사용자별 적립금 및 출금 관리</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link
                                href="/admin/platform-settlements"
                                className="px-3 py-1.5 text-yellow-400 hover:text-yellow-300 transition-colors text-sm"
                            >
                                플랫폼 정산
                            </Link>
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

                {/* 요약 카드 */}
                {summary && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-blue-500/20 rounded-lg">
                                    <Users className="w-5 h-5 text-blue-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">총 사용자</p>
                            <p className="text-2xl font-bold text-white">{summary.total_users.toLocaleString()}</p>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-green-500/20 rounded-lg">
                                    <DollarSign className="w-5 h-5 text-green-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">총 적립금</p>
                            <p className="text-2xl font-bold text-green-400">{summary.total_earnings.toLocaleString()} P</p>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-purple-500/20 rounded-lg">
                                    <Wallet className="w-5 h-5 text-purple-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">총 출금액</p>
                            <p className="text-2xl font-bold text-purple-400">{summary.total_withdrawn.toLocaleString()} P</p>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-yellow-500/20 rounded-lg">
                                    <Clock className="w-5 h-5 text-yellow-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">출금 대기</p>
                            <p className="text-2xl font-bold text-yellow-400">{summary.pending_withdrawals.toLocaleString()} P</p>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-cyan-500/20 rounded-lg">
                                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">오늘 활동</p>
                            <p className="text-2xl font-bold text-cyan-400">{summary.active_users_today.toLocaleString()}명</p>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                            <div className="flex items-center justify-between mb-3">
                                <div className="p-2 bg-pink-500/20 rounded-lg">
                                    <Users className="w-5 h-5 text-pink-400" />
                                </div>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">신규 (7일)</p>
                            <p className="text-2xl font-bold text-pink-400">{summary.new_users_week.toLocaleString()}명</p>
                        </div>
                    </div>
                )}

                {/* 탭 네비게이션 */}
                <div className="flex space-x-4 mb-6 border-b border-slate-700">
                    {[
                        { key: 'overview', label: '개요', icon: TrendingUp },
                        { key: 'users', label: '사용자별 적립금', icon: Users },
                        { key: 'transactions', label: '정산 내역', icon: DollarSign },
                        { key: 'withdrawals', label: '출금 요청', icon: Wallet },
                    ].map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => setActiveTab(key as TabType)}
                            className={`pb-3 px-1 font-medium transition-colors flex items-center space-x-2 ${
                                activeTab === key
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{label}</span>
                        </button>
                    ))}
                </div>

                {/* 사용자별 적립금 */}
                {activeTab === 'users' && (
                    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                        {/* 필터 */}
                        <div className="p-4 border-b border-slate-700 flex flex-wrap gap-4">
                            <div className="flex-1 min-w-[200px]">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                                    <input
                                        type="text"
                                        placeholder="사용자명 또는 이메일 검색..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && fetchUsers(1)}
                                        className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                                    />
                                </div>
                            </div>
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="earnings">적립금순</option>
                                <option value="recent">최근가입순</option>
                                <option value="quality">품질점수순</option>
                            </select>
                        </div>

                        {/* 테이블 */}
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-700/50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">사용자</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">적립금</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">품질점수</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">정산 횟수</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">마지막 활동</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {users.map((user) => (
                                        <tr key={user.user_id} className="hover:bg-slate-700/30">
                                            <td className="px-4 py-4">
                                                <div>
                                                    <p className="text-white font-medium">{user.username}</p>
                                                    <p className="text-slate-400 text-sm">{user.email}</p>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <span className="text-green-400 font-semibold">{user.total_earnings.toLocaleString()} P</span>
                                            </td>
                                            <td className="px-4 py-4 text-center">
                                                <span className={`font-medium ${user.quality_score >= 70 ? 'text-green-400' : user.quality_score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                                                    {user.quality_score}
                                                </span>
                                            </td>
                                            <td className="px-4 py-4 text-right text-slate-300">{user.transaction_count}회</td>
                                            <td className="px-4 py-4 text-right text-slate-400 text-sm">{formatDateTime(user.last_activity)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* 페이지네이션 */}
                        {totalPages > 1 && (
                            <div className="p-4 border-t border-slate-700 flex items-center justify-between">
                                <p className="text-sm text-slate-400">총 {total.toLocaleString()}명</p>
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => handlePageChange(currentPage - 1)}
                                        disabled={currentPage === 1}
                                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                                    >
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <span className="text-slate-300">{currentPage} / {totalPages}</span>
                                    <button
                                        onClick={() => handlePageChange(currentPage + 1)}
                                        disabled={currentPage === totalPages}
                                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                                    >
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 정산 내역 */}
                {activeTab === 'transactions' && (
                    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 flex items-center space-x-4">
                            <Filter className="w-4 h-4 text-slate-400" />
                            <select
                                value={typeFilter}
                                onChange={(e) => setTypeFilter(e.target.value)}
                                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="">전체 타입</option>
                                <option value="ADVERTISER">광고주</option>
                                <option value="PLATFORM">플랫폼</option>
                            </select>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-700/50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">사용자</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">광고주</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">타입</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">금액</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">상태</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">일시</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {transactions.map((tx) => (
                                        <tr key={tx.id} className="hover:bg-slate-700/30">
                                            <td className="px-4 py-4 text-white">{tx.username}</td>
                                            <td className="px-4 py-4 text-slate-300">{tx.buyer_name || '-'}</td>
                                            <td className="px-4 py-4 text-center">{getTypeBadge(tx.type)}</td>
                                            <td className="px-4 py-4 text-right text-green-400 font-semibold">{tx.amount.toLocaleString()} P</td>
                                            <td className="px-4 py-4 text-center">{getStatusBadge(tx.status)}</td>
                                            <td className="px-4 py-4 text-right text-slate-400 text-sm">{formatDateTime(tx.created_at)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {totalPages > 1 && (
                            <div className="p-4 border-t border-slate-700 flex items-center justify-between">
                                <p className="text-sm text-slate-400">총 {total.toLocaleString()}건</p>
                                <div className="flex items-center space-x-2">
                                    <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="p-2 text-slate-400 hover:text-white disabled:opacity-50">
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <span className="text-slate-300">{currentPage} / {totalPages}</span>
                                    <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className="p-2 text-slate-400 hover:text-white disabled:opacity-50">
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 출금 요청 */}
                {activeTab === 'withdrawals' && (
                    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 flex items-center space-x-4">
                            <Filter className="w-4 h-4 text-slate-400" />
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="">전체 상태</option>
                                <option value="REQUESTED">대기중</option>
                                <option value="COMPLETED">완료</option>
                                <option value="REJECTED">거절</option>
                            </select>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-700/50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">사용자</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">계좌정보</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">요청액</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">세금</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">실지급액</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">상태</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase">액션</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {withdrawals.map((wd) => (
                                        <tr key={wd.id} className="hover:bg-slate-700/30">
                                            <td className="px-4 py-4">
                                                <p className="text-white font-medium">{wd.username}</p>
                                                <p className="text-slate-400 text-sm">{wd.email}</p>
                                            </td>
                                            <td className="px-4 py-4">
                                                <p className="text-slate-300">{wd.bank_name}</p>
                                                <p className="text-slate-400 text-sm">{wd.account_number} ({wd.account_holder})</p>
                                            </td>
                                            <td className="px-4 py-4 text-right text-white">{wd.request_amount.toLocaleString()} P</td>
                                            <td className="px-4 py-4 text-right text-red-400">-{wd.tax_amount.toLocaleString()} P</td>
                                            <td className="px-4 py-4 text-right text-green-400 font-semibold">{wd.final_amount.toLocaleString()} P</td>
                                            <td className="px-4 py-4 text-center">{getStatusBadge(wd.status)}</td>
                                            <td className="px-4 py-4 text-center">
                                                {wd.status === 'REQUESTED' ? (
                                                    <div className="flex items-center justify-center space-x-2">
                                                        <button
                                                            onClick={() => handleWithdrawalAction(wd.id, 'approve')}
                                                            disabled={processingId === wd.id}
                                                            className="p-1.5 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 disabled:opacity-50"
                                                            title="승인"
                                                        >
                                                            <CheckCircle className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => handleWithdrawalAction(wd.id, 'reject')}
                                                            disabled={processingId === wd.id}
                                                            className="p-1.5 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 disabled:opacity-50"
                                                            title="거절"
                                                        >
                                                            <XCircle className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <span className="text-slate-500 text-sm">-</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {withdrawals.length === 0 && (
                            <div className="p-12 text-center">
                                <Wallet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                                <p className="text-slate-400">출금 요청이 없습니다.</p>
                            </div>
                        )}

                        {totalPages > 1 && (
                            <div className="p-4 border-t border-slate-700 flex items-center justify-between">
                                <p className="text-sm text-slate-400">총 {total.toLocaleString()}건</p>
                                <div className="flex items-center space-x-2">
                                    <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="p-2 text-slate-400 hover:text-white disabled:opacity-50">
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <span className="text-slate-300">{currentPage} / {totalPages}</span>
                                    <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className="p-2 text-slate-400 hover:text-white disabled:opacity-50">
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 개요 탭 */}
                {activeTab === 'overview' && summary && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                                <DollarSign className="w-5 h-5 text-green-400" />
                                <span>적립금 현황</span>
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">총 적립금</span>
                                    <span className="text-white font-semibold">{summary.total_earnings.toLocaleString()} P</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">총 출금액</span>
                                    <span className="text-purple-400 font-semibold">{summary.total_withdrawn.toLocaleString()} P</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">출금 대기</span>
                                    <span className="text-yellow-400 font-semibold">{summary.pending_withdrawals.toLocaleString()} P</span>
                                </div>
                                <hr className="border-slate-700" />
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-300 font-medium">현재 보유 잔액</span>
                                    <span className="text-green-400 font-bold text-xl">
                                        {(summary.total_earnings - summary.total_withdrawn - summary.pending_withdrawals).toLocaleString()} P
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                                <Users className="w-5 h-5 text-blue-400" />
                                <span>사용자 현황</span>
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">총 사용자</span>
                                    <span className="text-white font-semibold">{summary.total_users.toLocaleString()}명</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">오늘 활동 사용자</span>
                                    <span className="text-cyan-400 font-semibold">{summary.active_users_today.toLocaleString()}명</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">신규 가입 (7일)</span>
                                    <span className="text-pink-400 font-semibold">{summary.new_users_week.toLocaleString()}명</span>
                                </div>
                                <hr className="border-slate-700" />
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-300 font-medium">평균 적립금</span>
                                    <span className="text-green-400 font-bold">
                                        {summary.total_users > 0 
                                            ? Math.round(summary.total_earnings / summary.total_users).toLocaleString() 
                                            : 0} P
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}

