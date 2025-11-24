'use client'

import { DollarSign, Percent, Target, TrendingUp } from 'lucide-react'

interface BiddingSummaryProps {
    biddingSummary?: {
        totalBids: number
        successfulBids: number
        totalSpent: number
        averageBidAmount: number
    }
}

export default function BiddingSummary({ biddingSummary }: BiddingSummaryProps) {
    if (!biddingSummary) {
        return (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    const successRate = biddingSummary.totalBids > 0
        ? Math.round((biddingSummary.successfulBids / biddingSummary.totalBids) * 100)
        : 0

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-100">Bidding Summary</h2>
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-white" />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {/* Total Bids */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                            <Target className="w-4 h-4 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Total Bids</p>
                            <p className="text-2xl font-bold text-slate-100">{biddingSummary.totalBids}</p>
                        </div>
                    </div>
                </div>

                {/* Successful Bids */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-4 h-4 text-green-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Successful</p>
                            <p className="text-2xl font-bold text-slate-100">{biddingSummary.successfulBids}</p>
                        </div>
                    </div>
                </div>

                {/* Total Spent */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                            <DollarSign className="w-4 h-4 text-yellow-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Total Spent</p>
                            <p className="text-2xl font-bold text-slate-100">{biddingSummary.totalSpent.toLocaleString()}P</p>
                        </div>
                    </div>
                </div>

                {/* Success Rate */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                            <Percent className="w-4 h-4 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Success Rate</p>
                            <p className="text-2xl font-bold text-slate-100">{successRate}%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Average Bid Amount */}
            <div className="mt-6 p-4 bg-gradient-to-r from-blue-500/10 to-green-500/10 rounded-xl border border-blue-500/20">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-slate-400">Average Bid Amount</p>
                        <p className="text-xl font-bold text-slate-100">{biddingSummary.averageBidAmount.toLocaleString()}P</p>
                    </div>
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-green-500 rounded-xl flex items-center justify-center">
                        <DollarSign className="w-6 h-6 text-white" />
                    </div>
                </div>
            </div>
        </div>
    )
} 