'use client'

import { authenticatedFetch, handleTokenExpiry } from '@/lib/auth';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface DashboardData {
    earnings: {
        total: number;
        primary: number;
        secondary: number;
        thisMonth: {
            total: number;
            primary: number;
            secondary: number;
        };
        lastMonth: {
            total: number;
            primary: number;
            secondary: number;
        };
        growth: {
            percentage: string;
            isPositive: boolean;
        };
    };
    qualityHistory: Array<{
        name: string;
        score: number;
    }>;
    qualityStats: {
        average: number;
        max: number;
        min: number;
        growth: {
            percentage: string;
            isPositive: boolean;
        };
        recentScore: number;
    };
    submissionLimit: {
        level: 'Excellent' | 'Good' | 'Average' | 'Needs Improvement';
        dailyMax: number;
    };
    dailySubmission: {
        count: number;
        limit: number;
        remaining: number;
        qualityScoreAvg: number;
    };
    stats: {
        monthlySearches: number;
        successRate: number;
        avgQualityScore: number;
    };
    transactions: any[];
}

const fetchDashboardData = async (): Promise<DashboardData> => {
    try {
        const response = await authenticatedFetch('/api/user/dashboard')
        return response.json()
    } catch (error) {
        if (error instanceof Error && error.message.includes('로그인이 만료')) {
            handleTokenExpiry()
            throw new Error('Authentication failed')
        }
        throw error
    }
}

export function useDashboardData() {
    const router = useRouter()
    const queryClient = useQueryClient()

    const {
        data: dashboardData,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    } = useQuery({
        queryKey: ['dashboard'],
        queryFn: fetchDashboardData,
        staleTime: 30000, // 30초 동안 데이터를 fresh로 간주
        gcTime: 5 * 60 * 1000, // 5분 동안 캐시 유지
        retry: (failureCount, error) => {
            // 인증 에러는 재시도하지 않음
            if (error instanceof Error && error.message.includes('Authentication failed')) {
                return false
            }
            // 네트워크 에러는 최대 3번 재시도
            return failureCount < 3
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    })

    // 인증 에러 시 로그인 페이지로 리다이렉트
    useEffect(() => {
        if (error instanceof Error && error.message.includes('Authentication failed')) {
            router.push('/login')
        }
    }, [error, router])

    // 실시간 업데이트를 위한 백그라운드 리페칭
    useEffect(() => {
        const interval = setInterval(() => {
            if (!isLoading && !isError) {
                queryClient.invalidateQueries({ queryKey: ['dashboard'] })
            }
        }, 30000) // 30초마다 백그라운드에서 데이터 갱신

        return () => clearInterval(interval)
    }, [queryClient, isLoading, isError])

    // 탭 포커스 시 데이터 갱신
    useEffect(() => {
        const handleFocus = () => {
            if (!isLoading && !isError) {
                queryClient.invalidateQueries({ queryKey: ['dashboard'] })
            }
        }

        window.addEventListener('focus', handleFocus)
        return () => window.removeEventListener('focus', handleFocus)
    }, [queryClient, isLoading, isError])

    // 커스텀 이벤트 리스너
    useEffect(() => {
        const handleStatsUpdate = () => {
            queryClient.invalidateQueries({ queryKey: ['dashboard'] })
        }

        window.addEventListener('stats-updated', handleStatsUpdate)
        window.addEventListener('reward-updated', handleStatsUpdate)
        window.addEventListener('quality-updated', handleStatsUpdate)
        window.addEventListener('submission-updated', handleStatsUpdate)

        return () => {
            window.removeEventListener('stats-updated', handleStatsUpdate)
            window.removeEventListener('reward-updated', handleStatsUpdate)
            window.removeEventListener('quality-updated', handleStatsUpdate)
            window.removeEventListener('submission-updated', handleStatsUpdate)
        }
    }, [queryClient])

    return {
        dashboardData,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
}

// 개별 섹션별 데이터 추출 훅들
export function useEarningsData() {
    const { dashboardData, isLoading, error, refetch, isFetching, isError } = useDashboardData()

    return {
        earnings: dashboardData?.earnings,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
}

export function useQualityData() {
    const { dashboardData, isLoading, error, refetch, isFetching, isError } = useDashboardData()

    return {
        qualityHistory: dashboardData?.qualityHistory,
        qualityStats: dashboardData?.qualityStats,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
}

export function useSubmissionData() {
    const { dashboardData, isLoading, error, refetch, isFetching, isError } = useDashboardData()

    return {
        submissionLimit: dashboardData?.submissionLimit,
        dailySubmission: dashboardData?.dailySubmission,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
}

export function useStatsData() {
    const { dashboardData, isLoading, error, refetch, isFetching, isError } = useDashboardData()

    return {
        stats: dashboardData?.stats,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
}

export function useTransactionData() {
    const { dashboardData, isLoading, error, refetch, isFetching, isError } = useDashboardData()

    return {
        transactions: dashboardData?.transactions,
        isLoading,
        error,
        refetch,
        isFetching,
        isError,
    }
} 