// 품질 지수 변화 추이 차트

'use client'

import { ErrorFallback } from '@/components/ui/ErrorFallback';
import { QualityHistorySkeleton } from '@/components/ui/Skeleton';
import { useQualityData } from '@/lib/hooks/useDashboardData';
import { logComponentError } from '@/lib/utils/errorMonitor';
import { BarChart3, Target, TrendingUp } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface QualityHistoryData {
  name: string;
  score: number;
}

interface QualityStats {
  average: number;
  max: number;
  min: number;
  growth: {
    percentage: string;
    isPositive: boolean;
  };
  recentScore: number;
}

export default function QualityHistory() {
  const { qualityHistory, qualityStats, isLoading, error, refetch } = useQualityData();

  // 에러 처리
  if (error) {
    logComponentError(
      error instanceof Error ? error : new Error(error.toString()),
      'QualityHistory',
      undefined,
      { qualityHistory, qualityStats }
    );
  }

  // 로딩 상태
  if (isLoading) {
    return <QualityHistorySkeleton />;
  }

  // 에러 상태
  if (error) {
    return (
      <ErrorFallback
        error={error}
        componentName="Quality History"
        onRetry={refetch}
      />
    );
  }

  // 데이터가 없는 경우
  if (!qualityHistory || qualityHistory.length === 0) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <span>Quality History</span>
        </h3>
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center space-y-4">
            <BarChart3 className="w-8 h-8 text-slate-400" />
            <p className="text-slate-400">품질 이력 데이터가 없습니다</p>
            <p className="text-slate-500 text-sm text-center">검색어를 제출하면 품질 점수가 기록됩니다</p>
          </div>
        </div>
      </div>
    )
  }

  // 차트 데이터 준비 (역순으로 정렬하여 최신이 오른쪽에 오도록)
  const chartData = qualityHistory
    .slice()
    .reverse()
    .map((item, index) => ({
      week: item.name,
      score: item.score,
      target: 70
    }))

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Quality History</span>
      </h3>

      {/* Summary Stats */}
      {qualityStats && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-400">{qualityStats.average}</p>
            <p className="text-sm text-slate-400">평균 점수</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-400">{qualityStats.max}</p>
            <p className="text-sm text-slate-400">최고 점수</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-400">{qualityStats.recentScore}</p>
            <p className="text-sm text-slate-400">최근 점수</p>
          </div>
          <div className="text-center">
            <p className={`text-2xl font-bold ${qualityStats.growth.isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {qualityStats.growth.percentage}
            </p>
            <p className="text-sm text-slate-400">성장률</p>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorTarget" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="week"
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
              domain={[0, 110]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }}
              labelStyle={{ color: '#9CA3AF' }}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#3B82F6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorScore)"
              name="Quality Score"
            />
            <Line
              type="monotone"
              dataKey="target"
              stroke="#EF4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Target"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <span className="text-slate-300">Quality Score</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-slate-300">Target (70)</span>
        </div>
      </div>

      {/* Insights */}
      {qualityStats && (
        <div className="mt-6 pt-6 border-t border-slate-600">
          <h4 className="text-lg font-semibold text-slate-100 mb-4 flex items-center space-x-2">
            <Target className="w-5 h-5 text-yellow-400" />
            <span>Insights</span>
          </h4>
          <div className="space-y-2 text-sm">
            <p className="text-slate-300">
              • 평균 품질 점수: <span className="text-blue-400 font-semibold">{qualityStats.average}점</span>
            </p>
            <p className="text-slate-300">
              • 최고 기록: <span className="text-green-400 font-semibold">{qualityStats.max}점</span>
            </p>
            {qualityStats.growth.percentage !== "N/A" && (
              <p className="text-slate-300">
                • 성장률: <span className={`font-semibold ${qualityStats.growth.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {qualityStats.growth.percentage}
                </span>
              </p>
            )}
            {qualityStats.recentScore >= 70 && (
              <p className="text-slate-300">
                • 목표 점수(70점)를 달성하고 있습니다
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
} 