'use client'

import { BarChart3, TrendingUp } from 'lucide-react'

interface PerformanceHistoryProps {
    performanceHistory?: Array<{
        name: string
        score: number
    }>
}

export default function PerformanceHistory({ performanceHistory }: PerformanceHistoryProps) {
    if (!performanceHistory) {
        return (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    const maxScore = Math.max(...performanceHistory.map(item => item.score))
    const currentScore = performanceHistory[performanceHistory.length - 1]?.score || 0

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-100">Performance History</h2>
                <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-white" />
                </div>
            </div>

            {/* Current Performance Score */}
            <div className="mb-6 p-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl border border-green-500/20">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-slate-400">Current Performance Score</p>
                        <p className="text-3xl font-bold text-slate-100">{currentScore}</p>
                        <p className="text-sm text-slate-400">out of 100</p>
                    </div>
                    <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-xl flex items-center justify-center">
                        <TrendingUp className="w-8 h-8 text-white" />
                    </div>
                </div>
            </div>

            {/* Performance Chart */}
            <div className="space-y-4">
                {performanceHistory.map((item, index) => {
                    const percentage = (item.score / maxScore) * 100
                    const isLatest = index === performanceHistory.length - 1

                    return (
                        <div key={item.name} className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-300">{item.name}</span>
                                <span className={`text-sm font-bold ${isLatest ? 'text-green-400' : 'text-slate-400'
                                    }`}>
                                    {item.score}
                                </span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full transition-all duration-500 ${isLatest
                                        ? 'bg-gradient-to-r from-green-500 to-blue-500'
                                        : 'bg-slate-600'
                                        }`}
                                    style={{ width: `${percentage}%` }}
                                />
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Performance Insights */}
            <div className="mt-6 p-4 bg-slate-700/30 rounded-xl">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Performance Insights</h3>
                <div className="space-y-2 text-sm text-slate-400">
                    {currentScore >= 80 && (
                        <p>🎉 Excellent performance! Keep up the great work.</p>
                    )}
                    {currentScore >= 60 && currentScore < 80 && (
                        <p>📈 Good performance. Consider optimizing your bidding strategy.</p>
                    )}
                    {currentScore < 60 && (
                        <p>⚠️ Performance needs improvement. Review your bidding patterns.</p>
                    )}
                </div>
            </div>
        </div>
    )
} 