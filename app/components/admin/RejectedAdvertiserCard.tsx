'use client'

import { Building2, Calendar, Globe, Trash2, XCircle } from 'lucide-react'
import { useState } from 'react'

interface RejectedAdvertiserData {
    id: number
    advertiser_id: number
    company_name: string
    email: string
    website_url: string
    daily_budget: number
    created_at: string
    keywords: string[]
    categories: number[]
    review_status: string
    review_notes?: string
    recommended_bid_min: number
    recommended_bid_max: number
}

interface RejectedAdvertiserCardProps {
    advertiser: RejectedAdvertiserData
    onDelete: (advertiserId: number) => void
}

export default function RejectedAdvertiserCard({
    advertiser,
    onDelete
}: RejectedAdvertiserCardProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    const handleDelete = async () => {
        setIsDeleting(true)
        try {
            await onDelete(advertiser.advertiser_id)
        } finally {
            setIsDeleting(false)
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const formatBudget = (budget: number) => {
        return new Intl.NumberFormat('ko-KR').format(budget)
    }

    return (
        <div className="bg-slate-800/50 rounded-xl border border-red-500/20 overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-slate-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                            <XCircle className="w-5 h-5 text-red-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-100">
                                {advertiser.company_name}
                            </h3>
                            <p className="text-sm text-slate-400">{advertiser.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="px-3 py-1 bg-red-500/20 text-red-400 text-sm rounded-full">
                            거절됨
                        </span>
                        <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="p-2 text-slate-400 hover:text-slate-300 transition-colors"
                        >
                            {isExpanded ? '접기' : '펼치기'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="p-6 space-y-6">
                    {/* Basic Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <div className="flex items-center space-x-3">
                                <Globe className="w-5 h-5 text-slate-400" />
                                <div>
                                    <p className="text-sm text-slate-400">웹사이트</p>
                                    <p className="text-slate-100">{advertiser.website_url}</p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-3">
                                <Calendar className="w-5 h-5 text-slate-400" />
                                <div>
                                    <p className="text-sm text-slate-400">등록일</p>
                                    <p className="text-slate-100">{formatDate(advertiser.created_at)}</p>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center space-x-3">
                                <Building2 className="w-5 h-5 text-slate-400" />
                                <div>
                                    <p className="text-sm text-slate-400">일일 예산</p>
                                    <p className="text-slate-100">₩{formatBudget(advertiser.daily_budget)}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Keywords */}
                    <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-3">키워드</h4>
                        <div className="flex flex-wrap gap-2">
                            {advertiser.keywords.map((keyword, index) => (
                                <span
                                    key={index}
                                    className="px-3 py-1 bg-slate-700/50 text-slate-300 text-sm rounded-full"
                                >
                                    {keyword}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Rejection Notes */}
                    {advertiser.review_notes && (
                        <div>
                            <h4 className="text-sm font-medium text-slate-300 mb-3">거절 사유</h4>
                            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                                <p className="text-red-300">{advertiser.review_notes}</p>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-700">
                        <button
                            onClick={handleDelete}
                            disabled={isDeleting}
                            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span>{isDeleting ? '삭제 중...' : '완전 삭제'}</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
} 