'use client'

import {
    AlertTriangle,
    BarChart3,
    Brain,
    CheckCircle,
    DollarSign,
    Lightbulb,
    Play,
    Target,
    TrendingUp,
    Zap
} from 'lucide-react'
import { useEffect, useState } from 'react'

interface AnalyticsData {
    timeSeries: {
        date: string
        totalBids: number
        successRate: number
        avgBidAmount: number
        totalSpent: number
    }[]
    keywordPerformance: {
        keyword: string
        totalBids: number
        successRate: number
        avgBidAmount: number
        roi: number
    }[]
    matchTypeAnalysis: {
        matchType: string
        totalBids: number
        successRate: number
        avgBidAmount: number
    }[]
    optimizationSuggestions: {
        type: 'keyword' | 'bid' | 'timing' | 'budget'
        priority: 'high' | 'medium' | 'low'
        title: string
        description: string
        expectedImpact: string
        action: string
    }[]
    performanceComparison: {
        metric: string
        autoBid: number
        manualBid: number
        improvement: number
    }[]
}

interface AutoBidAnalyticsProps {
    advertiserId: number
    timeRange: 'day' | 'week' | 'month'
}

interface OptimizationRequest {
    search_query: string
    quality_score: number
    match_type: string
    match_score: number
    competitor_count: number
    budget_remaining: number
}

export default function AutoBidAnalytics({ advertiserId, timeRange }: AutoBidAnalyticsProps) {
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isExecuting, setIsExecuting] = useState(false)
    const [optimizationResult, setOptimizationResult] = useState<any>(null)

    useEffect(() => {
        fetchAnalyticsData()
    }, [advertiserId, timeRange])

    const fetchAnalyticsData = async () => {
        try {
            setIsLoading(true)
            const token = localStorage.getItem('token')

            const response = await fetch(`/api/advertiser/analytics/auto-bidding?timeRange=${timeRange}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                throw new Error('Failed to fetch analytics data')
            }

            const data = await response.json()
            setAnalyticsData(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('ko-KR').format(amount)
    }

    const formatPercentage = (value: number) => {
        return `${value.toFixed(1)}%`
    }

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high': return 'text-red-400'
            case 'medium': return 'text-yellow-400'
            case 'low': return 'text-green-400'
            default: return 'text-slate-400'
        }
    }

    const getPriorityIcon = (priority: string) => {
        switch (priority) {
            case 'high': return <AlertTriangle className="w-4 h-4" />
            case 'medium': return <Target className="w-4 h-4" />
            case 'low': return <CheckCircle className="w-4 h-4" />
            default: return <Lightbulb className="w-4 h-4" />
        }
    }

    const executeAutoBid = async (suggestion: any) => {
        try {
            setIsExecuting(true)
            const token = localStorage.getItem('token')

            // 기본 파라미터 설정
            const requestData = {
                search_query: suggestion.title.includes('키워드') ? '테스트 키워드' : '일반 검색',
                quality_score: 75,
                match_type: 'broad',
                match_score: 0.7,
                competitor_count: 3
            }

            const response = await fetch('/api/advertiser/auto-bid/execute', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            })

            if (!response.ok) {
                throw new Error('Failed to execute auto bid')
            }

            const result = await response.json()
            setOptimizationResult(result.data)

            // 성공 메시지 표시
            alert(`자동 입찰 실행 완료!\n입찰가: ${result.data.bid_amount}원\n결과: ${result.data.bid_result}`)

        } catch (err) {
            setError(err instanceof Error ? err.message : '자동 입찰 실행 실패')
        } finally {
            setIsExecuting(false)
        }
    }

    if (isLoading) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="text-center text-red-400">
                    <p>Error loading analytics: {error}</p>
                </div>
            </div>
        )
    }

    if (!analyticsData) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="text-center text-slate-400">
                    <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>분석 데이터가 없습니다</p>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* 성과 개요 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <div className="flex items-center space-x-2 mb-2">
                        <Target className="w-5 h-5 text-blue-400" />
                        <span className="text-sm text-slate-400">총 입찰</span>
                    </div>
                    <p className="text-2xl font-bold text-slate-200">
                        {analyticsData.timeSeries.reduce((sum, item) => sum + item.totalBids, 0)}
                    </p>
                </div>

                <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-green-400" />
                        <span className="text-sm text-slate-400">성공률</span>
                    </div>
                    <p className="text-2xl font-bold text-green-400">
                        {formatPercentage(analyticsData.timeSeries.reduce((sum, item) => sum + item.successRate, 0) / analyticsData.timeSeries.length)}
                    </p>
                </div>

                <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <div className="flex items-center space-x-2 mb-2">
                        <DollarSign className="w-5 h-5 text-yellow-400" />
                        <span className="text-sm text-slate-400">총 지출</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-400">
                        {formatCurrency(analyticsData.timeSeries.reduce((sum, item) => sum + item.totalSpent, 0))}원
                    </p>
                </div>

                <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <div className="flex items-center space-x-2 mb-2">
                        <Brain className="w-5 h-5 text-purple-400" />
                        <span className="text-sm text-slate-400">AI 점수</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-400">
                        {Math.round(analyticsData.timeSeries.reduce((sum, item) => sum + item.successRate, 0) / analyticsData.timeSeries.length * 10)}/10
                    </p>
                </div>
            </div>

            {/* 키워드별 성과 분석 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                        <Target className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-100">키워드별 성과 분석</h3>
                        <p className="text-sm text-slate-400">AI가 분석한 키워드별 최적화 지표</p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-slate-600">
                                <th className="text-left py-2 text-slate-400">키워드</th>
                                <th className="text-left py-2 text-slate-400">입찰 수</th>
                                <th className="text-left py-2 text-slate-400">성공률</th>
                                <th className="text-left py-2 text-slate-400">평균 입찰가</th>
                                <th className="text-left py-2 text-slate-400">ROI</th>
                                <th className="text-left py-2 text-slate-400">상태</th>
                            </tr>
                        </thead>
                        <tbody>
                            {analyticsData.keywordPerformance.map((keyword, index) => (
                                <tr key={index} className="border-b border-slate-700/50">
                                    <td className="py-3 text-slate-200 font-medium">{keyword.keyword}</td>
                                    <td className="py-3 text-slate-200">{keyword.totalBids}</td>
                                    <td className="py-3">
                                        <span className={`${keyword.successRate >= 70 ? 'text-green-400' : keyword.successRate >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                                            {formatPercentage(keyword.successRate)}
                                        </span>
                                    </td>
                                    <td className="py-3 text-slate-200">{formatCurrency(keyword.avgBidAmount)}원</td>
                                    <td className="py-3">
                                        <span className={`${keyword.roi >= 150 ? 'text-green-400' : keyword.roi >= 100 ? 'text-yellow-400' : 'text-red-400'}`}>
                                            {formatPercentage(keyword.roi)}
                                        </span>
                                    </td>
                                    <td className="py-3">
                                        <span className={`px-2 py-1 rounded text-xs ${keyword.successRate >= 70 && keyword.roi >= 150
                                            ? 'bg-green-500/20 text-green-400'
                                            : keyword.successRate >= 50 && keyword.roi >= 100
                                                ? 'bg-yellow-500/20 text-yellow-400'
                                                : 'bg-red-500/20 text-red-400'
                                            }`}>
                                            {keyword.successRate >= 70 && keyword.roi >= 150 ? '최적' :
                                                keyword.successRate >= 50 && keyword.roi >= 100 ? '보통' : '개선 필요'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 매칭 타입별 분석 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                            <Zap className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-100">매칭 타입별 성과</h3>
                            <p className="text-sm text-slate-400">매칭 정확도별 성공률 비교</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {analyticsData.matchTypeAnalysis.map((matchType, index) => (
                            <div key={index} className="bg-slate-700/30 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-slate-200 font-medium capitalize">{matchType.matchType}</span>
                                    <span className="text-slate-400 text-sm">{matchType.totalBids}회</span>
                                </div>
                                <div className="flex items-center space-x-4 text-sm">
                                    <div>
                                        <span className="text-slate-400">성공률: </span>
                                        <span className={`${matchType.successRate >= 70 ? 'text-green-400' : matchType.successRate >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                                            {formatPercentage(matchType.successRate)}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-slate-400">평균: </span>
                                        <span className="text-slate-200">{formatCurrency(matchType.avgBidAmount)}원</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 자동 vs 수동 비교 */}
                <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-100">자동 vs 수동 비교</h3>
                            <p className="text-sm text-slate-400">AI 자동 입찰의 성과 개선도</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {analyticsData.performanceComparison.map((comparison, index) => (
                            <div key={index} className="bg-slate-700/30 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-slate-200 font-medium">{comparison.metric}</span>
                                    <span className={`text-sm ${comparison.improvement > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {comparison.improvement > 0 ? '+' : ''}{comparison.improvement.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex items-center space-x-4 text-sm">
                                    <div>
                                        <span className="text-slate-400">자동: </span>
                                        <span className="text-green-400">{comparison.autoBid}</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-400">수동: </span>
                                        <span className="text-slate-200">{comparison.manualBid}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* AI 최적화 제안 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                        <Brain className="w-5 h-5 text-orange-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-100">AI 최적화 제안</h3>
                        <p className="text-sm text-slate-400">머신러닝 기반 개선 방안</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analyticsData.optimizationSuggestions.map((suggestion, index) => (
                        <div key={index} className={`bg-slate-700/30 rounded-lg p-4 border-l-4 ${suggestion.priority === 'high' ? 'border-red-500' :
                            suggestion.priority === 'medium' ? 'border-yellow-500' : 'border-green-500'
                            }`}>
                            <div className="flex items-start space-x-3">
                                <div className={`mt-1 ${getPriorityColor(suggestion.priority)}`}>
                                    {getPriorityIcon(suggestion.priority)}
                                </div>
                                <div className="flex-1">
                                    <h4 className="text-slate-200 font-medium mb-1">{suggestion.title}</h4>
                                    <p className="text-sm text-slate-400 mb-2">{suggestion.description}</p>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-slate-400">예상 효과: {suggestion.expectedImpact}</span>
                                        <button
                                            onClick={() => executeAutoBid(suggestion)}
                                            disabled={isExecuting}
                                            className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50"
                                        >
                                            {isExecuting ? (
                                                <>
                                                    <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-400"></div>
                                                    <span>실행중...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="w-3 h-3" />
                                                    <span>{suggestion.action}</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
} 