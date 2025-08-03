'use client'

import { ErrorFallback } from '@/components/ui/ErrorFallback';
import { RealtimeStatsSkeleton } from '@/components/ui/Skeleton';
import { useStatsData } from '@/lib/hooks/useDashboardData';
import { logComponentError } from '@/lib/utils/errorMonitor';
import { Search, Target, TrendingUp } from 'lucide-react';

interface StatsData {
    monthlySearches: number;
    successRate: number;
    avgQualityScore: number;
}

export default function RealtimeStats() {
    const { stats, isLoading, error, refetch } = useStatsData();

    // 에러 처리
    if (error) {
        logComponentError(
            error instanceof Error ? error : new Error(error.toString()),
            'RealtimeStats',
            undefined,
            { stats }
        );
    }

    if (isLoading) {
        return <RealtimeStatsSkeleton />;
    }

    if (error) {
        return (
            <ErrorFallback
                error={error}
                componentName="Realtime Stats"
                onRetry={refetch}
            />
        );
    }

    const defaultStats = {
        monthlySearches: 0,
        successRate: 0,
        avgQualityScore: 0,
    }

    const currentStats = stats || defaultStats

    return (
        <div className="mt-8 grid md:grid-cols-3 gap-6">
            {/* Total Searches */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-600">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Total Searches</h3>
                    <Search className="w-5 h-5 text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-blue-400">
                    {currentStats.monthlySearches}
                </p>
                <p className="text-sm text-slate-400 mt-1">This month</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>

            {/* Success Rate */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-700">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Success Rate</h3>
                    <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <p className="text-3xl font-bold text-green-400">
                    {currentStats.successRate}%
                </p>
                <p className="text-sm text-slate-400 mt-1">Auction completion</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>

            {/* Avg Quality Score */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-800">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Avg Quality Score</h3>
                    <Target className="w-5 h-5 text-yellow-400" />
                </div>
                <p className="text-3xl font-bold text-yellow-400">
                    {currentStats.avgQualityScore}
                </p>
                <p className="text-sm text-slate-400 mt-1">Out of 100</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>
        </div>
    )
} 