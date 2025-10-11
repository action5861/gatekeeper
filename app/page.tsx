// 메인 페이지

'use client'

import Header from '@/components/Header'
import AuctionStatus from '@/components/main/AuctionStatus'
import QualityAdvisor from '@/components/main/QualityAdvisor'
import SearchInput from '@/components/main/SearchInput'
import { authenticatedFetch, handleTokenExpiry } from '@/lib/auth'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { Auction, QualityReport } from '@/lib/types'
import { Eye, FileText, Lock, Shield } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

export default function Home() {
  // 상태 관리
  const [query, setQuery] = useState('')
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)

  // StrictMode 가드용 ref
  const didRunRef = useRef(false)
  const [auction, setAuction] = useState<Auction | null>(null)
  const [selectedBid, setSelectedBid] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // 디바운싱 적용: 1000ms 동안 타이핑이 없으면 최종 값을 반영
  const debouncedQuery = useDebounce(query, 1000)

  // 알림 표시 함수
  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 5000) // 5초 후 자동 제거
  }

  // Step 1: 디바운싱된 검색어가 바뀔 때만 품질 평가 API를 호출 (일일 제출 한도 적용 없음)
  useEffect(() => {
    if (!debouncedQuery.trim() || debouncedQuery.trim().length < 2) {
      setQualityReport(null)
      setIsEvaluating(false)
      return
    }

    // StrictMode 가드: 개발 모드에서 이중 마운트 방지
    if (didRunRef.current) return;
    didRunRef.current = true;

    console.log(`🔍 [STEP 1] 디바운싱된 검색어 '${debouncedQuery}'로 품질 평가 API를 호출합니다.`)
    setIsEvaluating(true)

    const evaluateQuality = async () => {
      try {
        const token = localStorage.getItem('token')
        console.log(`🔍 [STEP 1] Calling /api/evaluate-quality for query: "${debouncedQuery.trim()}"`)
        const response = await fetch('/api/evaluate-quality', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({
            query: debouncedQuery.trim()
          }),
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
    }

    evaluateQuality()

    // cleanup 함수에서 ref 리셋
    return () => {
      didRunRef.current = false
    }
  }, [debouncedQuery])

  // 검색어 변경 처리
  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery)
  }, [])

  // Step 2: 폼 제출 처리 (광고 검색 - 일일 제출 한도 차감 없음)
  const handleSearchSubmit = useCallback(async (searchQuery: string) => {
    // 품질 평가가 완료되지 않은 경우 제출 불가
    if (!qualityReport) {
      showNotification('error', '검색어 품질 평가를 완료한 후 제출해주세요.')
      return
    }

    setIsLoading(true)
    setAuction(null) // 이전 경매 초기화
    setSelectedBid(null) // 선택된 입찰 초기화

    try {
      console.log(`🚀 [STEP 2] Calling /api/search for ad search: "${searchQuery}" with quality score: ${qualityReport.score}`)
      const response = await authenticatedFetch('/api/search', {
        method: 'POST',
        body: JSON.stringify({
          query: searchQuery,
          qualityScore: qualityReport.score // 품질 점수를 함께 전달
        }),
      })

      const data = await response.json()

      if (data.success) {
        setAuction(data.data.auction)
        showNotification('success', '광고 검색이 완료되었습니다!')

        // 대시보드 데이터 갱신 이벤트 발생 (일일 제출 한도는 차감되지 않음)
        window.dispatchEvent(new CustomEvent('stats-updated'))
      } else {
        console.error('Ad search failed:', data.error)
        showNotification('error', data.error || '광고 검색에 실패했습니다.')
      }
    } catch (error) {
      console.error('Ad search error:', error)
      if (error instanceof Error && error.message.includes('로그인이 만료')) {
        showNotification('error', '로그인이 만료되었습니다. 다시 로그인해주세요.')
        handleTokenExpiry()
      } else {
        showNotification('error', '네트워크 오류가 발생했습니다.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [qualityReport])

  // Step 3: 광고 클릭 처리 (일일 제출 한도 차감 및 보상 지급)
  const handleBidSelect = useCallback(async (bidId: string) => {
    if (!auction) return

    console.log('🔍 [STEP 3] Ad click started:', { bidId, auction });

    setIsLoading(true)
    try {
      const selectedBid = auction.bids.find(bid => bid.id === bidId)

      // 광고 타입 결정 (입찰 광고 vs fallback 광고)
      const adType = selectedBid ? 'bidded' : 'fallback'

      console.log(`🔍 [STEP 3] Calling /api/track-click: searchId=${auction.searchId}, bidId=${bidId}, adType=${adType}`)

      // Step 3: 클릭 추적 및 보상 지급
      const trackResponse = await authenticatedFetch('/api/track-click', {
        method: 'POST',
        body: JSON.stringify({
          searchId: auction.searchId,
          bidId: bidId,
          adType: adType,
          query: query // 실제 검색어도 함께 전달
        }),
      })

      const trackData = await trackResponse.json()

      if (trackData.success) {
        setSelectedBid(bidId)
        const rewardAmount = trackData.data.rewardAmount
        const finalUrl = trackData.data.finalUrl

        console.log(`✅ [STEP 3] Click tracked successfully: ${rewardAmount}원 reward, redirecting to: ${finalUrl}`)

        // 보상 지급 알림
        showNotification('success', `보상 ${rewardAmount}원이 지급되었습니다!`)

        // 대시보드 데이터 갱신 이벤트 발생 (일일 제출 한도 차감됨)
        window.dispatchEvent(new CustomEvent('stats-updated'))
        window.dispatchEvent(new CustomEvent('submission-updated'))

        // 최종 광고 URL로 리디렉션
        setTimeout(() => {
          window.open(finalUrl, '_blank')
        }, 1000)

      } else {
        console.error('Track click failed:', trackData.error)
        showNotification('error', trackData.error || '광고 클릭 처리에 실패했습니다.')
      }
    } catch (error) {
      console.error('Ad click error:', error)
      if (error instanceof Error && error.message.includes('로그인이 만료')) {
        showNotification('error', '로그인이 만료되었습니다. 다시 로그인해주세요.')
        handleTokenExpiry()
      } else {
        showNotification('error', '광고 클릭 처리 중 오류가 발생했습니다.')
      }
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
        <div className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 ${notification.type === 'success'
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
            The World&apos;s First Intent Exchange
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            List what you&apos;re searching for. Advertisers bid in real-time. Get settled when SLA is verified—or they get refunded.
          </p>
        </section>

        {/* Main Components Area */}
        <div className="space-y-8 animate-fadeInUp animation-delay-200">
          {/* Search Input Component - 항상 표시 */}
          <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h3 className="text-2xl font-semibold mb-6 text-slate-100 text-center">
              List Your Intent
            </h3>
            <SearchInput
              onQueryChange={handleQueryChange}
              onSearchSubmit={handleSearchSubmit}
              isLoading={isLoading}
            />
          </section>

          {/* Feature Cards Section */}
          <section className="animate-fadeInUp">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Card 1: Transparent Pricing */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-blue-500/50 transition-all duration-300 hover:transform hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center mb-4">
                  <Eye className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">
                  Transparent Pricing
                </h3>
                <p className="text-sm font-semibold text-blue-400 mb-3">
                  See What Your Intent Is Worth
                </p>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Real-time orderbook shows actual bids from advertisers competing for your attention.
                </p>
              </div>

              {/* Card 2: Quality Verified */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-green-500/50 transition-all duration-300 hover:transform hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">
                  Quality Verified
                </h3>
                <p className="text-sm font-semibold text-green-400 mb-3">
                  Get Paid Only When You Actually Engage
                </p>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Our SDK measures visibility, focus, and dwell time—failed quality means auto-refund to advertisers, zero for you.
                </p>
              </div>

              {/* Card 3: Privacy First */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-purple-500/50 transition-all duration-300 hover:transform hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mb-4">
                  <Lock className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">
                  Privacy First
                </h3>
                <p className="text-sm font-semibold text-purple-400 mb-3">
                  Access Rights, Not Data Ownership
                </p>
                <p className="text-sm text-slate-400 leading-relaxed">
                  We never capture screens or content—only session-based exposure metrics with HMAC verification.
                </p>
              </div>

              {/* Card 4: Settlement by Proof */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-yellow-500/50 transition-all duration-300 hover:transform hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-green-500 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">
                  Settlement by Proof
                </h3>
                <p className="text-sm font-semibold text-yellow-400 mb-3">
                  This Isn&apos;t a Reward. It&apos;s a Transaction.
                </p>
                <p className="text-sm text-slate-400 leading-relaxed">
                  SLA verification determines PASSED (full payment), PARTIAL (prorated), or FAILED (refund). All logged for audit.
                </p>
              </div>
            </div>
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
          <p className="text-sm mb-2">
            © 2025 Intendex. All rights reserved.
          </p>
          <p className="text-xs text-slate-500 font-semibold">
            Intent as Access. Settlement by Proof.
          </p>
        </footer>
      </main>
    </div>
  )
}
