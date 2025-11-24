'use client'

import Link from 'next/link'
import { ArrowRight, DollarSign, Settings, Target, TrendingUp } from 'lucide-react'

interface BudgetStatusProps {
    additionalStats?: {
        autoBidEnabled: boolean
        dailyBudget: number
        todaySpent: number
        budgetUsagePercent: number
        maxBidPerKeyword: number
        minQualityScore: number
        remainingBudget: number
    }
}

export default function BudgetStatus({ additionalStats }: BudgetStatusProps) {
    if (!additionalStats) {
        return (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    const getBudgetColor = (usagePercent: number) => {
        if (usagePercent >= 90) return 'text-red-400'
        if (usagePercent >= 70) return 'text-yellow-400'
        return 'text-green-400'
    }

    const getBudgetBarColor = (usagePercent: number) => {
        if (usagePercent >= 90) return 'bg-red-500'
        if (usagePercent >= 70) return 'bg-yellow-500'
        return 'bg-green-500'
    }

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-100">Budget & Settings</h2>
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                    <Settings className="w-5 h-5 text-white" />
                </div>
            </div>

            {/* Auto Bid Status */}
            <div className="mb-6 p-4 bg-slate-700/30 rounded-xl">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${additionalStats.autoBidEnabled ? 'bg-green-400' : 'bg-red-400'}`}></div>
                        <span className="text-slate-300 font-medium">
                            Auto Bidding: {additionalStats.autoBidEnabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                    <span className={`text-sm ${additionalStats.autoBidEnabled ? 'text-green-400' : 'text-red-400'}`}>
                        {additionalStats.autoBidEnabled ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>

            {/* Budget Overview */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Daily Budget */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                            <DollarSign className="w-4 h-4 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Daily Budget</p>
                            <p className="text-lg font-bold text-slate-100">{additionalStats.dailyBudget.toLocaleString()}P</p>
                        </div>
                    </div>
                </div>

                {/* Today Spent */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-4 h-4 text-yellow-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Today Spent</p>
                            <p className="text-lg font-bold text-slate-100">{additionalStats.todaySpent.toLocaleString()}P</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Budget Usage Bar */}
            <div className="mb-6">
                <div className="flex justify-between text-sm text-slate-400 mb-2">
                    <span>Budget Usage</span>
                    <span className={getBudgetColor(additionalStats.budgetUsagePercent)}>
                        {additionalStats.budgetUsagePercent}%
                    </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                    <div
                        className={`h-3 rounded-full transition-all duration-300 ${getBudgetBarColor(additionalStats.budgetUsagePercent)}`}
                        style={{ width: `${Math.min(additionalStats.budgetUsagePercent, 100)}%` }}
                    ></div>
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>0P</span>
                    <span>{additionalStats.dailyBudget.toLocaleString()}P</span>
                </div>
            </div>

            {/* Remaining Budget */}
            <div className="mb-6 p-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl border border-green-500/20">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-slate-400">Remaining Budget</p>
                        <p className="text-xl font-bold text-green-400">{additionalStats.remainingBudget.toLocaleString()}P</p>
                    </div>
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-xl flex items-center justify-center">
                        <DollarSign className="w-6 h-6 text-white" />
                    </div>
                </div>
            </div>

            {/* Settings */}
            <div className="grid grid-cols-2 gap-4">
                {/* Max Bid */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                            <Target className="w-4 h-4 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Max Bid</p>
                            <p className="text-lg font-bold text-slate-100">{additionalStats.maxBidPerKeyword.toLocaleString()}P</p>
                        </div>
                    </div>
                </div>

                {/* Min Quality */}
                <div className="bg-slate-700/30 rounded-xl p-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-orange-500/20 rounded-lg flex items-center justify-center">
                            <Target className="w-4 h-4 text-orange-400" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Min Quality</p>
                            <p className="text-lg font-bold text-slate-100">{additionalStats.minQualityScore}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Manage Auto Bidding CTA */}
            <div className="mt-6">
                <Link
                    href="/advertiser/auto-bidding"
                    className="group inline-flex w-full items-center justify-between rounded-xl bg-blue-600/90 px-5 py-3 text-base font-semibold text-white transition-all duration-200 hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300"
                >
                    <span>자동 입찰 설정 관리하기</span>
                    <ArrowRight className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
            </div>
        </div>
    )
}
