// [LIVE]
'use client'

import { BarChart3, Target, TrendingUp } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

type Point = { date: string; avg: number; count: number }

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

export default function QualityHistory({ series = [] as Point[] }) {
  // 차트/리스트에 series 사용 (하드코딩 제거)

  // 데이터가 없는 경우
  if (!series || series.length === 0) {
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

  // 차트 데이터 준비
  const chartData = series.map((item, index) => ({
    week: item.date,
    score: item.avg,
    target: 70
  }))

  // 통계 계산
  const scores = series.map(item => item.avg)
  const average = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
  const max = Math.max(...scores)
  const min = Math.min(...scores)
  const recentScore = scores[scores.length - 1] || 0

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Quality History</span>
      </h3>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-400">{average.toFixed(1)}</p>
          <p className="text-sm text-slate-400">평균 점수</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-400">{max.toFixed(1)}</p>
          <p className="text-sm text-slate-400">최고 점수</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-yellow-400">{recentScore.toFixed(1)}</p>
          <p className="text-sm text-slate-400">최근 점수</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-400">N/A</p>
          <p className="text-sm text-slate-400">성장률</p>
        </div>
      </div>

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
      <div className="mt-6 pt-6 border-t border-slate-600">
        <h4 className="text-lg font-semibold text-slate-100 mb-4 flex items-center space-x-2">
          <Target className="w-5 h-5 text-yellow-400" />
          <span>Insights</span>
        </h4>
        <div className="space-y-2 text-sm">
          <p className="text-slate-300">
            • 평균 품질 점수: <span className="text-blue-400 font-semibold">{average.toFixed(1)}점</span>
          </p>
          <p className="text-slate-300">
            • 최고 기록: <span className="text-green-400 font-semibold">{max.toFixed(1)}점</span>
          </p>
          <p className="text-slate-300">
            • 최근 점수: <span className="text-yellow-400 font-semibold">{recentScore.toFixed(1)}점</span>
          </p>
          {recentScore >= 70 && (
            <p className="text-slate-300">
              • 목표 점수(70점)를 달성하고 있습니다
            </p>
          )}
        </div>
      </div>
    </div>
  )
} 