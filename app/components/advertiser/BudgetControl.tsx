'use client'

import { AlertTriangle, CheckCircle2, DollarSign, Target, TrendingUp, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'

interface BudgetControlProps {
    dailyBudget: number
    maxBidPerKeyword: number
    onBudgetChange: (dailyBudget: number, maxBidPerKeyword: number, targetSlaTier: string) => Promise<boolean>
    isLoading?: boolean
    currentTier?: string
}

type TierType = 'standard' | 'deep' | 'booster'

interface TierConfig {
    name: string
    sla: string
    minBid: number
    color: string
    bgColor: string
    borderColor: string
    recommendedFor: string
    icon: typeof CheckCircle2
}

const TIER_CONFIGS: Record<TierType, TierConfig> = {
    standard: {
        name: 'Standard',
        sla: '20s+',
        minBid: 1000,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500',
        recommendedFor: 'Shopping, App Install',
        icon: CheckCircle2,
    },
    deep: {
        name: 'Deep',
        sla: '60s+',
        minBid: 3000,
        color: 'text-green-400',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500',
        recommendedFor: 'Insurance, Medical (Best Value)',
        icon: Zap,
    },
    booster: {
        name: 'Booster',
        sla: '90s+',
        minBid: 6000,
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500',
        recommendedFor: 'B2B, Real Estate',
        icon: Target,
    },
}

export default function BudgetControl({
    dailyBudget,
    maxBidPerKeyword,
    onBudgetChange,
    isLoading = false,
    currentTier = 'standard'
}: BudgetControlProps) {
    const [localDailyBudget, setLocalDailyBudget] = useState(dailyBudget)
    const [localMaxBid, setLocalMaxBid] = useState(maxBidPerKeyword)
    const [selectedTier, setSelectedTier] = useState<TierType>(currentTier as TierType || 'standard')
    const [isSaving, setIsSaving] = useState(false)
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
    const [statusMessage, setStatusMessage] = useState('')

    useEffect(() => {
        setLocalDailyBudget(dailyBudget)
        setLocalMaxBid(maxBidPerKeyword)
        if (currentTier) {
            setSelectedTier(currentTier as TierType)
        }
    }, [dailyBudget, maxBidPerKeyword, currentTier])

    // Tier 선택 시 최소 입찰가 자동 조정
    useEffect(() => {
        const tierConfig = TIER_CONFIGS[selectedTier]
        if (localMaxBid < tierConfig.minBid) {
            setLocalMaxBid(tierConfig.minBid)
        }
    }, [selectedTier])

    const handleSave = async () => {
        if (isSaving) return
        setIsSaving(true)
        setStatus('idle')
        setStatusMessage('')
        try {
            const tierConfig = TIER_CONFIGS[selectedTier]
            // 최소 입찰가 검증
            if (localMaxBid < tierConfig.minBid) {
                setStatus('error')
                setStatusMessage(`${tierConfig.name} 티어는 최소 ${tierConfig.minBid.toLocaleString()}원 입찰가가 필요합니다.`)
                setIsSaving(false)
                return
            }
            const saved = await onBudgetChange(localDailyBudget, localMaxBid, selectedTier)
            if (saved) {
                setStatus('success')
                setStatusMessage('예산 설정이 안전하게 저장되었습니다.')
            } else {
                setStatus('error')
                setStatusMessage('예산 설정을 저장하지 못했습니다. 다시 시도해주세요.')
            }
        } catch (error) {
            console.error('BudgetControl handleSave error:', error)
            setStatus('error')
            setStatusMessage('예산 설정 저장 중 문제가 발생했습니다.')
        } finally {
            setIsSaving(false)
        }
    }

    const handleTierSelect = (tier: TierType) => {
        setSelectedTier(tier)
        const tierConfig = TIER_CONFIGS[tier]
        // 최소 입찰가보다 낮으면 자동 업데이트
        if (localMaxBid < tierConfig.minBid) {
            setLocalMaxBid(tierConfig.minBid)
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
    const tierConfig = TIER_CONFIGS[selectedTier]
    const minBidForTier = tierConfig.minBid

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-slate-100">예산 관리</h3>
                    <p className="text-sm text-slate-400">SLA 티어를 선택하고 예산을 설정하세요</p>
                </div>
            </div>

            <div className="space-y-6">
                {/* 3-Card Tier Selection */}
                <div>
                    <label className="text-sm font-medium text-slate-300 mb-3 block">
                        SLA 티어 선택
                    </label>
                    <div className="grid grid-cols-3 gap-4">
                        {(['standard', 'deep', 'booster'] as TierType[]).map((tier) => {
                            const config = TIER_CONFIGS[tier]
                            const Icon = config.icon
                            const isSelected = selectedTier === tier
                            const isRecommended = tier === 'deep'

                            return (
                                <button
                                    key={tier}
                                    type="button"
                                    onClick={() => handleTierSelect(tier)}
                                    disabled={isLoading || isSaving}
                                    className={`
                                        relative p-4 rounded-lg border-2 transition-all
                                        ${isSelected
                                            ? `${config.borderColor} ${config.bgColor} ring-2 ring-offset-2 ring-offset-slate-800 ${config.borderColor.replace('border-', 'ring-')}`
                                            : 'border-slate-600 bg-slate-700/30 hover:border-slate-500'
                                        }
                                        ${isLoading || isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                    `}
                                >
                                    {isRecommended && (
                                        <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                                            추천
                                        </span>
                                    )}
                                    <div className="flex flex-col items-center text-center space-y-2">
                                        <Icon className={`w-6 h-6 ${config.color}`} />
                                        <div>
                                            <div className={`font-semibold ${config.color}`}>
                                                {config.name}
                                            </div>
                                            <div className="text-xs text-slate-400 mt-1">
                                                {config.sla} 체류시간
                                            </div>
                                        </div>
                                        <div className="text-xs text-slate-300 mt-2">
                                            최소 {formatCurrency(config.minBid)}원
                                        </div>
                                        <div className="text-xs text-slate-400 mt-1 px-2">
                                            {config.recommendedFor}
                                        </div>
                                    </div>
                                </button>
                            )
                        })}
                    </div>
                    {selectedTier && (
                        <p className="mt-3 text-sm text-slate-400">
                            <span className={tierConfig.color}>
                                {tierConfig.name} 티어:
                            </span>{' '}
                            {tierConfig.sla} 이상 체류시간 보장. 실패 시 자동 환불됩니다.
                        </p>
                    )}
                </div>
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
                        min={minBidForTier}
                        max="10000"
                        step="100"
                        value={localMaxBid}
                        onChange={(e) => {
                            const newValue = Number(e.target.value)
                            if (newValue >= minBidForTier) {
                                setLocalMaxBid(newValue)
                            }
                        }}
                        disabled={isLoading || isSaving}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                        <span className={tierConfig.color}>
                            {formatCurrency(minBidForTier)}원 (최소)
                        </span>
                        <span>10,000원</span>
                    </div>
                    {localMaxBid < minBidForTier && (
                        <p className="text-xs text-red-400 mt-1">
                            ⚠️ {tierConfig.name} 티어는 최소 {formatCurrency(minBidForTier)}원 입찰가가 필요합니다.
                        </p>
                    )}
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
                    disabled={isLoading || isSaving || (localDailyBudget === dailyBudget && localMaxBid === maxBidPerKeyword && selectedTier === currentTier) || localMaxBid < minBidForTier}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSaving ? '저장 중...' : '설정 저장'}
                </button>
                {status !== 'idle' && statusMessage && (
                    <div
                        role="status"
                        aria-live="polite"
                        className={`mt-4 rounded-lg border px-4 py-3 text-sm ${status === 'success'
                            ? 'border-[#4CAF50] bg-[#4CAF50]/10 text-[#4CAF50]'
                            : 'border-[#FFD700] bg-[#FFD700]/10 text-[#FFD700]'
                            }`}
                    >
                        {statusMessage}
                    </div>
                )}
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