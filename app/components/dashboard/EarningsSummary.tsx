// 수익 현황 요약

'use client'

import { DollarSign, TrendingUp, TrendingDown, Calendar } from 'lucide-react'

interface EarningsSummaryProps {
  earnings?: {
    total: number;
    primary: number;
    secondary: number;
  };
}

export default function EarningsSummary({ earnings }: EarningsSummaryProps) {
  // 시뮬레이션 데이터 (fallback)
  const earningsData = {
    totalEarnings: earnings?.total || 1500,
    thisMonth: earnings?.primary || 850,
    lastMonth: earnings?.secondary || 650,
    change: '+30.8%',
    isPositive: true
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
                {earningsData.totalEarnings.toLocaleString()}원
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
            {earningsData.thisMonth.toLocaleString()}원
          </p>
        </div>
        
        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300 text-sm">Last Month</span>
          </div>
          <p className="text-xl font-bold text-slate-400">
            {earningsData.lastMonth.toLocaleString()}원
          </p>
        </div>
      </div>

      {/* Growth Indicator */}
      <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
        <div className="flex items-center space-x-2">
          {earningsData.isPositive ? (
            <TrendingUp className="w-5 h-5 text-green-400" />
          ) : (
            <TrendingDown className="w-5 h-5 text-red-400" />
          )}
          <span className="text-slate-300">Monthly Growth</span>
        </div>
        <span className={`font-semibold ${
          earningsData.isPositive ? 'text-green-400' : 'text-red-400'
        }`}>
          {earningsData.change}
        </span>
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-6 border-t border-slate-600">
        <h4 className="text-lg font-semibold text-slate-100 mb-4">Quick Stats</h4>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Completed Auctions</span>
            <span className="text-slate-100 font-semibold">18</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Average Bid Price</span>
            <span className="text-slate-100 font-semibold">3,200원</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Highest Single Bid</span>
            <span className="text-slate-100 font-semibold">8,500원</span>
          </div>
        </div>
      </div>
    </div>
  )
} 