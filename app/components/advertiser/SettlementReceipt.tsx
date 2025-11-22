'use client'

import { CheckCircle, Clock, Eye, FileText, MousePointerClick, Timer, X, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

interface SettlementMetrics {
    v_atf: number
    clicked: boolean
    t_dwell_on_ad_site: number
    created_at?: string | null
}

interface SettlementData {
    decision: string
    settled_amount: number
    settled_at?: string | null
    metrics: SettlementMetrics
}

interface SettlementReceiptData {
    bid_id: string
    search_query: string
    bid_amount: number
    bid_timestamp?: string | null
    transaction_id?: string | null
    user_id?: string | null
    primary_reward: number
    settlement?: SettlementData | null
}

interface SettlementReceiptProps {
    bidId: string
    isOpen: boolean
    onClose: () => void
}

export default function SettlementReceipt({ bidId, isOpen, onClose }: SettlementReceiptProps) {
    const [data, setData] = useState<SettlementReceiptData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchSettlementReceipt = async () => {
        if (!bidId) {
            setError('입찰 ID가 없습니다.')
            return
        }

        setLoading(true)
        setError(null)
        setData(null) // 이전 데이터 초기화
        
        try {
            const token = localStorage.getItem('token')
            if (!token) {
                setError('인증 토큰이 없습니다. 다시 로그인해주세요.')
                setLoading(false)
                return
            }

            console.log(`[SettlementReceipt] Fetching receipt for bidId: ${bidId}`)
            const response = await fetch(`/api/advertiser/settlement-receipt/${bidId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            })

            console.log(`[SettlementReceipt] Response status: ${response.status}`)

            if (!response.ok) {
                let errorMessage = '정산 영수증을 불러올 수 없습니다.'
                try {
                    const errorData = await response.json()
                    errorMessage = errorData.message || errorData.detail || errorMessage
                    console.error(`[SettlementReceipt] API error:`, errorData)
                } catch (parseError) {
                    const errorText = await response.text()
                    errorMessage = errorText || `서버 오류 (${response.status})`
                    console.error(`[SettlementReceipt] Failed to parse error response:`, errorText)
                }
                throw new Error(errorMessage)
            }

            const receiptData = await response.json()
            console.log(`[SettlementReceipt] Received data:`, receiptData)
            setData(receiptData)
        } catch (err) {
            console.error(`[SettlementReceipt] Error:`, err)
            setError(err instanceof Error ? err.message : '정산 영수증을 불러오는 중 오류가 발생했습니다.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isOpen && bidId) {
            fetchSettlementReceipt()
        } else if (!isOpen) {
            // 모달이 닫힐 때 데이터 초기화
            setData(null)
            setError(null)
            setLoading(false)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, bidId])

    const getDecisionIcon = (decision: string) => {
        switch (decision) {
            case 'PASSED':
                return <CheckCircle className="w-5 h-5 text-green-400" />
            case 'PARTIAL':
                return <Clock className="w-5 h-5 text-yellow-400" />
            case 'FAILED':
                return <XCircle className="w-5 h-5 text-red-400" />
            default:
                return <Clock className="w-5 h-5 text-slate-400" />
        }
    }

    const getDecisionColor = (decision: string) => {
        switch (decision) {
            case 'PASSED':
                return 'text-green-400 bg-green-400/10 border-green-400/20'
            case 'PARTIAL':
                return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
            case 'FAILED':
                return 'text-red-400 bg-red-400/10 border-red-400/20'
            default:
                return 'text-slate-400 bg-slate-400/10 border-slate-400/20'
        }
    }

    const getDecisionText = (decision: string) => {
        switch (decision) {
            case 'PASSED':
                return '정산 완료'
            case 'PARTIAL':
                return '부분 정산'
            case 'FAILED':
                return '정산 실패'
            default:
                return '대기 중'
        }
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
                {/* Header */}
                <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <FileText className="w-6 h-6 text-blue-400" />
                        <h2 className="text-xl font-bold text-slate-100">정산 영수증</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {loading && (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-4">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {data && !loading && (
                        <div className="space-y-6">
                            {/* 거래 기본 정보 */}
                            <div className="bg-slate-700/30 rounded-xl p-5 border border-slate-600">
                                <h3 className="text-lg font-semibold text-slate-100 mb-4">거래 정보</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-xs text-slate-400 mb-1">거래 ID</p>
                                        <p className="text-sm font-medium text-slate-200">{data.bid_id}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-400 mb-1">검색어</p>
                                        <p className="text-sm font-medium text-slate-200">{data.search_query}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-400 mb-1">입찰 금액</p>
                                        <p className="text-sm font-bold text-slate-100">{data.bid_amount.toLocaleString()}P</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-400 mb-1">거래 일시</p>
                                        <p className="text-sm font-medium text-slate-200">
                                            {data.bid_timestamp
                                                ? new Date(data.bid_timestamp).toLocaleString('ko-KR')
                                                : 'N/A'}
                                        </p>
                                    </div>
                                    {data.user_id && (
                                        <div>
                                            <p className="text-xs text-slate-400 mb-1">사용자 ID</p>
                                            <p className="text-sm font-medium text-slate-200">{data.user_id}</p>
                                        </div>
                                    )}
                                    {data.transaction_id && (
                                        <div>
                                            <p className="text-xs text-slate-400 mb-1">거래 내역 ID</p>
                                            <p className="text-sm font-medium text-slate-200">{data.transaction_id}</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* 정산 결과 */}
                            {data.settlement ? (
                                <>
                                    <div className="bg-slate-700/30 rounded-xl p-5 border border-slate-600">
                                        <h3 className="text-lg font-semibold text-slate-100 mb-4">정산 결과</h3>
                                        <div className="flex items-center space-x-3 mb-4">
                                            {getDecisionIcon(data.settlement.decision)}
                                            <div className={`px-4 py-2 rounded-lg border ${getDecisionColor(data.settlement.decision)}`}>
                                                <p className="text-sm font-semibold">
                                                    {getDecisionText(data.settlement.decision)}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-xs text-slate-400 mb-1">원래 보상</p>
                                                <p className="text-sm font-medium text-slate-200">
                                                    {data.primary_reward.toLocaleString()}P
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-slate-400 mb-1">정산 금액</p>
                                                <p className="text-lg font-bold text-blue-400">
                                                    {data.settlement.settled_amount.toLocaleString()}P
                                                </p>
                                            </div>
                                            {data.settlement.settled_at && (
                                                <div>
                                                    <p className="text-xs text-slate-400 mb-1">정산 일시</p>
                                                    <p className="text-sm font-medium text-slate-200">
                                                        {new Date(data.settlement.settled_at).toLocaleString('ko-KR')}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* SLA 지표 */}
                                    <div className="bg-slate-700/30 rounded-xl p-5 border border-slate-600">
                                        <h3 className="text-lg font-semibold text-slate-100 mb-4">SLA 지표</h3>
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between p-3 bg-slate-600/30 rounded-lg">
                                                <div className="flex items-center space-x-2">
                                                    <Eye className="w-4 h-4 text-slate-400" />
                                                    <span className="text-sm text-slate-300">가시성 지표 (v_atf)</span>
                                                </div>
                                                <span className="text-sm font-semibold text-slate-100">
                                                    {(data.settlement.metrics.v_atf * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-slate-600/30 rounded-lg">
                                                <div className="flex items-center space-x-2">
                                                    <MousePointerClick className="w-4 h-4 text-slate-400" />
                                                    <span className="text-sm text-slate-300">클릭 여부</span>
                                                </div>
                                                <span className={`text-sm font-semibold ${data.settlement.metrics.clicked ? 'text-green-400' : 'text-red-400'}`}>
                                                    {data.settlement.metrics.clicked ? '클릭됨' : '클릭 안됨'}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-slate-600/30 rounded-lg">
                                                <div className="flex items-center space-x-2">
                                                    <Timer className="w-4 h-4 text-slate-400" />
                                                    <span className="text-sm text-slate-300">체류시간</span>
                                                </div>
                                                <span className="text-sm font-semibold text-slate-100">
                                                    {data.settlement.metrics.t_dwell_on_ad_site.toFixed(2)}초
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-5">
                                    <p className="text-yellow-400 text-sm">정산 정보가 아직 없습니다. 정산이 완료되면 표시됩니다.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-slate-800 border-t border-slate-700 px-6 py-4 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        닫기
                    </button>
                </div>
            </div>
        </div>
    )
}

