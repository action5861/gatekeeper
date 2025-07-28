// 메인 페이지

'use client'

import { useState, useEffect, useCallback } from 'react'
import Header from '@/components/Header'
import SearchInput from '@/components/main/SearchInput'
import QualityAdvisor from '@/components/main/QualityAdvisor'
import AuctionStatus from '@/components/main/AuctionStatus'
import { QualityReport, Auction } from '@/lib/types'

export default function Home() {
  // 상태 관리
  const [query, setQuery] = useState('')
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)
  const [auction, setAuction] = useState<Auction | null>(null)
  const [selectedBid, setSelectedBid] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // 알림 표시 함수
  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 5000) // 5초 후 자동 제거
  }

  // Debounce를 위한 useEffect
  useEffect(() => {
    if (!query.trim()) {
      setQualityReport(null)
      return
    }

    setIsEvaluating(true)
    const timer = setTimeout(async () => {
      try {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: query.trim() }),
        })

        const data = await response.json()
        
        if (data.success) {
          setQualityReport(data.data.qualityReport)
        } else {
          console.error('Quality evaluation failed:', data.error)
          setQualityReport(null)
        }
      } catch (error) {
        console.error('Quality evaluation error:', error)
        setQualityReport(null)
      } finally {
        setIsEvaluating(false)
      }
    }, 500) // 0.5초 debounce

    return () => clearTimeout(timer)
  }, [query])

  // 검색어 변경 처리
  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery)
  }, [])

  // 폼 제출 처리 (경매 시작)
  const handleSearchSubmit = useCallback(async (searchQuery: string) => {
    setIsLoading(true)
    setAuction(null) // 이전 경매 초기화
    setSelectedBid(null) // 선택된 입찰 초기화
    
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      })

      const data = await response.json()
      
      if (data.success) {
        setQualityReport(data.data.qualityReport)
        setAuction(data.data.auction)
        showNotification('success', 'Reverse auction started successfully!')
      } else {
        console.error('Search failed:', data.error)
        showNotification('error', data.error || 'Failed to start auction')
      }
    } catch (error) {
      console.error('Search error:', error)
      showNotification('error', 'Network error occurred')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 입찰 선택 처리
  const handleBidSelect = useCallback(async (bidId: string) => {
    if (!auction) return
    
    console.log('Bid selection started:', { bidId, auction });
    
    setIsLoading(true)
    try {
      // 1. 입찰 선택 처리
      const auctionResponse = await fetch('/api/auction/select', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          searchId: auction.searchId,
          selectedBidId: bidId,
        }),
      })

      const auctionData = await auctionResponse.json()
      
      if (auctionData.success) {
        setSelectedBid(bidId)
        const rewardAmount = auctionData.data.rewardAmount
        
        // 2. 보상 지급 처리 (거래 내역에 추가)
        const selectedBid = auction.bids.find(bid => bid.id === bidId)
        console.log('Selected bid info:', { 
          selectedBid, 
          auctionQuery: auction.query, 
          buyerName: selectedBid?.buyerName 
        });
        
        const rewardResponse = await fetch('/api/reward', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            bidId: bidId,
            amount: rewardAmount,
            query: auction.query,
            buyerName: selectedBid?.buyerName || 'Unknown Buyer'
          }),
        })

        const rewardData = await rewardResponse.json()
        
        if (rewardData.success) {
          showNotification('success', `1차 보상 지급 완료! ${rewardAmount.toLocaleString()}원이 지급되었습니다. 대시보드에서 2차 보상을 신청할 수 있습니다.`)
          
          // 대시보드 업데이트 이벤트 발생
          window.dispatchEvent(new CustomEvent('reward-updated'))
        } else {
          showNotification('error', '보상 지급에 실패했습니다.')
        }
      } else {
        showNotification('error', auctionData.error || '입찰 선택에 실패했습니다.')
      }
    } catch (error) {
      console.error('Bid selection error:', error)
      showNotification('error', '입찰 선택 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [auction])

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <Header />
      
      {/* Notification */}
      {notification && (
        <div className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 ${
          notification.type === 'success' 
            ? 'bg-green-600 text-white' 
            : 'bg-red-600 text-white'
        }`}>
          {notification.message}
        </div>
      )}
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="text-center mb-12 animate-fadeInUp">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-green-400 to-purple-400 bg-clip-text text-transparent">
            Trade Your Search Data
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Transform your search queries into valuable assets. Get real-time bids from data buyers 
            and earn rewards for your digital footprint.
          </p>
        </section>

        {/* Main Components Area */}
        <div className="space-y-8 animate-fadeInUp animation-delay-200">
          {/* Search Input Component - 항상 표시 */}
          <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h3 className="text-2xl font-semibold mb-6 text-slate-100 text-center">
              Search Input Component
            </h3>
            <SearchInput 
              onQueryChange={handleQueryChange}
              onSearchSubmit={handleSearchSubmit}
              isLoading={isLoading}
            />
          </section>

          {/* Quality Advisor Component - 검색어 입력 시 표시 */}
          {(query.trim() || qualityReport) && (
            <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
              <QualityAdvisor 
                qualityReport={isEvaluating ? null : qualityReport} 
              />
              {isEvaluating && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
                  <p className="text-slate-400">Evaluating search quality...</p>
                </div>
              )}
            </section>
          )}

          {/* Auction Status Component - 경매 시작 후 표시 */}
          {auction && (
            <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
              <AuctionStatus 
                auction={auction} 
                onBidSelect={handleBidSelect} 
              />
            </section>
          )}

          {/* Selected Bid Confirmation - 입찰 선택 후 표시 */}
          {selectedBid && auction && (
            <section className="bg-green-800/20 rounded-xl p-6 border border-green-600/30 animate-fadeInUp">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-green-400 mb-2">
                  🎉 Bid Selected Successfully!
                </h3>
                <p className="text-slate-300">
                  Your search data has been sold. Check your dashboard for earnings details.
                </p>
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-slate-400 animate-fadeIn animation-delay-400">
          <p className="text-sm">
            © 2024 Real-time Search Data Exchange. All rights reserved.
          </p>
        </footer>
      </main>
    </div>
  )
}
