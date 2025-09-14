'use client'

import { AlertCircle, CheckCircle, Clock, ToggleLeft, TrendingUp } from 'lucide-react'
import { useState } from 'react'

interface AutoBidToggleProps {
    isEnabled: boolean
    onToggle: (enabled: boolean) => void
    isLoading?: boolean
}

export default function AutoBidToggle({ isEnabled, onToggle, isLoading = false }: AutoBidToggleProps) {
    const [isToggling, setIsToggling] = useState(false)

    const handleToggle = async () => {
        setIsToggling(true)
        try {
            await onToggle(!isEnabled)
        } finally {
            setIsToggling(false)
        }
    }

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isEnabled ? 'bg-green-500/20' : 'bg-slate-600/20'
                        }`}>
                        {isEnabled ? (
                            <TrendingUp className="w-5 h-5 text-green-400" />
                        ) : (
                            <Clock className="w-5 h-5 text-slate-400" />
                        )}
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-100">
                            자동 입찰 시스템
                        </h3>
                        <p className="text-sm text-slate-400">
                            {isEnabled ? '활성화됨' : '비활성화됨'}
                        </p>
                    </div>
                </div>
                <ToggleLeft
                    checked={isEnabled}
                    onCheckedChange={handleToggle}
                    disabled={isLoading || isToggling}
                    className={`${isEnabled ? 'bg-green-500' : 'bg-slate-600'
                        } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50`}
                >
                    <span
                        className={`${isEnabled ? 'translate-x-6' : 'translate-x-1'
                            } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                    />
                </ToggleLeft>
            </div>

            {/* 상태별 설명 */}
            {isEnabled ? (
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="text-green-400 font-medium">자동 입찰 활성화됨</span>
                    </div>
                    <ul className="text-sm text-green-300 space-y-1">
                        <li>• 설정된 키워드에 자동으로 입찰합니다</li>
                        <li>• 예산 한도 내에서 최적의 입찰가를 제시합니다</li>
                        <li>• 실시간으로 매칭되는 검색어에 참여합니다</li>
                    </ul>
                </div>
            ) : (
                <div className="bg-slate-600/20 border border-slate-600/30 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <AlertCircle className="w-5 h-5 text-slate-400" />
                        <span className="text-slate-400 font-medium">자동 입찰 비활성화됨</span>
                    </div>
                    <ul className="text-sm text-slate-300 space-y-1">
                        <li>• 수동으로만 입찰에 참여할 수 있습니다</li>
                        <li>• 자동 입찰을 활성화하면 더 많은 기회를 얻을 수 있습니다</li>
                        <li>• 설정을 완료한 후 활성화하세요</li>
                    </ul>
                </div>
            )}

            {/* 로딩 상태 */}
            {(isLoading || isToggling) && (
                <div className="mt-4 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
                    <span className="ml-2 text-sm text-slate-400">
                        {isToggling ? '설정 업데이트 중...' : '로딩 중...'}
                    </span>
                </div>
            )}
        </div>
    )
} 