'use client'

import { BarChart3, Clock, DollarSign, Target, TrendingDown, TrendingUp } from 'lucide-react'
import { useState } from 'react'

interface BidHistoryItem {
    id: string
    searchQuery: string
    bidAmount: number
    result: 'won' | 'lost' | 'pending'
    timestamp: string
    matchScore: number
    qualityScore: number
    isAutoBid: boolean
}

interface BidHistoryProps {
    bidHistory: BidHistoryItem[]
    isLoading?: boolean
}

export default function BidHistory({ bidHistory, isLoading = false }: BidHistoryProps) {
    const [filter, setFilter] = useState<'all' | 'auto' | 'manual'>('all')
    const [resultFilter, setResultFilter] = useState<'all' | 'won' | 'lost'>('all')
    const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month'>('week')

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('ko-KR').format(amount)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getResultColor = (result: string) => {
        switch (result) {
            case 'won': return 'text-green-400'
            case 'lost': return 'text-red-400'
            case 'pending': return 'text-yellow-400'
            default: return 'text-slate-400'
        }
    }

    const getResultIcon = (result: string) => {
        switch (result) {
            case 'won': return <TrendingUp className="w-4 h-4" />
            case 'lost': return <TrendingDown className="w-4 h-4" />
            case 'pending': return <Clock className="w-4 h-4" />
            default: return <Target className="w-4 h-4" />
        }
    }

    const filteredHistory = bidHistory.filter(bid => {
        // 필터 조건 적용
        if (filter === 'auto' && !bid.isAutoBid) return false
        if (filter === 'manual' && bid.isAutoBid) return false
        if (resultFilter === 'won' && bid.result !== 'won') return false
        if (resultFilter === 'lost' && bid.result !== 'lost') return false

        // 시간 범위 필터
        const bidDate = new Date(bid.timestamp)
        const now = new Date()
        const diffTime = now.getTime() - bidDate.getTime()
        const diffDays = diffTime / (1000 * 60 * 60 * 24)

        if (timeRange === 'today' && diffDays > 1) return false
        if (timeRange === 'week' && diffDays > 7) return false
        if (timeRange === 'month' && diffDays > 30) return false

        return true
    })

    // 통계 계산
    const totalBids = filteredHistory.length
    const wonBids = filteredHistory.filter(bid => bid.result === 'won').length
    const lostBids = filteredHistory.filter(bid => bid.result === 'lost').length
    const pendingBids = filteredHistory.filter(bid => bid.result === 'pending').length
    const successRate = totalBids > 0 ? (wonBids / totalBids) * 100 : 0
    const totalSpent = filteredHistory.filter(bid => bid.result === 'won').reduce((sum, bid) => sum + bid.bidAmount, 0)
    const averageBidAmount = totalBids > 0 ? filteredHistory.reduce((sum, bid) => sum + bid.bidAmount, 0) / totalBids : 0
    const autoBidCount = filteredHistory.filter(bid => bid.isAutoBid).length
    const manualBidCount = filteredHistory.filter(bid => !bid.isAutoBid).length

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-slate-100">입찰 내역</h3>
                    <p className="text-sm text-slate-400">자동/수동 입찰 성과를 모니터링하세요</p>
                </div>
            </div>

            {/* 필터 */}
            <div className="flex flex-wrap gap-4 mb-6">
                <div>
                    <label className="text-sm text-slate-400 mb-1 block">입찰 유형</label>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value as any)}
                        className="px-3 py-1 bg-slate-700/50 border border-slate-600 rounded text-slate-200 text-sm"
                    >
                        <option value="all">전체</option>
                        <option value="auto">자동 입찰</option>
                        <option value="manual">수동 입찰</option>
                    </select>
                </div>

                <div>
                    <label className="text-sm text-slate-400 mb-1 block">결과</label>
                    <select
                        value={resultFilter}
                        onChange={(e) => setResultFilter(e.target.value as any)}
                        className="px-3 py-1 bg-slate-700/50 border border-slate-600 rounded text-slate-200 text-sm"
                    >
                        <option value="all">전체</option>
                        <option value="won">성공</option>
                        <option value="lost">실패</option>
                    </select>
                </div>

                <div>
                    <label className="text-sm text-slate-400 mb-1 block">기간</label>
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value as any)}
                        className="px-3 py-1 bg-slate-700/50 border border-slate-600 rounded text-slate-200 text-sm"
                    >
                        <option value="today">오늘</option>
                        <option value="week">이번 주</option>
                        <option value="month">이번 달</option>
                    </select>
                </div>
            </div>

            {/* 통계 카드 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center space-x-2 mb-2">
                        <Target className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-slate-400">총 입찰</span>
                    </div>
                    <p className="text-xl font-bold text-slate-200">{totalBids}회</p>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-green-400" />
                        <span className="text-sm text-slate-400">성공률</span>
                    </div>
                    <p className="text-xl font-bold text-green-400">{successRate.toFixed(1)}%</p>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center space-x-2 mb-2">
                        <DollarSign className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm text-slate-400">총 지출</span>
                    </div>
                    <p className="text-xl font-bold text-yellow-400">{formatCurrency(totalSpent)}원</p>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center space-x-2 mb-2">
                        <BarChart3 className="w-4 h-4 text-purple-400" />
                        <span className="text-sm text-slate-400">평균 입찰가</span>
                    </div>
                    <p className="text-xl font-bold text-purple-400">{formatCurrency(Math.round(averageBidAmount))}원</p>
                </div>
            </div>

            {/* 상세 통계 */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">입찰 결과 분포</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-green-400">성공</span>
                            <span className="text-slate-200">{wonBids}회</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-red-400">실패</span>
                            <span className="text-slate-200">{lostBids}회</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-yellow-400">대기중</span>
                            <span className="text-slate-200">{pendingBids}회</span>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">입찰 유형 분포</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-blue-400">자동 입찰</span>
                            <span className="text-slate-200">{autoBidCount}회</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-purple-400">수동 입찰</span>
                            <span className="text-slate-200">{manualBidCount}회</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 입찰 내역 테이블 */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-600">
                            <th className="text-left py-2 text-slate-400">검색어</th>
                            <th className="text-left py-2 text-slate-400">입찰가</th>
                            <th className="text-left py-2 text-slate-400">결과</th>
                            <th className="text-left py-2 text-slate-400">매칭점수</th>
                            <th className="text-left py-2 text-slate-400">유형</th>
                            <th className="text-left py-2 text-slate-400">시간</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredHistory.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="text-center py-8 text-slate-400">
                                    <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                    <p>입찰 내역이 없습니다</p>
                                </td>
                            </tr>
                        ) : (
                            filteredHistory.map((bid) => (
                                <tr key={bid.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                                    <td className="py-3 text-slate-200 font-medium">
                                        {bid.searchQuery}
                                    </td>
                                    <td className="py-3 text-slate-200">
                                        {formatCurrency(bid.bidAmount)}원
                                    </td>
                                    <td className="py-3">
                                        <div className={`flex items-center space-x-1 ${getResultColor(bid.result)}`}>
                                            {getResultIcon(bid.result)}
                                            <span className="capitalize">
                                                {bid.result === 'won' ? '성공' : bid.result === 'lost' ? '실패' : '대기중'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="py-3 text-slate-200">
                                        {(bid.matchScore * 100).toFixed(1)}%
                                    </td>
                                    <td className="py-3">
                                        <span className={`px-2 py-1 rounded text-xs ${bid.isAutoBid
                                                ? 'bg-blue-500/20 text-blue-400'
                                                : 'bg-purple-500/20 text-purple-400'
                                            }`}>
                                            {bid.isAutoBid ? '자동' : '수동'}
                                        </span>
                                    </td>
                                    <td className="py-3 text-slate-400">
                                        {formatDate(bid.timestamp)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* 로딩 상태 */}
            {isLoading && (
                <div className="mt-4 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-400"></div>
                    <span className="ml-2 text-sm text-slate-400">로딩 중...</span>
                </div>
            )}
        </div>
    )
} 