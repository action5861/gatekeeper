// [LIVE] useDashboardData – 실제 데이터 연동
import { fetchQualityHistory, fetchRealtime, fetchSummary, fetchTransactions, type TransactionItem } from '@/lib/api/dashboard'
import { useEffect, useState } from 'react'

export function useDashboardData() {
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const [transactions, setTransactions] = useState<TransactionItem[] | null>(null)
    const [summary, setSummary] = useState<null | {
        avgQualityScore: number; successRate: number; totalEarnings: number; today: { bids: number; bidValue: number; rewards: number }
    }>(null)
    const [qualitySeries, setQualitySeries] = useState<null | { date: string; avg: number; count: number }[]>(null)
    const [realtime, setRealtime] = useState<{ recentQueries: number; recentBids: number } | null>(null)

    useEffect(() => {
        let mounted = true
        ; (async () => {
            try {
                if (typeof window !== 'undefined') {
                    const userType = localStorage.getItem('userType')
                    if (userType === 'advertiser') {
                        if (mounted) {
                            setIsLoading(false)
                            setError(new Error('advertiser_redirect'))
                        }
                        return
                    }
                }

                const [s, q, t, r] = await Promise.all([
                    fetchSummary(),
                    fetchQualityHistory(),
                    fetchTransactions(),
                    fetchRealtime(),
                ])
                if (!mounted) return
                setSummary(s)
                setQualitySeries(q)
                setTransactions(t)
                setRealtime(r)
            } catch (e: any) {
                if (mounted) setError(e instanceof Error ? e : new Error(String(e)))
            } finally {
                if (mounted) setIsLoading(false)
            }
        })()
        return () => { mounted = false }
    }, [])

    // 데이터 새로고침 함수 추가
    const refetch = () => {
        if (typeof window !== 'undefined' && localStorage.getItem('userType') === 'advertiser') {
            setError(new Error('advertiser_redirect'))
            setIsLoading(false)
            return
        }

        setIsLoading(true)
        setError(null)
        ; (async () => {
            try {
                const [s, q, t, r] = await Promise.all([
                    fetchSummary(),
                    fetchQualityHistory(),
                    fetchTransactions(),
                    fetchRealtime(),
                ])
                setSummary(s)
                setQualitySeries(q)
                setTransactions(t)
                setRealtime(r)
            } catch (e: any) {
                setError(e instanceof Error ? e : new Error(String(e)))
            } finally {
                setIsLoading(false)
            }
        })()
    }

    return { isLoading, error, transactions, summary, qualitySeries, realtime, refetch }
}

// 개별 섹션별 데이터 추출 훅들
export function useEarningsData() {
    const { summary, isLoading, error } = useDashboardData()

    return {
        earnings: summary ? {
            total: summary.today.rewards,
            primary: summary.today.rewards,
            secondary: 0,
            thisMonth: {
                total: summary.today.rewards,
                primary: summary.today.rewards,
                secondary: 0,
            },
            lastMonth: {
                total: 0,
                primary: 0,
                secondary: 0,
            },
            growth: {
                percentage: "N/A",
                isPositive: true,
            },
        } : null,
        isLoading,
        error,
        refetch: () => { },
        isFetching: false,
        isError: !!error,
    }
}

export function useQualityData() {
    const { qualitySeries, summary, isLoading, error } = useDashboardData()

    return {
        qualityHistory: qualitySeries ? qualitySeries.map(item => ({
            name: item.date,
            score: item.avg
        })) : [],
        qualityStats: summary ? {
            average: summary.avgQualityScore,
            max: summary.avgQualityScore,
            min: summary.avgQualityScore,
            growth: {
                percentage: "N/A",
                isPositive: true,
            },
            recentScore: summary.avgQualityScore,
        } : null,
        isLoading,
        error,
        refetch: () => { },
        isFetching: false,
        isError: !!error,
    }
}

export function useSubmissionData() {
    const { summary, isLoading, error } = useDashboardData()

    return {
        submissionLimit: {
            level: 'Standard' as const,
            dailyMax: 5,
        },
        dailySubmission: summary ? {
            count: summary.today.bids,
            limit: 5,
            remaining: Math.max(0, 5 - summary.today.bids),
            qualityScoreAvg: summary.avgQualityScore,
        } : null,
        isLoading,
        error,
        refetch: () => { },
        isFetching: false,
        isError: !!error,
    }
}

export function useStatsData() {
    const { summary, realtime, isLoading, error } = useDashboardData()

    return {
        stats: summary && realtime ? {
            monthlySearches: realtime.recentQueries,
            successRate: summary.successRate,
            avgQualityScore: summary.avgQualityScore,
        } : null,
        isLoading,
        error,
        refetch: () => { },
        isFetching: false,
        isError: !!error,
    }
}

export function useTransactionData() {
    const { transactions, isLoading, error } = useDashboardData()

    return {
        transactions,
        isLoading,
        error,
        refetch: () => { },
        isFetching: false,
        isError: !!error,
    }
} 