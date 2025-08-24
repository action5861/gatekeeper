'use client'

import AdvertiserReviewCard from '@/components/admin/AdvertiserReviewCard'
import ApprovedAdvertiserCard from '@/components/admin/ApprovedAdvertiserCard'
import RejectedAdvertiserCard from '@/components/admin/RejectedAdvertiserCard'
import { AlertCircle, CheckCircle, RefreshCw, Shield, XCircle } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'

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
    const [rejectedAdvertisers, setRejectedAdvertisers] = useState<AdvertiserReviewData[]>([])
    const [approvedAdvertisers, setApprovedAdvertisers] = useState<AdvertiserReviewData[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [activeTab, setActiveTab] = useState<'pending' | 'rejected' | 'approved'>('pending')
    const router = useRouter()

    // 토큰 확인 및 리다이렉트 함수
    const checkTokenAndRedirect = useCallback(() => {
        if (typeof window === 'undefined') return null
        const token = localStorage.getItem('adminToken')
        if (!token) {
            router.push('/admin/login')
            return null
        }
        return token
    }, [router])

    // 승인된 광고주 조회 함수 개선
    const fetchApprovedAdvertisers = useCallback(async () => {
        console.log('=== fetchApprovedAdvertisers 시작 ===')

        const token = checkTokenAndRedirect()
        if (!token) return

        try {
            console.log('API 요청 전송 중...')
            const response = await fetch('/api/admin/advertiser-review?status=approved', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            console.log('응답 상태:', response.status)

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('adminToken')
                    router.push('/admin/login')
                    return
                }
                throw new Error(`HTTP ${response.status}: Failed to fetch approved advertisers`)
            }

            const data = await response.json()
            console.log('받은 데이터:', data)
            console.log('광고주 개수:', data.advertisers?.length || 0)

            // 상태 업데이트를 즉시 실행
            const approvedData = Array.isArray(data.advertisers) ? data.advertisers : []
            console.log('설정할 데이터:', approvedData)

            setApprovedAdvertisers(approvedData)

            // 상태 업데이트 확인을 위한 즉시 로그
            console.log('상태 업데이트 완료, 개수:', approvedData.length)

        } catch (err) {
            console.error('fetchApprovedAdvertisers 에러:', err)
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }, [checkTokenAndRedirect, router])

    // 대기 중인 심사 조회
    const fetchPendingReviews = useCallback(async () => {
        const token = checkTokenAndRedirect()
        if (!token) return

        try {
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
            setAdvertisers(Array.isArray(data.advertisers) ? data.advertisers : [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }, [checkTokenAndRedirect, router])

    // 거절된 광고주 조회
    const fetchRejectedAdvertisers = useCallback(async () => {
        const token = checkTokenAndRedirect()
        if (!token) return

        try {
            const response = await fetch('/api/admin/advertiser-review?status=rejected', {
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
                throw new Error('Failed to fetch rejected advertisers')
            }

            const data = await response.json()
            setRejectedAdvertisers(Array.isArray(data.advertisers) ? data.advertisers : [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }, [checkTokenAndRedirect, router])

    // 모든 데이터 로드
    const loadAllData = useCallback(async () => {
        setIsLoading(true)
        setError(null)

        try {
            await Promise.all([
                fetchPendingReviews(),
                fetchRejectedAdvertisers(),
                fetchApprovedAdvertisers()
            ])
        } catch (err) {
            console.error('데이터 로드 에러:', err)
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [fetchPendingReviews, fetchRejectedAdvertisers, fetchApprovedAdvertisers])

    // 탭별 데이터 로드
    const loadTabData = useCallback(async () => {
        if (activeTab === 'pending') {
            await fetchPendingReviews()
        } else if (activeTab === 'rejected') {
            await fetchRejectedAdvertisers()
        } else if (activeTab === 'approved') {
            await fetchApprovedAdvertisers()
        }
    }, [activeTab, fetchPendingReviews, fetchRejectedAdvertisers, fetchApprovedAdvertisers])

    // 심사 업데이트 처리
    const handleReviewUpdate = async (
        advertiserId: number,
        status: 'approved' | 'rejected',
        notes: string,
        bidRange: { min: number; max: number }
    ) => {
        try {
            if (typeof window === 'undefined') return
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

            // 성공 시 목록에서 제거하고 전체 데이터 다시 로드
            setAdvertisers(prev => prev.filter(adv => adv.advertiser_id !== advertiserId))

            // 승인/거절 상태에 따라 해당 목록 새로고침
            if (status === 'approved') {
                await fetchApprovedAdvertisers()
            } else {
                await fetchRejectedAdvertisers()
            }

            alert(`광고주 심사가 ${status === 'approved' ? '승인' : '거절'}되었습니다.`)

        } catch (error) {
            console.error('Review update failed:', error)
            alert('심사 업데이트에 실패했습니다.')
        }
    }

    // 광고주 데이터 업데이트
    const handleDataUpdate = async (
        advertiserId: number,
        keywords: string[],
        categories: number[]
    ) => {
        try {
            if (typeof window === 'undefined') return
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

    // 광고주 삭제
    const handleDeleteAdvertiser = async (advertiserId: number) => {
        if (typeof window === 'undefined') return
        if (!confirm('정말로 이 광고주를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
            return
        }

        try {
            const token = localStorage.getItem('adminToken')
            if (!token) return

            const response = await fetch(`/api/admin/advertiser-review/${advertiserId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                throw new Error('Failed to delete advertiser')
            }

            // 성공 시 목록에서 제거
            setRejectedAdvertisers(prev => prev.filter(adv => adv.advertiser_id !== advertiserId))
            alert('광고주가 삭제되었습니다.')

        } catch (error) {
            console.error('Delete failed:', error)
            alert('삭제에 실패했습니다.')
        }
    }

    // 새로고침 처리
    const handleRefresh = () => {
        setIsRefreshing(true)
        loadTabData()
    }

    // 초기 데이터 로드
    useEffect(() => {
        if (typeof window === 'undefined') return
        console.log('=== 컴포넌트 마운트, 초기 데이터 로드 ===')
        loadAllData()
    }, []) // 빈 의존성 배열로 한 번만 실행

    // 탭 변경 시 데이터 로드
    useEffect(() => {
        if (typeof window === 'undefined') return
        console.log('=== 탭 변경됨:', activeTab, '===')
        loadTabData()
    }, [activeTab, loadTabData])

    // 상태 변경 감지를 위한 디버깅 useEffect
    useEffect(() => {
        if (typeof window === 'undefined') return
        console.log('=== 승인된 광고주 상태 변경 감지 ===')
        console.log('현재 승인된 광고주 수:', approvedAdvertisers.length)
        console.log('승인된 광고주 목록:', approvedAdvertisers)
    }, [approvedAdvertisers])

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
                <div className="mb-8 grid grid-cols-1 md:grid-cols-4 gap-6">
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
                                    {approvedAdvertisers.length}
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
                                    {rejectedAdvertisers.length}
                                </p>
                                <p className="text-sm text-slate-400">거절됨</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-slate-500/20 rounded-lg flex items-center justify-center">
                                <Shield className="w-5 h-5 text-slate-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-100">
                                    {advertisers.length + approvedAdvertisers.length + rejectedAdvertisers.length}
                                </p>
                                <p className="text-sm text-slate-400">전체</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="mb-6">
                    <div className="border-b border-slate-700">
                        <nav className="-mb-px flex space-x-8">
                            <button
                                type="button"
                                onClick={() => setActiveTab('pending')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'pending'
                                    ? 'border-blue-500 text-blue-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                                    }`}
                            >
                                심사 대기 ({advertisers.length})
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('approved')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'approved'
                                    ? 'border-green-500 text-green-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                                    }`}
                            >
                                승인됨 ({approvedAdvertisers.length})
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('rejected')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'rejected'
                                    ? 'border-red-500 text-red-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                                    }`}
                            >
                                거절됨 ({rejectedAdvertisers.length})
                            </button>
                        </nav>
                    </div>
                </div>

                {/* Advertiser Cards */}
                {activeTab === 'pending' ? (
                    advertisers.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-8 h-8 text-green-400" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-100 mb-2">
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
                                    key={advertiser.advertiser_id}
                                    advertiser={advertiser}
                                    onReviewUpdate={handleReviewUpdate}
                                    onDataUpdate={handleDataUpdate}
                                />
                            ))}
                        </div>
                    )
                ) : activeTab === 'approved' ? (
                    approvedAdvertisers.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-8 h-8 text-green-400" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-100 mb-2">
                                승인된 광고주가 없습니다
                            </h3>
                            <p className="text-slate-400">
                                아직 승인된 광고주가 없습니다.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {approvedAdvertisers.map((advertiser) => (
                                <ApprovedAdvertiserCard
                                    key={advertiser.advertiser_id}
                                    advertiser={advertiser}
                                />
                            ))}
                        </div>
                    )
                ) : (
                    rejectedAdvertisers.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-8 h-8 text-green-400" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-100 mb-2">
                                거절된 광고주가 없습니다
                            </h3>
                            <p className="text-slate-400">
                                모든 광고주가 승인되었거나 아직 거절된 광고주가 없습니다.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {rejectedAdvertisers.map((advertiser) => (
                                <RejectedAdvertiserCard
                                    key={advertiser.advertiser_id}
                                    advertiser={advertiser}
                                    onDelete={handleDeleteAdvertiser}
                                />
                            ))}
                        </div>
                    )
                )}
            </div>
        </div>
    )
}