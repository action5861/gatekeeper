'use client'

import AdvertiserReviewCard from '@/components/admin/AdvertiserReviewCard'
import { AlertCircle, CheckCircle, RefreshCw, Shield, XCircle } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

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

export default function AdminAdvertiserReviewPage() {
    const [advertisers, setAdvertisers] = useState<AdvertiserReviewData[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const router = useRouter()

    const fetchPendingReviews = async () => {
        try {
            const token = localStorage.getItem('adminToken')
            if (!token) {
                router.push('/admin/login')
                return
            }

            const response = await fetch('/api/admin/advertiser-review', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('adminToken')
                    router.push('/admin/login')
                    return
                }
                throw new Error('Failed to fetch pending reviews')
            }

            const data = await response.json()
            setAdvertisers(data.advertisers || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }

    const handleReviewUpdate = async (
        advertiserId: number,
        status: 'approved' | 'rejected',
        notes: string,
        bidRange: { min: number; max: number }
    ) => {
        try {
            const token = localStorage.getItem('adminToken')
            if (!token) return

            const response = await fetch('/api/admin/advertiser-review', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    advertiser_id: advertiserId,
                    review_status: status,
                    review_notes: notes,
                    recommended_bid_min: bidRange.min,
                    recommended_bid_max: bidRange.max
                }),
            })

            if (!response.ok) {
                throw new Error('Failed to update review')
            }

            // 성공 시 목록에서 제거
            setAdvertisers(prev => prev.filter(adv => adv.advertiser_id !== advertiserId))

            // 성공 메시지
            alert(`광고주 심사가 ${status === 'approved' ? '승인' : '거절'}되었습니다.`)

        } catch (error) {
            console.error('Review update failed:', error)
            alert('심사 업데이트에 실패했습니다.')
        }
    }

    const handleDataUpdate = async (
        advertiserId: number,
        keywords: string[],
        categories: number[]
    ) => {
        try {
            const token = localStorage.getItem('adminToken')
            if (!token) return

            const response = await fetch('/api/admin/advertiser-review', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    advertiser_id: advertiserId,
                    keywords,
                    categories
                }),
            })

            if (!response.ok) {
                throw new Error('Failed to update advertiser data')
            }

            // 성공 시 로컬 상태 업데이트
            setAdvertisers(prev => prev.map(adv =>
                adv.advertiser_id === advertiserId
                    ? { ...adv, keywords, categories }
                    : adv
            ))

            alert('광고주 데이터가 업데이트되었습니다.')

        } catch (error) {
            console.error('Data update failed:', error)
            alert('데이터 업데이트에 실패했습니다.')
        }
    }

    const handleRefresh = () => {
        setIsRefreshing(true)
        fetchPendingReviews()
    }

    useEffect(() => {
        fetchPendingReviews()
    }, [])

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-900">
            {/* Header */}
            <div className="bg-slate-800/50 border-b border-slate-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                <Shield className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-100">
                                    광고주 심사 관리
                                </h1>
                                <p className="text-slate-400">
                                    심사 대기 중인 광고주 목록
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                            className="flex items-center space-x-2 px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 disabled:opacity-50 transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                            <span>새로고침</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                            <AlertCircle className="w-5 h-5 text-red-400" />
                            <p className="text-red-400">{error}</p>
                        </div>
                    </div>
                )}

                {/* Stats */}
                <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                <AlertCircle className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-100">
                                    {advertisers.length}
                                </p>
                                <p className="text-sm text-slate-400">심사 대기</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-green-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-100">
                                    {advertisers.filter(adv => adv.review_status === 'approved').length}
                                </p>
                                <p className="text-sm text-slate-400">승인됨</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                                <XCircle className="w-5 h-5 text-red-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-100">
                                    {advertisers.filter(adv => adv.review_status === 'rejected').length}
                                </p>
                                <p className="text-sm text-slate-400">거절됨</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Advertisers List */}
                {advertisers.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <CheckCircle className="w-8 h-8 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-300 mb-2">
                            심사 대기 중인 광고주가 없습니다
                        </h3>
                        <p className="text-slate-400">
                            모든 광고주 심사가 완료되었습니다.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {advertisers.map((advertiser) => (
                            <AdvertiserReviewCard
                                key={advertiser.id}
                                advertiser={advertiser}
                                onReviewUpdate={handleReviewUpdate}
                                onDataUpdate={handleDataUpdate}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
} 