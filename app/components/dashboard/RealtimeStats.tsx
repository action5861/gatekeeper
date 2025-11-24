// [LIVE]
'use client'

import { Search, Target, TrendingUp } from 'lucide-react';

export default function RealtimeStats({ recentQueries = 0, recentBids = 0 }: { recentQueries: number; recentBids: number }) {
    // 숫자 표시를 props 기반으로

    const currentStats = {
        monthlySearches: recentQueries,
        successRate: 0, // This would need to be passed as a prop or calculated
        avgQualityScore: 0, // This would need to be passed as a prop or calculated
    }

    return (
        <div className="mt-8 grid md:grid-cols-3 gap-6">
            {/* Recent Queries */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-600">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Recent Queries</h3>
                    <Search className="w-5 h-5 text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-blue-400">
                    {recentQueries}
                </p>
                <p className="text-sm text-slate-400 mt-1">Last 24 hours</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>

            {/* Recent Bids */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-700">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Recent Bids</h3>
                    <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <p className="text-3xl font-bold text-green-400">
                    {recentBids}
                </p>
                <p className="text-sm text-slate-400 mt-1">Last 24 hours</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>

            {/* Activity Status */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp animation-delay-800">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">Activity Status</h3>
                    <Target className="w-5 h-5 text-yellow-400" />
                </div>
                <p className="text-3xl font-bold text-yellow-400">
                    {recentQueries + recentBids > 0 ? 'Active' : 'Idle'}
                </p>
                <p className="text-sm text-slate-400 mt-1">Current status</p>
                <div className="mt-2 flex items-center text-xs text-slate-500">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse"></div>
                    <span>Live data</span>
                </div>
            </div>
        </div>
    )
} 