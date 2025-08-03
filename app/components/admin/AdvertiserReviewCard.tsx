'use client'

import { Building2, Calendar, CheckCircle, Globe, XCircle } from 'lucide-react'
import { useState } from 'react'
import CategorySelector from './CategorySelector'
import KeywordEditor from './KeywordEditor'
import WebsitePreview from './WebsitePreview'

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

interface AdvertiserReviewCardProps {
    advertiser: AdvertiserReviewData
    onReviewUpdate: (advertiserId: number, status: 'approved' | 'rejected', notes: string, bidRange: { min: number; max: number }) => void
    onDataUpdate: (advertiserId: number, keywords: string[], categories: number[]) => void
}

export default function AdvertiserReviewCard({
    advertiser,
    onReviewUpdate,
    onDataUpdate
}: AdvertiserReviewCardProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [reviewNotes, setReviewNotes] = useState(advertiser.review_notes || '')
    const [bidRange, setBidRange] = useState({
        min: advertiser.recommended_bid_min,
        max: advertiser.recommended_bid_max
    })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [editingKeywords, setEditingKeywords] = useState(advertiser.keywords)
    const [editingCategories, setEditingCategories] = useState(advertiser.categories)

    const handleApprove = async () => {
        setIsSubmitting(true)
        try {
            await onReviewUpdate(advertiser.advertiser_id, 'approved', reviewNotes, bidRange)
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleReject = async () => {
        if (!reviewNotes.trim()) {
            alert('거절 사유를 입력해주세요')
            return
        }

        setIsSubmitting(true)
        try {
            await onReviewUpdate(advertiser.advertiser_id, 'rejected', reviewNotes, bidRange)
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleDataUpdate = async () => {
        setIsSubmitting(true)
        try {
            await onDataUpdate(advertiser.advertiser_id, editingKeywords, editingCategories)
        } finally {
            setIsSubmitting(false)
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
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-slate-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-100">
                                {advertiser.company_name}
                            </h3>
                            <p className="text-sm text-slate-400">{advertiser.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-400">
                            {formatDate(advertiser.created_at)}
                        </span>
                        <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="p-2 text-slate-400 hover:text-slate-300 transition-colors"
                        >
                            {isExpanded ? '접기' : '펼치기'}
                        </button>
                    </div>
                </div>

                {/* Basic Info */}
                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center space-x-2">
                        <Globe className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-300 truncate">
                            {advertiser.website_url}
                        </span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-300">
                            일일 예산: {formatBudget(advertiser.daily_budget)}원
                        </span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-300">
                            키워드: {advertiser.keywords.length}개
                        </span>
                    </div>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="p-6 space-y-6">
                    {/* Website Preview */}
                    <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-3">웹사이트 미리보기</h4>
                        <WebsitePreview url={advertiser.website_url} />
                    </div>

                    {/* Keywords and Categories */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <KeywordEditor
                                keywords={editingKeywords}
                                onKeywordsChange={setEditingKeywords}
                                maxKeywords={20}
                            />
                        </div>
                        <div>
                            <CategorySelector
                                categories={editingCategories}
                                onCategoriesChange={setEditingCategories}
                                maxCategories={3}
                            />
                        </div>
                    </div>

                    {/* Data Update Button */}
                    <div className="flex justify-end">
                        <button
                            onClick={handleDataUpdate}
                            disabled={isSubmitting}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                            {isSubmitting ? '업데이트 중...' : '데이터 업데이트'}
                        </button>
                    </div>

                    {/* Review Section */}
                    <div className="border-t border-slate-700 pt-6">
                        <h4 className="text-sm font-medium text-slate-300 mb-4">심사 결정</h4>

                        {/* Bid Range */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                추천 입찰가 범위
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">최소 입찰가</label>
                                    <input
                                        type="number"
                                        value={bidRange.min}
                                        onChange={(e) => setBidRange(prev => ({ ...prev, min: Number(e.target.value) }))}
                                        className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">최대 입찰가</label>
                                    <input
                                        type="number"
                                        value={bidRange.max}
                                        onChange={(e) => setBidRange(prev => ({ ...prev, max: Number(e.target.value) }))}
                                        className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Review Notes */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                심사 메모
                            </label>
                            <textarea
                                value={reviewNotes}
                                onChange={(e) => setReviewNotes(e.target.value)}
                                placeholder="심사 결과에 대한 메모를 입력하세요..."
                                rows={4}
                                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center justify-end space-x-3">
                            <button
                                onClick={handleReject}
                                disabled={isSubmitting || !reviewNotes.trim()}
                                className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                            >
                                <XCircle className="w-4 h-4" />
                                <span>거절</span>
                            </button>
                            <button
                                onClick={handleApprove}
                                disabled={isSubmitting}
                                className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                            >
                                <CheckCircle className="w-4 h-4" />
                                <span>승인</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
} 