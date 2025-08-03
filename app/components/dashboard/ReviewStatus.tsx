'use client'

import { AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

interface ReviewStatusData {
    review_status: string
    message: string
    created_at: string
    updated_at: string
    notes?: string
}

export default function ReviewStatus() {
    const [reviewData, setReviewData] = useState<ReviewStatusData | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
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

        fetchReviewStatus()
    }, [])

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

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'approved':
                return <CheckCircle className="w-6 h-6 text-green-400" />
            case 'rejected':
                return <XCircle className="w-6 h-6 text-red-400" />
            case 'in_progress':
                return <Clock className="w-6 h-6 text-yellow-400" />
            default:
                return <AlertCircle className="w-6 h-6 text-blue-400" />
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
                return '심사 중'
            default:
                return '심사 대기'
        }
    }

    return (
        <div className={`rounded-xl p-6 border ${getStatusColor(reviewData.review_status)}`}>
            <div className="flex items-center space-x-3 mb-4">
                {getStatusIcon(reviewData.review_status)}
                <div>
                    <h3 className="text-lg font-semibold text-slate-100">
                        심사 상태: {getStatusText(reviewData.review_status)}
                    </h3>
                    <p className="text-sm text-slate-400">
                        {new Date(reviewData.created_at).toLocaleDateString('ko-KR')} 등록
                    </p>
                </div>
            </div>

            <div className="space-y-3">
                <p className="text-slate-300 text-sm">
                    {reviewData.message}
                </p>

                {reviewData.notes && (
                    <div className="bg-slate-700/50 rounded-lg p-3">
                        <p className="text-xs text-slate-400 mb-1">심사 메모:</p>
                        <p className="text-sm text-slate-300">{reviewData.notes}</p>
                    </div>
                )}

                {reviewData.review_status === 'pending' && (
                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                        <p className="text-xs text-blue-400">
                            ⏰ 심사는 보통 24시간 이내에 완료됩니다. 심사가 완료되면 이메일로 알려드립니다.
                        </p>
                    </div>
                )}

                {reviewData.review_status === 'rejected' && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                        <p className="text-xs text-red-400">
                            ❌ 심사가 거부되었습니다. 자세한 내용은 고객센터로 문의해주세요.
                        </p>
                    </div>
                )}

                {reviewData.review_status === 'approved' && (
                    <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                        <p className="text-xs text-green-400">
                            ✅ 심사가 승인되었습니다! 이제 광고 등록이 가능합니다.
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
} 