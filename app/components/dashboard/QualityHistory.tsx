// 품질 지수 변화 추이 차트

'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, Target } from 'lucide-react'

export default function QualityHistory() {
  // 시뮬레이션 데이터 - 최근 30일간의 품질 점수
  const qualityData = [
    { date: '1/1', score: 65, target: 70 },
    { date: '1/2', score: 68, target: 70 },
    { date: '1/3', score: 72, target: 70 },
    { date: '1/4', score: 70, target: 70 },
    { date: '1/5', score: 75, target: 70 },
    { date: '1/6', score: 78, target: 70 },
    { date: '1/7', score: 82, target: 70 },
    { date: '1/8', score: 79, target: 70 },
    { date: '1/9', score: 85, target: 70 },
    { date: '1/10', score: 88, target: 70 },
    { date: '1/11', score: 86, target: 70 },
    { date: '1/12', score: 90, target: 70 },
    { date: '1/13', score: 87, target: 70 },
    { date: '1/14', score: 92, target: 70 },
    { date: '1/15', score: 89, target: 70 },
    { date: '1/16', score: 94, target: 70 },
    { date: '1/17', score: 91, target: 70 },
    { date: '1/18', score: 96, target: 70 },
    { date: '1/19', score: 93, target: 70 },
    { date: '1/20', score: 95, target: 70 },
    { date: '1/21', score: 98, target: 70 },
    { date: '1/22', score: 96, target: 70 },
    { date: '1/23', score: 99, target: 70 },
    { date: '1/24', score: 97, target: 70 },
    { date: '1/25', score: 100, target: 70 },
    { date: '1/26', score: 98, target: 70 },
    { date: '1/27', score: 102, target: 70 },
    { date: '1/28', score: 99, target: 70 },
    { date: '1/29', score: 105, target: 70 },
    { date: '1/30', score: 103, target: 70 },
  ]

  // 평균 점수 계산
  const averageScore = Math.round(
    qualityData.reduce((sum, item) => sum + item.score, 0) / qualityData.length
  )

  // 최근 7일 평균
  const recentAverage = Math.round(
    qualityData.slice(-7).reduce((sum, item) => sum + item.score, 0) / 7
  )

  // 성장률 계산
  const growth = ((recentAverage - averageScore) / averageScore * 100).toFixed(1)

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Quality History</span>
      </h3>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-400">{averageScore}</p>
          <p className="text-sm text-slate-400">30-day Avg</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-400">{recentAverage}</p>
          <p className="text-sm text-slate-400">7-day Avg</p>
        </div>
        <div className="text-center">
          <p className={`text-2xl font-bold ${parseFloat(growth) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {parseFloat(growth) >= 0 ? '+' : ''}{growth}%
          </p>
          <p className="text-sm text-slate-400">Growth</p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={qualityData}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorTarget" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="date" 
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
            • Your quality score has improved by <span className="text-green-400 font-semibold">{growth}%</span> this week
          </p>
          <p className="text-slate-300">
            • You're consistently exceeding the target score of 70
          </p>
          <p className="text-slate-300">
            • Best performance: <span className="text-blue-400 font-semibold">105 points</span> on Jan 29
          </p>
        </div>
      </div>
    </div>
  )
} 