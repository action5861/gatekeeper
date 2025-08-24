'use client'

import { Calendar, CheckCircle, Clock, DollarSign, FileText, Globe, Tag } from 'lucide-react'
import { useState } from 'react'

interface AdvertiserReviewData {
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

interface ApprovedAdvertiserCardProps {
    advertiser: AdvertiserReviewData
}

export default function ApprovedAdvertiserCard({ advertiser }: ApprovedAdvertiserCardProps) {
    const [isExpanded, setIsExpanded] = useState(false)

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    return (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                            <CheckCircle className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-100">
                                {advertiser.company_name}
                            </h3>
                            <p className="text-slate-400">{advertiser.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-4">
                        <div className="text-right">
                            <div className="flex items-center space-x-2 text-slate-400">
                                <Calendar className="w-4 h-4" />
                                <span className="text-sm">일일 예산: {advertiser.daily_budget.toLocaleString()}원</span>
                            </div>
                            <div className="flex items-center space-x-2 text-slate-400 mt-1">
                                <Tag className="w-4 h-4" />
                                <span className="text-sm">키워드: {advertiser.keywords.length}개</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-slate-400">{formatDate(advertiser.created_at)}</p>
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="text-blue-400 hover:text-blue-300 text-sm mt-1"
                            >
                                {isExpanded ? '접기' : '펼치기'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Website URL */}
                <div className="mt-4 flex items-center space-x-2">
                    <Globe className="w-4 h-4 text-slate-400" />
                    <a
                        href={advertiser.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                        {advertiser.website_url}
                    </a>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="border-t border-slate-700 p-6 bg-slate-800/30">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Keywords */}
                        <div>
                            <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                                <Tag className="w-4 h-4" />
                                <span>키워드</span>
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {advertiser.keywords.map((keyword, index) => (
                                    <span
                                        key={index}
                                        className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm"
                                    >
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Categories */}
                        <div>
                            <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                                <FileText className="w-4 h-4" />
                                <span>카테고리</span>
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {advertiser.categories.map((category, index) => (
                                    <span
                                        key={index}
                                        className="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-sm"
                                    >
                                        {category.toString()}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Bid Range */}
                        <div>
                            <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                                <DollarSign className="w-4 h-4" />
                                <span>권장 입찰 범위</span>
                            </h4>
                            <div className="bg-slate-700/50 rounded-lg p-3">
                                <p className="text-slate-300 text-sm">
                                    최소: {advertiser.recommended_bid_min.toLocaleString()}원
                                </p>
                                <p className="text-slate-300 text-sm">
                                    최대: {advertiser.recommended_bid_max.toLocaleString()}원
                                </p>
                            </div>
                        </div>

                        {/* Review Notes */}
                        {advertiser.review_notes && (
                            <div>
                                <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                                    <FileText className="w-4 h-4" />
                                    <span>심사 노트</span>
                                </h4>
                                <div className="bg-slate-700/50 rounded-lg p-3">
                                    <p className="text-slate-300 text-sm">{advertiser.review_notes}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Status Badge */}
                    <div className="mt-6 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <CheckCircle className="w-5 h-5 text-green-400" />
                            <span className="text-green-400 font-medium">승인됨</span>
                        </div>
                        <div className="flex items-center space-x-2 text-slate-400">
                            <Clock className="w-4 h-4" />
                            <span className="text-sm">승인일: {formatDate(advertiser.created_at)}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
} 