// frontend/src/app/api/track-click/route.ts

import { NextRequest, NextResponse } from 'next/server'
const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://api-gateway:8000'

export async function POST(request: NextRequest) {
    console.log('--- ✅ /api/track-click API 시작 ---')
    try {
        const body = await request.json()
        const { searchId, bidId, adType, query } = body
        console.log('[SERVER LOG] 요청 데이터:', { searchId, bidId, adType, query })

        const authHeader = request.headers.get('authorization')
        if (!authHeader) {
            return NextResponse.json({ success: false, error: '인증이 필요합니다.' }, { status: 401 })
        }
        console.log(`[SERVER LOG] 인증 헤더 확인됨: ${authHeader.substring(0, 20)}...`)

        if (!searchId || typeof searchId !== 'string') {
            return NextResponse.json({ success: false, error: '유효하지 않은 검색 ID입니다.' }, { status: 400 })
        }
        if (!bidId || typeof bidId !== 'string') {
            return NextResponse.json({ success: false, error: '유효하지 않은 입찰 ID입니다.' }, { status: 400 })
        }
        if (!adType || !['bidded', 'fallback'].includes(adType)) {
            return NextResponse.json({ success: false, error: '유효하지 않은 광고 타입입니다.' }, { status: 400 })
        }

        console.log(`🔍 [TRACK-CLICK] Processing click: searchId=${searchId}, bidId=${bidId}, adType=${adType}`)

        // --- 일일 제출 한도 조회 (생략 가능) ---
        let dailySubmission = { count: 0, limit: 5, remaining: 5, qualityScoreAvg: 0 }
        try {
            const dashboardRes = await fetch(`${API_GATEWAY_URL}/api/user/dashboard`, {
                method: 'GET',
                headers: { Authorization: authHeader },
            })
            if (dashboardRes.ok) {
                const dashboardData = await dashboardRes.json()
                const ds = dashboardData?.data?.dailySubmission ?? {}
                dailySubmission = {
                    count: ds.count ?? 0,
                    limit: ds.limit ?? 5,
                    remaining: ds.remaining ?? 5,
                    qualityScoreAvg: ds.qualityScoreAvg ?? 0,
                }
                console.log(`✅ [TRACK-CLICK] Daily limit check passed: ${dailySubmission.remaining}/${dailySubmission.limit} remaining`)
            } else {
                console.warn('⚠️ User service unavailable, using default limits')
            }
            if (dailySubmission.remaining <= 0) {
                return NextResponse.json({ success: false, error: `일일 제출 한도(${dailySubmission.limit}회) 소진` }, { status: 429 })
            }
        } catch (e) {
            console.warn('⚠️ Failed to check daily submission limit:', e)
        }

        // --- 입찰 정보 조회/보상금 결정 ---
        let rewardAmount = 0
        let finalUrl = ''
        let bidLandingUrl = ''
        // ✅ 함수 상단에서 선언해 스코프 문제 제거
        let bidInfo: {
            id?: string
            auction_id?: number | null
            buyer_name?: string | null
            price?: number
            landing_url?: string
            advertiser_id?: number | null
            type?: 'PLATFORM' | 'ADVERTISER'
        } | null = null

        if (adType === 'bidded') {
            try {
                console.log(`[SERVER LOG] Getting bid information for bidId: ${bidId}`)
                const bidRes = await fetch(`${API_GATEWAY_URL}/api/auction/bid/${encodeURIComponent(bidId)}`, {
                    method: 'GET',
                    headers: { Authorization: authHeader },
                    cache: 'no-store',
                })
                if (!bidRes.ok) {
                    const text = await bidRes.text().catch(() => '')
                    console.warn(`⚠️ Error getting bid info: ${bidRes.status} ${text}`)
                } else {
                    bidInfo = await bidRes.json()
                }

                // ✅ 항상 bidInfo로 참조
                rewardAmount = Number(bidInfo?.price ?? 200)
                bidLandingUrl = String(bidInfo?.landing_url ?? '')
                console.log(`✅ [TRACK-CLICK] Bidded ad reward from DB: ${rewardAmount}원 (bid: ${bidInfo?.buyer_name ?? '시스템'})`)
                console.log(`✅ [TRACK-CLICK] Bid landing URL: ${bidLandingUrl}`)
            } catch (e) {
                console.warn('⚠️ Error getting bid information, using fallback amount:', e)
                rewardAmount = 200
            }
        } else {
            rewardAmount = 200
            console.log(`✅ [TRACK-CLICK] Fallback ad reward: ${rewardAmount}원`)
        }

        // --- 거래 등록 (PENDING) ---
        console.log('--- 📝 거래 등록 시작 (PENDING) ---')
        console.log(`[SERVER LOG] 거래 등록: amount=${rewardAmount}, bidId=${bidId}`)

        try {
            const payload = {
                trade_id: bidId,
                bidId, // settlement/user-service가 bid_id로 매핑할 수 있도록 유지
                search_id: searchId,
                ad_type: adType,
                query_text: query,
                // 호환성 유지를 위해 camelCase도 함께 전송
                searchId,
                adType,
                query,
                amount: rewardAmount,
                source: bidInfo?.type ?? (bidId.startsWith('platform_bid_') ? 'PLATFORM' : 'ADVERTISER'),
                buyer_name: bidInfo?.buyer_name ?? '시스템',
                auction_id: bidInfo?.auction_id ?? null,
                advertiser_id: bidInfo?.advertiser_id ?? null,
            }

            const txRes = await fetch(`${API_GATEWAY_URL}/api/user/earnings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: authHeader },
                body: JSON.stringify(payload),
            })
            console.log(`[SERVER LOG] /api/user/earnings 응답 상태: ${txRes.status}`)

            if (!txRes.ok && txRes.status !== 202) {
                const text = await txRes.text().catch(() => '')
                console.error('--- 🚨 거래 등록 실패 ---', text)
                return NextResponse.json({ success: false, error: `거래 등록 실패 (상태: ${txRes.status})` }, { status: 500 })
            }
            const resp = await txRes.json().catch(() => ({}))
            console.log('[SERVER LOG] 거래 등록 성공:', resp)
            console.log(`✅ [TRACK-CLICK] Transaction registered (PENDING): ${rewardAmount}원`)
        } catch (e) {
            console.error('--- 🚨 거래 등록 오류 ---', e)
            return NextResponse.json({ success: false, error: '거래 등록 중 오류가 발생했습니다.' }, { status: 500 })
        }

        // --- 최종 이동 URL ---
        let actualQuery = query ?? ''
        if (!actualQuery) {
            try {
                const qRes = await fetch(`${API_GATEWAY_URL}/api/auction/search/${encodeURIComponent(searchId)}`, {
                    method: 'GET',
                    headers: { Authorization: authHeader },
                })
                if (qRes.ok) {
                    const qData = await qRes.json()
                    actualQuery = qData?.query ?? searchId
                    console.log(`✅ [TRACK-CLICK] Retrieved query from API: "${actualQuery}"`)
                } else {
                    actualQuery = searchId
                }
            } catch {
                actualQuery = searchId
            }
        } else {
            console.log(`✅ [TRACK-CLICK] Using provided query: "${actualQuery}"`)
        }

        if (adType === 'bidded') {
            if (bidId.includes('coupang')) {
                finalUrl = `https://www.coupang.com/np/search?q=${encodeURIComponent(actualQuery)}`
            } else if (bidId.includes('naver')) {
                finalUrl = `https://search.naver.com/search.naver?where=web&query=${encodeURIComponent(actualQuery)}`
            } else if (bidId.includes('google')) {
                finalUrl = `https://www.google.com/search?q=${encodeURIComponent(actualQuery)}`
            } else if (bidLandingUrl) {
                finalUrl = bidLandingUrl
            } else {
                finalUrl = `https://advertiser.example.com/click/${encodeURIComponent(bidId)}`
            }
        } else {
            finalUrl = `https://partner.example.com/search?q=${encodeURIComponent(actualQuery)}`
        }

        console.log(`🔗 [TRACK-CLICK] Generated final URL: ${finalUrl}`)

        const successResponse = {
            success: true,
            data: { finalUrl, rewardAmount, adType, searchId, bidId, trade_id: bidId },
            message: '거래가 등록되었으며, SLA 검증 대기 중입니다.',
        }
        console.log('[SERVER LOG] 성공 응답 데이터:', successResponse)
        console.log('--- ✅ /api/track-click API 완료 (성공) ---')
        return NextResponse.json(successResponse, { status: 200 })
    } catch (err: any) {
        console.error('--- 🚨 CRITICAL ERROR in /api/track-click ---', err)
        return NextResponse.json({ success: false, error: '서버 오류가 발생했습니다.' }, { status: 500 })
    }
}
