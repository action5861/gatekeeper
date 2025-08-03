// 수익 현황 요약

'use client'

import { ErrorFallback } from '@/components/ui/ErrorFallback';
import { EarningsSummarySkeleton } from '@/components/ui/Skeleton';
import { useEarningsData } from '@/lib/hooks/useDashboardData';
import { logComponentError } from '@/lib/utils/errorMonitor';
import { Calendar, DollarSign, TrendingDown, TrendingUp } from 'lucide-react';

interface EarningsData {
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
}

export default function EarningsSummary() {
  const { earnings, isLoading, error, refetch, isFetching } = useEarningsData();

  // 에러 처리
  if (error) {
    logComponentError(
      error instanceof Error ? error : new Error(error.toString()),
      'EarningsSummary',
      undefined,
      { earnings }
    );
  }

  // 로딩 상태
  if (isLoading) {
    return <EarningsSummarySkeleton />;
  }

  // 에러 상태
  if (error) {
    return (
      <ErrorFallback
        error={error}
        componentName="Earnings Summary"
        onRetry={refetch}
      />
    );
  }

  // 데이터가 없는 경우
  if (!earnings) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center space-y-4">
            <DollarSign className="w-8 h-8 text-slate-400" />
            <p className="text-slate-400">수익 데이터가 없습니다</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <DollarSign className="w-6 h-6 text-green-400" />
        <span>Earnings Summary</span>
      </h3>

      {/* Total Earnings */}
      <div className="mb-6">
        <div className="bg-gradient-to-r from-green-600/20 to-blue-600/20 rounded-lg p-4 border border-green-500/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Earnings</p>
              <p className="text-3xl font-bold text-green-400">
                {earnings.total.toLocaleString()}원
              </p>
            </div>
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Monthly Breakdown */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Calendar className="w-4 h-4 text-blue-400" />
            <span className="text-slate-300 text-sm">This Month</span>
          </div>
          <p className="text-xl font-bold text-blue-400">
            {earnings.thisMonth.total.toLocaleString()}원
          </p>
        </div>

        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300 text-sm">Last Month</span>
          </div>
          <p className="text-xl font-bold text-slate-400">
            {earnings.lastMonth.total.toLocaleString()}원
          </p>
        </div>
      </div>

      {/* Growth Indicator */}
      <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
        <div className="flex items-center space-x-2">
          {earnings.growth.isPositive ? (
            <TrendingUp className="w-5 h-5 text-green-400" />
          ) : (
            <TrendingDown className="w-5 h-5 text-red-400" />
          )}
          <span className="text-slate-300">Monthly Growth</span>
        </div>
        <span className={`font-semibold ${earnings.growth.isPositive ? 'text-green-400' : 'text-red-400'
          }`}>
          {earnings.growth.percentage}
        </span>
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-6 border-t border-slate-600">
        <h4 className="text-lg font-semibold text-slate-100 mb-4">Quick Stats</h4>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Primary Earnings</span>
            <span className="text-slate-100 font-semibold">
              {earnings.primary.toLocaleString()}원
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Secondary Earnings</span>
            <span className="text-slate-100 font-semibold">
              {earnings.secondary.toLocaleString()}원
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">This Month Primary</span>
            <span className="text-slate-100 font-semibold">
              {earnings.thisMonth.primary.toLocaleString()}원
            </span>
          </div>
        </div>
      </div>
    </div>
  )
} 