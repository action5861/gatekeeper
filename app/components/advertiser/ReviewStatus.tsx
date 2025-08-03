'use client'

import { AlertCircle, CheckCircle, Clock, FileText, RefreshCw, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

interface ReviewStatusData {
    review_status: string
    message: string
    created_at: string
    updated_at: string
    notes?: string
    estimated_completion?: string
}

interface ReviewStatusProps {
    onStatusChange?: (status: string) => void
}

export default function ReviewStatus({ onStatusChange }: ReviewStatusProps) {
    const [reviewData, setReviewData] = useState<ReviewStatusData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [timeRemaining, setTimeRemaining] = useState<string>('')
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        fetchReviewStatus()
        const interval = setInterval(updateTimeRemaining, 1000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        if (reviewData) {
            updateTimeRemaining()
            updateProgress()
            onStatusChange?.(reviewData.review_status)
        }
    }, [reviewData])

    const fetchReviewStatus = async () => {
        try {
            const token = localStorage.getItem('token')
            if (!token) return

            const response = await fetch('/api/advertiser/review-status', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (response.ok) {
                const data = await response.json()
                setReviewData(data)
            }
        } catch (error) {
            console.error('Failed to fetch review status:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const updateTimeRemaining = () => {
        if (!reviewData || reviewData.review_status !== 'pending') return

        const created = new Date(reviewData.created_at)
        const estimated = new Date(created.getTime() + 24 * 60 * 60 * 1000) // 24시간 후
        const now = new Date()
        const diff = estimated.getTime() - now.getTime()

        if (diff <= 0) {
            setTimeRemaining('곧 완료 예정')
        } else {
            const hours = Math.floor(diff / (1000 * 60 * 60))
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
            setTimeRemaining(`${hours}시간 ${minutes}분 남음`)
        }
    }

    const updateProgress = () => {
        if (!reviewData || reviewData.review_status !== 'pending') return

        const created = new Date(reviewData.created_at)
        const estimated = new Date(created.getTime() + 24 * 60 * 60 * 1000)
        const now = new Date()
        const total = 24 * 60 * 60 * 1000
        const elapsed = now.getTime() - created.getTime()

        const progressPercent = Math.min((elapsed / total) * 100, 95) // 최대 95%까지만
        setProgress(progressPercent)
    }

    const handleResubmit = async () => {
        // 재신청 로직
        alert('재신청 기능은 준비 중입니다.')
    }

    const handleAdditionalInfo = async () => {
        // 추가 정보 제출 로직
        alert('추가 정보 제출 기능은 준비 중입니다.')
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'approved':
                return <CheckCircle className="w-8 h-8 text-green-400" />
            case 'rejected':
                return <XCircle className="w-8 h-8 text-red-400" />
            case 'in_progress':
                return <Clock className="w-8 h-8 text-yellow-400" />
            default:
                return <AlertCircle className="w-8 h-8 text-blue-400" />
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'approved':
                return 'border-green-500/20 bg-green-500/10'
            case 'rejected':
                return 'border-red-500/20 bg-red-500/10'
            case 'in_progress':
                return 'border-yellow-500/20 bg-yellow-500/10'
            default:
                return 'border-blue-500/20 bg-blue-500/10'
        }
    }

    const getStatusText = (status: string) => {
        switch (status) {
            case 'approved':
                return '승인됨'
            case 'rejected':
                return '거부됨'
            case 'in_progress':
                return '심사 진행 중'
            default:
                return '심사 대기 중'
        }
    }

    if (isLoading) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-center h-16">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    if (!reviewData) {
        return null
    }

    return (
        <div className={`rounded-xl p-6 border ${getStatusColor(reviewData.review_status)}`}>
            {/* Header */}
            <div className="flex items-center space-x-4 mb-6">
                {getStatusIcon(reviewData.review_status)}
                <div className="flex-1">
                    <h2 className="text-xl font-semibold text-slate-100">
                        심사 상태: {getStatusText(reviewData.review_status)}
                    </h2>
                    <p className="text-sm text-slate-400">
                        {new Date(reviewData.created_at).toLocaleDateString('ko-KR')} 등록
                    </p>
                </div>
                <button
                    onClick={fetchReviewStatus}
                    className="p-2 text-slate-400 hover:text-slate-300 transition-colors"
                    title="새로고침"
                >
                    <RefreshCw className="w-5 h-5" />
                </button>
            </div>

            {/* Status Specific Content */}
            {reviewData.review_status === 'pending' && (
                <div className="space-y-4">
                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                            <Clock className="w-5 h-5 text-blue-400" />
                            <span className="text-blue-400 font-medium">예상 완료 시간</span>
                        </div>
                        <p className="text-blue-300 text-lg font-semibold">{timeRemaining}</p>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm text-slate-400">
                            <span>심사 진행률</span>
                            <span>{Math.round(progress)}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="bg-slate-700/50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-slate-300 mb-2">심사 안내</h3>
                        <ul className="text-sm text-slate-400 space-y-1">
                            <li>• 심사는 보통 24시간 이내에 완료됩니다</li>
                            <li>• 심사가 완료되면 이메일로 알려드립니다</li>
                            <li>• 심사 중에는 광고 등록이 제한됩니다</li>
                        </ul>
                    </div>
                </div>
            )}

            {reviewData.review_status === 'in_progress' && (
                <div className="space-y-4">
                    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                            <Clock className="w-5 h-5 text-yellow-400" />
                            <span className="text-yellow-400 font-medium">심사 진행 중</span>
                        </div>
                        <p className="text-yellow-300">현재 심사가 진행 중입니다. 곧 완료될 예정입니다.</p>
                    </div>

                    <div className="bg-slate-700/50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-slate-300 mb-2">진행 상황</h3>
                        <ul className="text-sm text-slate-400 space-y-1">
                            <li>• 웹사이트 검토 완료</li>
                            <li>• 키워드 및 카테고리 검토 중</li>
                            <li>• 최종 승인 절차 진행 중</li>
                        </ul>
                    </div>
                </div>
            )}

            {reviewData.review_status === 'rejected' && (
                <div className="space-y-4">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                            <XCircle className="w-5 h-5 text-red-400" />
                            <span className="text-red-400 font-medium">심사 거부</span>
                        </div>
                        {reviewData.notes && (
                            <div className="mt-3">
                                <p className="text-sm text-red-300 font-medium mb-1">거부 사유:</p>
                                <p className="text-sm text-red-300">{reviewData.notes}</p>
                            </div>
                        )}
                    </div>

                    <div className="flex space-x-3">
                        <button
                            onClick={handleResubmit}
                            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                            <FileText className="w-4 h-4" />
                            <span>재신청</span>
                        </button>
                        <button
                            onClick={handleAdditionalInfo}
                            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            <FileText className="w-4 h-4" />
                            <span>추가 정보 제출</span>
                        </button>
                    </div>
                </div>
            )}

            {reviewData.review_status === 'approved' && (
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="text-green-400 font-medium">심사 승인</span>
                    </div>
                    <p className="text-green-300">축하합니다! 심사가 승인되었습니다. 이제 광고 등록이 가능합니다.</p>
                </div>
            )}

            {/* Common Message */}
            <div className="mt-6 pt-4 border-t border-slate-700">
                <p className="text-slate-300 text-sm">
                    {reviewData.message}
                </p>
            </div>
        </div>
    )
} 