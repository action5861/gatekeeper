// 메인 페이지

'use client'

import Header from '@/components/Header'
import AuctionStatus from '@/components/main/AuctionStatus'
import HeroSection from '@/components/main/HeroSection'
import QualityAdvisor from '@/components/main/QualityAdvisor'
import SearchInput from '@/components/main/SearchInput'
import { authenticatedFetch, handleTokenExpiry } from '@/lib/auth'
import { useDebounce } from '@/lib/hooks/useDebounce'
import { useSlaTracker } from '@/lib/hooks/useSlaTracker'
import { Auction, QualityReport } from '@/lib/types'
import { useCallback, useEffect, useRef, useState } from 'react'

export default function Home() {
  // 상태 관리
  const [query, setQuery] = useState('')
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)

  // StrictMode 가드용 ref
  const didRunRef = useRef(false)
  const [auction, setAuction] = useState<Auction | null>(null)
  const [selectedBid, setSelectedBid] = useState<string | null>(null)
  const [tradeId, setTradeId] = useState<string | null>(null) // SLA 검증용 trade_id
  const [isLoading, setIsLoading] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // ⭐ 점진적 평가를 위한 새로운 상태
  const [evaluationStage, setEvaluationStage] = useState<'idle' | 'quick' | 'ai'>('idle')

  // SLA 추적용 ref (광고 영역을 참조)
  const auctionRef = useRef<HTMLDivElement>(null)

  // 디바운싱 적용: 1000ms 동안 타이핑이 없으면 최종 값을 반영
  const debouncedQuery = useDebounce(query, 1000)

  // 알림 표시 함수
  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 5000) // 5초 후 자동 제거
  }

  // Step 1: 디바운싱된 검색어가 바뀔 때만 품질 평가 API를 호출 (점진적 평가)
  useEffect(() => {
    if (!debouncedQuery.trim() || debouncedQuery.trim().length < 2) {
      setQualityReport(null)
      setIsEvaluating(false)
      setEvaluationStage('idle')
      return
    }

    // StrictMode 가드: 개발 모드에서 이중 마운트 방지
    if (didRunRef.current) return;
    didRunRef.current = true;

    console.log(`🔍 [STEP 1] 디바운싱된 검색어 '${debouncedQuery}'로 점진적 품질 평가를 시작합니다.`)
    setIsEvaluating(true)
    setEvaluationStage('quick')

    const evaluateQualityProgressive = async () => {
      const token = localStorage.getItem('token')
      const trimmedQuery = debouncedQuery.trim()

      // ⚡ 1단계: 빠른 평가 (Legacy만, ~0.1초)
      try {
        console.log(`⚡ [STEP 1-1] 빠른 평가 시작: "${trimmedQuery}"`)
        const quickResponse = await fetch('/api/evaluate-quality-quick', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: trimmedQuery }),
        })

        const quickData = await quickResponse.json()

        if (quickData.success) {
          // 빠른 결과 즉시 표시
          setQualityReport(quickData.data.qualityReport)
          setEvaluationStage('ai')
          console.log(`⚡ [STEP 1-1] 빠른 평가 완료: ${quickData.data.qualityReport.score}점`)
        }
      } catch (error) {
        console.error('Quick evaluation error:', error)
      }

      // 🤖 2단계: AI 정밀 분석 (~5초)
      try {
        console.log(`🤖 [STEP 1-2] AI 정밀 분석 시작: "${trimmedQuery}"`)
        const aiResponse = await fetch('/api/evaluate-quality', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({ query: trimmedQuery }),
        })

        const aiData = await aiResponse.json()

        if (aiData.success) {
          // AI 결과로 업데이트 (점수가 변경되면 애니메이션 효과)
          setQualityReport(aiData.data.qualityReport)
          console.log(`🤖 [STEP 1-2] AI 분석 완료: ${aiData.data.qualityReport.score}점`)
        } else {
          console.error('AI evaluation failed:', aiData.error)
        }
      } catch (error) {
        console.error('AI evaluation error:', error)
        // AI 실패 시 빠른 평가 결과 유지
      } finally {
        setIsEvaluating(false)
        setEvaluationStage('idle')
      }
    }

    evaluateQualityProgressive()

    // cleanup 함수에서 ref 리셋
    return () => {
      didRunRef.current = false
    }
  }, [debouncedQuery])

  // 검색어 변경 처리
  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery)
  }, [])

  // ⭐ AI 제안 검색어로 교체
  const handleQueryReplace = useCallback((newQuery: string) => {
    setQuery(newQuery)
    // 교체 후 즉시 재평가 (디바운싱 우회)
    setQualityReport(null)
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
        const receivedTradeId = trackData.data.trade_id || bidId

        console.log(`✅ [STEP 3] Click tracked successfully: ${rewardAmount}원 reward, trade_id: ${receivedTradeId}`)
        console.log(`📝 [STEP 3] Setting tradeId state to: ${receivedTradeId}`)

        // SLA 검증을 위한 trade_id 저장
        setTradeId(receivedTradeId)

        console.log(`🎯 [STEP 3] TradeId set! SLA Tracker should start now...`)

        // 🆕 광고 클릭을 SLA Tracker에 알림
        if (notifyAdClick) {
          notifyAdClick();
          console.log(`🖱️ [STEP 3] Notified SLA Tracker about ad click`);
        }

        // 📦 localStorage에 복귀 추적 데이터 저장 (2단계 평가용)
        const returnTrackerData = {
          trade_id: receivedTradeId,
          click_time: Date.now()
        };
        localStorage.setItem('ad_return_tracker', JSON.stringify(returnTrackerData));
        console.log(`💾 [STEP 3] Saved return tracker data:`, returnTrackerData);

        // 보상 등록 알림
        showNotification('success', `광고주 사이트 탐색 후 돌아와서 전액 정산을 받으세요!`)

        // 대시보드 데이터 갱신 이벤트 발생 (일일 제출 한도 차감됨)
        window.dispatchEvent(new CustomEvent('stats-updated'))
        window.dispatchEvent(new CustomEvent('submission-updated'))

        // 🆕 즉시 광고주 사이트로 리다이렉트 (2단계 평가 모델)
        setTimeout(() => {
          const redirectUrl = `/api/track-redirect?trade_id=${encodeURIComponent(receivedTradeId)}&dest=${encodeURIComponent(finalUrl)}`;
          window.open(redirectUrl, '_blank');
          console.log(`🔗 [STEP 3] Opening advertiser site: ${redirectUrl}`);
        }, 500)

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
  }, [auction, query])

  // SLA 검증 완료 콜백 (useCallback으로 메모이제이션)
  const handleSlaComplete = useCallback(async (metrics: any) => {
    if (!tradeId) return;

    try {
      console.log(`📤 Sending SLA verification for trade_id: ${tradeId}`, metrics);

      const response = await authenticatedFetch('/api/verify-delivery', {
        method: 'POST',
        body: JSON.stringify({
          trade_id: tradeId,
          ...metrics
        }),
      });

      const result = await response.json();
      console.log(`✅ SLA verification response:`, result);

      if (result.decision) {
        const messages = {
          'PASSED': '✅ SLA 검증 통과! 전액 정산됩니다.',
          'PARTIAL': '⚠️ SLA 부분 충족. 부분 정산됩니다.',
          'FAILED': '❌ SLA 미충족. 정산되지 않습니다.'
        };
        showNotification(
          result.decision === 'PASSED' ? 'success' : 'error',
          messages[result.decision as keyof typeof messages] || '검증 완료'
        );
      }

      // 대시보드 갱신
      window.dispatchEvent(new CustomEvent('stats-updated'));

    } catch (error) {
      console.error('SLA verification error:', error);
    }
  }, [tradeId]);

  // SLA 추적 및 검증 요청
  const { isTracking, notifyAdClick } = useSlaTracker<HTMLDivElement>({
    tradeId,
    elementRef: auctionRef,
    onComplete: handleSlaComplete,
  });

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

      {/* Hero Section - Full Width */}
      <HeroSection />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Main Components Area */}
        <div className="space-y-6 animate-fadeInUp animation-delay-200">
          {/* Search Input Component - Premium Glassmorphism */}
          <section className="mt-4 sm:mt-6">
            <SearchInput
              onQueryChange={handleQueryChange}
              onSearchSubmit={handleSearchSubmit}
              isLoading={isLoading}
            />
          </section>

          {/* Quality Advisor Component - 검색어 입력 시 표시 (점진적 평가) */}
          {(query.trim() || qualityReport) && (
            <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
              {/* 빠른 평가 결과가 있으면 즉시 표시 */}
              {qualityReport && (
                <QualityAdvisor
                  qualityReport={qualityReport}
                  onQueryReplace={handleQueryReplace}
                />
              )}

              {/* 평가 단계별 상태 표시 */}
              {evaluationStage === 'quick' && !qualityReport && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-t-2 border-yellow-500 mx-auto mb-3"></div>
                  <p className="text-lg font-semibold text-yellow-400 mb-1">⚡ 빠른 분석 중...</p>
                  <p className="text-sm text-slate-400">잠시만 기다려주세요</p>
                </div>
              )}

              {evaluationStage === 'ai' && (
                <div className="mt-4 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-t-2 border-blue-500"></div>
                    <div>
                      <p className="text-sm font-medium text-blue-400">🤖 AI 정밀 분석 진행 중...</p>
                      <p className="text-xs text-slate-400">상업적 의도, 구체성, 구매 단계를 평가합니다</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse animation-delay-200"></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse animation-delay-400"></div>
                    <span className="text-xs text-slate-500 ml-2">점수가 변경될 수 있습니다</span>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Auction Status Component - 경매 시작 후 표시 (SLA 추적용 ref 연결) */}
          <div ref={auctionRef}>
            {auction && (
              <section className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
                <AuctionStatus
                  auction={auction}
                  onBidSelect={handleBidSelect}
                />
              </section>
            )}
          </div>

          {/* Selected Bid Confirmation - 입찰 선택 후 표시 */}
          {selectedBid && auction && (
            <section className="bg-green-800/20 rounded-xl p-6 border border-green-600/30 animate-fadeInUp">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-green-400 mb-2">
                  🎉 입찰이 성공적으로 선택되었습니다!
                </h3>
                <p className="text-slate-300">
                  검색 데이터가 판매되었습니다. 대시보드에서 수익 내역을 확인하세요.
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
            의도가 곧 접근권. 증명으로 정산.
          </p>
        </footer>
      </main>
    </div>
  )
}
