'use client'

import { AlertTriangle, DollarSign, Target, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'

interface BudgetControlProps {
    dailyBudget: number
    maxBidPerKeyword: number
    onBudgetChange: (dailyBudget: number, maxBidPerKeyword: number) => void
    isLoading?: boolean
}

export default function BudgetControl({
    dailyBudget,
    maxBidPerKeyword,
    onBudgetChange,
    isLoading = false
}: BudgetControlProps) {
    const [localDailyBudget, setLocalDailyBudget] = useState(dailyBudget)
    const [localMaxBid, setLocalMaxBid] = useState(maxBidPerKeyword)
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        setLocalDailyBudget(dailyBudget)
        setLocalMaxBid(maxBidPerKeyword)
    }, [dailyBudget, maxBidPerKeyword])

    const handleSave = async () => {
        setIsSaving(true)
        try {
            await onBudgetChange(localDailyBudget, localMaxBid)
        } finally {
            setIsSaving(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('ko-KR').format(amount)
    }

    const getBudgetStatus = () => {
        const budgetRatio = (localMaxBid * 10) / localDailyBudget // 예상 일일 입찰 횟수 10회 가정
        if (budgetRatio > 0.8) return 'warning'
        if (budgetRatio > 0.5) return 'caution'
        return 'safe'
    }

    const budgetStatus = getBudgetStatus()

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-slate-100">예산 관리</h3>
                    <p className="text-sm text-slate-400">일일 예산과 키워드당 최대 입찰가를 설정하세요</p>
                </div>
            </div>

            <div className="space-y-6">
                {/* 일일 예산 설정 */}
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <label className="text-sm font-medium text-slate-300">
                            일일 예산
                        </label>
                        <span className="text-lg font-bold text-blue-400">
                            {formatCurrency(localDailyBudget)}원
                        </span>
                    </div>
                    <input
                        type="range"
                        min="1000"
                        max="100000"
                        step="1000"
                        value={localDailyBudget}
                        onChange={(e) => setLocalDailyBudget(Number(e.target.value))}
                        disabled={isLoading || isSaving}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                        <span>1,000원</span>
                        <span>100,000원</span>
                    </div>
                </div>

                {/* 키워드당 최대 입찰가 설정 */}
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <label className="text-sm font-medium text-slate-300">
                            키워드당 최대 입찰가
                        </label>
                        <span className="text-lg font-bold text-green-400">
                            {formatCurrency(localMaxBid)}원
                        </span>
                    </div>
                    <input
                        type="range"
                        min="100"
                        max="10000"
                        step="100"
                        value={localMaxBid}
                        onChange={(e) => setLocalMaxBid(Number(e.target.value))}
                        disabled={isLoading || isSaving}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                        <span>100원</span>
                        <span>10,000원</span>
                    </div>
                </div>

                {/* 예산 상태 표시 */}
                <div className={`rounded-lg p-4 border ${budgetStatus === 'warning'
                    ? 'bg-red-500/10 border-red-500/20'
                    : budgetStatus === 'caution'
                        ? 'bg-yellow-500/10 border-yellow-500/20'
                        : 'bg-green-500/10 border-green-500/20'
                    }`}>
                    <div className="flex items-center space-x-2 mb-2">
                        {budgetStatus === 'warning' ? (
                            <AlertTriangle className="w-5 h-5 text-red-400" />
                        ) : budgetStatus === 'caution' ? (
                            <Target className="w-5 h-5 text-yellow-400" />
                        ) : (
                            <TrendingUp className="w-5 h-5 text-green-400" />
                        )}
                        <span className={`font-medium ${budgetStatus === 'warning'
                            ? 'text-red-400'
                            : budgetStatus === 'caution'
                                ? 'text-yellow-400'
                                : 'text-green-400'
                            }`}>
                            {budgetStatus === 'warning'
                                ? '예산 주의'
                                : budgetStatus === 'caution'
                                    ? '예산 적정'
                                    : '예산 안전'
                            }
                        </span>
                    </div>
                    <p className={`text-sm ${budgetStatus === 'warning'
                        ? 'text-red-300'
                        : budgetStatus === 'caution'
                            ? 'text-yellow-300'
                            : 'text-green-300'
                        }`}>
                        {budgetStatus === 'warning'
                            ? '일일 예산 대비 입찰가가 높습니다. 예산을 늘리거나 입찰가를 낮춰주세요.'
                            : budgetStatus === 'caution'
                                ? '적절한 예산 설정입니다. 성과를 모니터링하여 조정하세요.'
                                : '안전한 예산 설정입니다. 충분한 여유가 있습니다.'
                        }
                    </p>
                </div>

                {/* 예상 성과 */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">예상 성과</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p className="text-slate-400">예상 일일 입찰 횟수</p>
                            <p className="text-slate-200 font-semibold">
                                {Math.floor(localDailyBudget / localMaxBid)}회
                            </p>
                        </div>
                        <div>
                            <p className="text-slate-400">평균 입찰가</p>
                            <p className="text-slate-200 font-semibold">
                                {formatCurrency(Math.floor(localMaxBid * 0.7))}원
                            </p>
                        </div>
                    </div>
                </div>

                {/* 저장 버튼 */}
                <button
                    onClick={handleSave}
                    disabled={isLoading || isSaving || (localDailyBudget === dailyBudget && localMaxBid === maxBidPerKeyword)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSaving ? '저장 중...' : '설정 저장'}
                </button>
            </div>

            {/* 로딩 상태 */}
            {isLoading && (
                <div className="mt-4 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                    <span className="ml-2 text-sm text-slate-400">로딩 중...</span>
                </div>
            )}
        </div>
    )
} 