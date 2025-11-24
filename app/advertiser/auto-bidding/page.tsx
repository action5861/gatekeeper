'use client'

import Header from '@/components/Header'
import AutoBidAnalytics from '@/components/advertiser/AutoBidAnalytics'
import AutoBidToggle from '@/components/advertiser/AutoBidToggle'
import BidHistory from '@/components/advertiser/BidHistory'
import BudgetControl from '@/components/advertiser/BudgetControl'
import KeywordManager from '@/components/advertiser/KeywordManager'
import { BarChart3, Brain, Settings } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface AutoBidSettings {
    isEnabled: boolean
    dailyBudget: number
    maxBidPerKeyword: number
    minQualityScore: number
    excludedKeywords: string[]
}

interface Keyword {
    id: number
    keyword: string
    priority: number
    match_type: 'exact' | 'phrase' | 'broad'
    status: 'active' | 'paused'
}

interface BidHistoryItem {
    id: string
    searchQuery: string
    bidAmount: number
    result: 'won' | 'lost' | 'pending'
    timestamp: string
    matchScore: number
    qualityScore: number
    isAutoBid: boolean
}

export default function AutoBiddingPage() {
    const [settings, setSettings] = useState<AutoBidSettings>({
        isEnabled: false,
        dailyBudget: 10000,
        maxBidPerKeyword: 3000,
        minQualityScore: 50,
        excludedKeywords: []
    })
    const [keywords, setKeywords] = useState<Keyword[]>([])
    const [bidHistory, setBidHistory] = useState<BidHistoryItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [activeTab, setActiveTab] = useState<'settings' | 'history' | 'analytics'>('settings')
    const [advertiserId, setAdvertiserId] = useState<number | null>(null)
    const router = useRouter()

    useEffect(() => {
        fetchAutoBidData()
    }, [])

    const fetchAutoBidData = async () => {
        try {
            const token = localStorage.getItem('token')
            if (!token) {
                router.push('/login')
                return
            }

            // 자동 입찰 설정 조회
            const settingsResponse = await fetch('/api/advertiser/auto-bidding', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (!settingsResponse.ok) {
                if (settingsResponse.status === 401) {
                    localStorage.removeItem('token')
                    localStorage.removeItem('userType')
                    router.push('/login')
                    return
                }
                throw new Error('Failed to fetch auto bid settings')
            }

            const settingsData = await settingsResponse.json()

            if (settingsData.success) {
                const autoBidSettings = settingsData.data.autoBidSettings
                setSettings({
                    isEnabled: autoBidSettings.is_enabled || false,
                    dailyBudget: autoBidSettings.daily_budget || 10000,
                    maxBidPerKeyword: autoBidSettings.max_bid_per_keyword || 3000,
                    minQualityScore: autoBidSettings.min_quality_score || 50,
                    excludedKeywords: autoBidSettings.excluded_keywords || []
                })
                setKeywords(settingsData.data.keywords || [])

                // 광고주 ID 설정
                const advertiserResponse = await fetch('/api/advertiser/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                })
                if (advertiserResponse.ok) {
                    const advertiserData = await advertiserResponse.json()
                    setAdvertiserId(advertiserData.id)
                }
            }

            // 입찰 내역 조회
            const historyResponse = await fetch('/api/advertiser/bid-history', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            })

            if (historyResponse.ok) {
                const historyData = await historyResponse.json()
                if (historyData.success) {
                    setBidHistory(historyData.data.bidHistory || [])
                }
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const handleAutoBidToggle = async (enabled: boolean) => {
        try {
            const token = localStorage.getItem('token')
            if (!token) return

            const response = await fetch('/api/advertiser/auto-bidding', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    isEnabled: enabled,
                    dailyBudget: settings.dailyBudget,
                    maxBidPerKeyword: settings.maxBidPerKeyword,
                    minQualityScore: settings.minQualityScore,
                    keywords: keywords,
                    excludedKeywords: settings.excludedKeywords
                }),
            })

            if (response.ok) {
                setSettings(prev => ({ ...prev, isEnabled: enabled }))
            } else {
                throw new Error('Failed to update auto bid settings')
            }
        } catch (error) {
            console.error('Error updating auto bid toggle:', error)
            alert('자동 입찰 설정 업데이트에 실패했습니다.')
        }
    }

    const handleBudgetChange = async (dailyBudget: number, maxBidPerKeyword: number): Promise<boolean> => {
        try {
            const token = localStorage.getItem('token')
            if (!token) return false

            const response = await fetch('/api/advertiser/auto-bidding', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    isEnabled: settings.isEnabled,
                    dailyBudget,
                    maxBidPerKeyword,
                    minQualityScore: settings.minQualityScore,
                    keywords: keywords,
                    excludedKeywords: settings.excludedKeywords
                }),
            })

            if (response.ok) {
                setSettings(prev => ({
                    ...prev,
                    dailyBudget,
                    maxBidPerKeyword
                }))
                return true
            } else {
                const errorPayload = await response.text()
                console.error('Failed to update budget settings:', errorPayload)
                return false
            }
        } catch (error) {
            console.error('Error updating budget settings:', error)
            return false
        }
    }

    const handleKeywordsChange = async (newKeywords: Keyword[]) => {
        try {
            const token = localStorage.getItem('token')
            if (!token) return

            const response = await fetch('/api/advertiser/auto-bidding', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    isEnabled: settings.isEnabled,
                    dailyBudget: settings.dailyBudget,
                    maxBidPerKeyword: settings.maxBidPerKeyword,
                    minQualityScore: settings.minQualityScore,
                    keywords: newKeywords,
                    excludedKeywords: settings.excludedKeywords
                }),
            })

            if (response.ok) {
                setKeywords(newKeywords)
            } else {
                throw new Error('Failed to update keywords')
            }
        } catch (error) {
            console.error('Error updating keywords:', error)
            alert('키워드 설정 업데이트에 실패했습니다.')
        }
    }

    const handleExcludedKeywordsChange = async (excludedKeywords: string[]) => {
        try {
            const token = localStorage.getItem('token')
            if (!token) return

            const response = await fetch('/api/advertiser/auto-bidding', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    isEnabled: settings.isEnabled,
                    dailyBudget: settings.dailyBudget,
                    maxBidPerKeyword: settings.maxBidPerKeyword,
                    minQualityScore: settings.minQualityScore,
                    keywords: keywords,
                    excludedKeywords
                }),
            })

            if (response.ok) {
                setSettings(prev => ({ ...prev, excludedKeywords }))
            } else {
                throw new Error('Failed to update excluded keywords')
            }
        } catch (error) {
            console.error('Error updating excluded keywords:', error)
            alert('제외 키워드 설정 업데이트에 실패했습니다.')
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
                    </div>
                </main>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="text-center text-red-400">
                        <p>Error loading auto bidding: {error}</p>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-900">
            <Header />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Page Title */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-100 mb-2">자동 입찰 관리</h1>
                    <p className="text-slate-400">자동 입찰 설정과 성과를 관리하세요</p>
                </div>

                {/* Tab Navigation */}
                <div className="flex space-x-1 bg-slate-800/50 rounded-lg p-1 mb-8">
                    <button
                        onClick={() => setActiveTab('settings')}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === 'settings'
                            ? 'bg-blue-600 text-white'
                            : 'text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <Settings className="w-4 h-4" />
                        <span>설정</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('history')}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === 'history'
                            ? 'bg-blue-600 text-white'
                            : 'text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <BarChart3 className="w-4 h-4" />
                        <span>입찰 내역</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('analytics')}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === 'analytics'
                            ? 'bg-blue-600 text-white'
                            : 'text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <Brain className="w-4 h-4" />
                        <span>AI 분석</span>
                    </button>
                </div>

                {/* Settings Tab */}
                {activeTab === 'settings' && (
                    <div className="space-y-8">
                        {/* Auto Bid Toggle */}
                        <AutoBidToggle
                            isEnabled={settings.isEnabled}
                            onToggle={handleAutoBidToggle}
                            isLoading={isLoading}
                        />

                        {/* Budget Control */}
                        <BudgetControl
                            dailyBudget={settings.dailyBudget}
                            maxBidPerKeyword={settings.maxBidPerKeyword}
                            onBudgetChange={handleBudgetChange}
                            isLoading={isLoading}
                        />

                        {/* Keyword Manager */}
                        <KeywordManager
                            keywords={keywords}
                            excludedKeywords={settings.excludedKeywords}
                            onKeywordsChange={handleKeywordsChange}
                            onExcludedKeywordsChange={handleExcludedKeywordsChange}
                            isLoading={isLoading}
                        />
                    </div>
                )}

                {/* History Tab */}
                {activeTab === 'history' && (
                    <BidHistory
                        bidHistory={bidHistory}
                        isLoading={isLoading}
                    />
                )}

                {/* Analytics Tab */}
                {activeTab === 'analytics' && advertiserId && (
                    <AutoBidAnalytics
                        advertiserId={advertiserId}
                        timeRange="week"
                    />
                )}
            </main>
        </div>
    )
} 