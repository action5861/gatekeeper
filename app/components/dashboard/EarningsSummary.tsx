// [LIVE]
'use client'

import { Calendar, DollarSign, TrendingUp, Wallet } from 'lucide-react';
import { useState } from 'react';
import WithdrawalModal from './WithdrawalModal';

type Props = {
  todayRewards: number
  todayBids: number
  todayBidValue: number
  successRate: number
  avgQualityScore: number
  totalEarnings?: number
  onWithdrawalSuccess?: () => void
}

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

export default function EarningsSummary({ todayRewards, todayBids, todayBidValue, successRate, avgQualityScore, totalEarnings = 0, onWithdrawalSuccess }: Props) {
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false)

  const handleWithdrawalSuccess = () => {
    setIsWithdrawalModalOpen(false)
    onWithdrawalSuccess?.()
  }

  return (
    <>
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
          <DollarSign className="w-6 h-6 text-green-400" />
          <span>Earnings Summary</span>
        </h3>

        {/* Total Earnings */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-green-600/20 to-blue-600/20 rounded-lg p-4 border border-green-500/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-slate-400 text-sm">Total Earnings</p>
                <p className="text-3xl font-bold text-green-400">
                  {totalEarnings.toLocaleString()}P
                </p>
              </div>
              <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
            </div>
            {/* Withdrawal Button - Always enabled */}
            <button
              onClick={() => setIsWithdrawalModalOpen(true)}
              className="w-full py-2.5 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-semibold rounded-lg transition-all flex items-center justify-center space-x-2"
            >
              <Wallet className="w-4 h-4" />
              <span>출금하기</span>
            </button>
            <p className="text-xs text-slate-400 text-center mt-2">
              최소 출금 금액: 10,000 Points
            </p>
          </div>
        </div>

        {/* Today's Earnings */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-4 border border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Today's Earnings</p>
                <p className="text-2xl font-bold text-blue-400">
                  {todayRewards.toLocaleString()}P
                </p>
              </div>
              <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Today's Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Calendar className="w-4 h-4 text-blue-400" />
              <span className="text-slate-300 text-sm">Today's Bids</span>
            </div>
            <p className="text-xl font-bold text-blue-400">
              {todayBids}
            </p>
          </div>

          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span className="text-slate-300 text-sm">Bid Value</span>
            </div>
            <p className="text-xl font-bold text-slate-400">
              {todayBidValue.toLocaleString()}P
            </p>
          </div>
        </div>

        {/* Success Rate */}
        <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <span className="text-slate-300">Success Rate</span>
          </div>
          <span className="font-semibold text-green-400">
            {successRate.toFixed(1)}%
          </span>
        </div>

        {/* Quick Stats */}
        <div className="mt-6 pt-6 border-t border-slate-600">
          <h4 className="text-lg font-semibold text-slate-100 mb-4">Quick Stats</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Avg Quality Score</span>
              <span className="text-slate-100 font-semibold">
                {avgQualityScore.toFixed(1)}점
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Today's Rewards</span>
              <span className="text-slate-100 font-semibold">
                {todayRewards.toLocaleString()}P
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Today's Bids</span>
              <span className="text-slate-100 font-semibold">
                {todayBids}회
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Withdrawal Modal */}
      <WithdrawalModal
        isOpen={isWithdrawalModalOpen}
        onClose={() => setIsWithdrawalModalOpen(false)}
        totalEarnings={totalEarnings}
        onSuccess={handleWithdrawalSuccess}
      />
    </>
  )
} 