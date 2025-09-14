// 실시간 역경매 입찰 현황판

'use client'

import { authenticatedFetch } from '@/lib/auth'
import { Auction } from '@/lib/types'
import { Award, Clock, DollarSign, TrendingUp, Users } from 'lucide-react'
import { useEffect, useState } from 'react'

interface AuctionStatusProps {
  auction: Auction | null
  onBidSelect?: (bidId: string) => void
}

export default function AuctionStatus({ auction, onBidSelect }: AuctionStatusProps) {
  const [timeLeft, setTimeLeft] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  // 남은 시간 계산
  useEffect(() => {
    if (!auction) return

    const timer = setInterval(() => {
      const now = new Date().getTime()
      const expiresAt = new Date(auction.expiresAt).getTime()
      const distance = expiresAt - now

      if (distance < 0) {
        setTimeLeft('EXPIRED')
        clearInterval(timer)
        return
      }

      const hours = Math.floor(distance / (1000 * 60 * 60))
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((distance % (1000 * 60)) / 1000)

      setTimeLeft(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`)
    }, 1000)

    return () => clearInterval(timer)
  }, [auction])

  const handleBidSelect = async (bidId: string) => {
    if (!auction || !onBidSelect) return

    setIsLoading(true)
    try {
      const response = await authenticatedFetch('/api/auction/select', {
        method: 'POST',
        body: JSON.stringify({
          searchId: auction.searchId,
          selectedBidId: bidId,
        }),
      })

      const data = await response.json()

      if (data.success) {
        onBidSelect(bidId)
        alert(`1차 보상이 지급되었습니다! (${data.data.rewardAmount.toLocaleString()}원)`)
      } else {
        alert('입찰 선택에 실패했습니다.')
      }
    } catch (error) {
      console.error('Bid selection error:', error)
      alert('입찰 선택 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBidClick = (bid: any) => {
    console.log(`[FRONTEND] handleBidClick called with bid:`, bid);

    // Step 3: 새로운 track-click API를 사용하여 클릭 처리
    if (onBidSelect) {
      console.log(`[FRONTEND] Calling onBidSelect with bidId: ${bid.id}`);
      onBidSelect(bid.id);
    } else {
      console.warn(`[FRONTEND] No onBidSelect handler, falling back to direct URL`);
      // Fallback: 직접 URL 열기
      try {
        if (bid.clickUrl) {
          console.log(`[FRONTEND] Using clickUrl: ${bid.clickUrl}`);
          window.open(bid.clickUrl, '_blank');
        } else {
          console.warn(`[FRONTEND] No clickUrl found for bid ${bid.id}, falling back to landingUrl`);
          window.open(bid.landingUrl, '_blank');
        }
      } catch (error) {
        console.error("클릭 처리 중 오류 발생:", error);
        alert("링크를 여는 데 실패했습니다. 다시 시도해주세요.");
      }
    }
  }

  if (!auction) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeIn">
        <h3 className="text-2xl font-semibold mb-4 text-slate-100 flex items-center space-x-2">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <span>Live Auction Status</span>
        </h3>
        <div className="text-center py-8">
          <Clock className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-400">Start a search to see live auction bids</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Live Auction Status</span>
      </h3>

      {/* Auction Info */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <span className="text-slate-300 font-medium">Time Left</span>
          </div>
          <div className="text-2xl font-bold text-red-400">{timeLeft}</div>
        </div>

        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Users className="w-5 h-5 text-green-400" />
            <span className="text-slate-300 font-medium">Bidders</span>
          </div>
          <div className="text-2xl font-bold text-green-400">{auction.bids.length}</div>
        </div>

        <div className="bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-5 h-5 text-yellow-400" />
            <span className="text-slate-300 font-medium">Top Bid</span>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {auction.bids.length > 0 ? auction.bids[0].price.toLocaleString() : 0}원
          </div>
        </div>
      </div>

      {/* Bids List */}
      <div className="space-y-3">
        <h4 className="text-lg font-semibold text-slate-100 mb-4">Current Bids</h4>

        {auction.bids.length === 0 ? (
          <div className="text-center py-8">
            <Award className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-400">No bids yet</p>
          </div>
        ) : (
          auction.bids.map((bid, index) => (
            <div
              key={bid.id}
              className={`bg-slate-700/30 rounded-lg p-4 border transition-all duration-200 ${index === 0
                ? 'border-yellow-500/50 bg-yellow-500/10'
                : 'border-slate-600 hover:border-slate-500'
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${index === 0
                      ? 'bg-yellow-500 text-yellow-900'
                      : 'bg-slate-600 text-slate-300'
                      }`}>
                      #{index + 1}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-100">{bid.buyerName}</div>
                      <div className="text-sm text-slate-400">{bid.bonus}</div>
                    </div>
                  </div>
                </div>

                <div className="text-right mr-6">
                  <div className="text-2xl font-bold text-slate-100">
                    {bid.price.toLocaleString()}원
                  </div>
                  <div className="text-sm text-slate-400">
                    {new Date(bid.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                <button
                  onClick={() => handleBidClick(bid)}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 flex items-center space-x-2 whitespace-nowrap"
                >
                  <span>Visit & Get {bid.price}원</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
} 