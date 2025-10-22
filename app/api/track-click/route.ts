// Step 3: 광고 클릭 추적 및 보상 지급 API
// 사용자가 광고를 클릭했을 때만 호출되며, 일일 제출 한도 차감과 보상 지급을 담당

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    console.log(`--- ✅ /api/track-click API 시작 ---`);
    try {
        const body = await request.json();
        const { searchId, bidId, adType, query } = body; // adType: 'bidded' | 'fallback', query: 실제 검색어

        console.log(`[SERVER LOG] 요청 데이터:`, { searchId, bidId, adType, query });

        // 사용자 인증 확인
        const authHeader = request.headers.get('authorization');
        if (!authHeader) {
            console.error(`[SERVER LOG] 인증 헤더 없음`);
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '인증이 필요합니다.'
            }, { status: 401 });
        }

        console.log(`[SERVER LOG] 인증 헤더 확인됨: ${authHeader.substring(0, 20)}...`);

        // 입력값 유효성 검사
        if (!searchId || typeof searchId !== 'string') {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '유효하지 않은 검색 ID입니다.'
            }, { status: 400 });
        }

        if (!bidId || typeof bidId !== 'string') {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '유효하지 않은 입찰 ID입니다.'
            }, { status: 400 });
        }

        if (!adType || !['bidded', 'fallback'].includes(adType)) {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '유효하지 않은 광고 타입입니다.'
            }, { status: 400 });
        }

        console.log(`🔍 [TRACK-CLICK] Processing click: searchId=${searchId}, bidId=${bidId}, adType=${adType}`);

        // Step 3a: 일일 제출 한도 체크 (User Service 연결 실패 시 기본값 사용)
        let dailySubmission = { count: 0, limit: 5, remaining: 5, qualityScoreAvg: 0 };

        try {
            const dashboardResponse = await fetch(`${API_GATEWAY_URL}/api/user/dashboard`, {
                method: 'GET',
                headers: {
                    'Authorization': authHeader,
                },
            });

            if (dashboardResponse.ok) {
                const dashboardData = await dashboardResponse.json();
                // dailySubmission 안전 접근
                const safeDailySubmission = (resp: any) =>
                    resp?.dailySubmission ?? {
                        count: resp?.count ?? 0,
                        limit: resp?.limit ?? 5,
                        remaining: resp?.remaining ?? 5,
                        qualityScoreAvg: resp?.qualityScoreAvg ?? 0
                    };
                dailySubmission = safeDailySubmission(dashboardData.data);
                console.log(`✅ [TRACK-CLICK] Daily limit check passed: ${dailySubmission.remaining}/${dailySubmission.limit} remaining`);
            } else {
                console.warn('⚠️ User service unavailable, using default limits');
            }

            // Step 3a: 일일 제출 한도가 0이면 에러 반환
            if (dailySubmission.remaining <= 0) {
                return NextResponse.json<ApiResponse<null>>({
                    success: false,
                    error: `일일 제출 한도(${dailySubmission.limit}회)를 모두 사용했습니다. 내일 다시 시도해주세요.`
                }, { status: 429 });
            }

        } catch (error) {
            console.warn('⚠️ Failed to check daily submission limit, using default:', error);
            // User Service 연결 실패 시에도 계속 진행
        }

        // ❗️❗️❗️ REMOVED ❗️❗️❗️
        // Step 3b: 일일 제출 한도 차감 로직 제거
        // 이제 earnings API에서만 제출 횟수를 카운트합니다.
        // 중복 카운트 방지를 위해 update-daily-submission 호출을 제거했습니다.

        // Step 3c & 3d: 광고 타입에 따른 보상 지급
        let rewardAmount = 0;
        let finalUrl = '';
        let bidLandingUrl = ''; // 실제 광고주 landing URL 저장용

        if (adType === 'bidded') {
            // 입찰 광고: 실제 입찰가와 landing URL을 데이터베이스에서 조회
            try {
                console.log(`[SERVER LOG] Getting bid information for bidId: ${bidId}`);

                // Bid 정보를 직접 조회하는 API 호출 (auction service의 bid 정보 조회)
                const bidResponse = await fetch(`${API_GATEWAY_URL}/api/auction/bid/${bidId}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': authHeader,
                    },
                });

                if (bidResponse.ok) {
                    const bidData = await bidResponse.json();
                    rewardAmount = bidData.price || 200; // 실제 입찰가 사용
                    bidLandingUrl = bidData.landing_url || ''; // landing URL 저장
                    console.log(`✅ [TRACK-CLICK] Bidded ad reward from DB: ${rewardAmount}원 (bid: ${bidData.buyer_name})`);
                    console.log(`✅ [TRACK-CLICK] Bid landing URL: ${bidLandingUrl}`);
                } else {
                    console.warn(`⚠️ Failed to get bid info (status: ${bidResponse.status}), using fallback amount`);
                    rewardAmount = 200; // Fallback 보상
                }
            } catch (error) {
                console.warn('⚠️ Error getting bid information, using fallback amount:', error);
                rewardAmount = 200; // Fallback 보상
            }
        } else {
            // Fallback 광고: 고정 200원 보상
            rewardAmount = 200;
            console.log(`✅ [TRACK-CLICK] Fallback ad reward: ${rewardAmount}원`);
        }

        // Step 3e: 거래 로그 저장 (User Service에 보상 지급 알림) - 🔥 중요!
        console.log(`--- 🚨 CRITICAL: DB 저장 시작 ---`);
        console.log(`[SERVER LOG] /api/user/earnings 호출 시작: amount=${rewardAmount}`);

        try {
            const rewardResponse = await fetch(`${API_GATEWAY_URL}/api/user/earnings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': authHeader,
                },
                body: JSON.stringify({
                    amount: rewardAmount,
                    query: query || '',
                    adType: adType,
                    searchId: searchId,
                    bidId: bidId
                }),
            });

            console.log(`[SERVER LOG] /api/user/earnings 응답 상태: ${rewardResponse.status}`);
            console.log(`[SERVER LOG] /api/user/earnings 응답 헤더:`, Object.fromEntries(rewardResponse.headers.entries()));

            if (rewardResponse.ok) {
                const responseData = await rewardResponse.json();
                console.log(`[SERVER LOG] /api/user/earnings 성공 응답:`, responseData);
                console.log(`✅ [TRACK-CLICK] Reward granted: ${rewardAmount}원`);
            } else {
                const errorData = await rewardResponse.text();
                console.error(`--- 🚨 CRITICAL ERROR in /api/user/earnings ---`);
                console.error(`[SERVER LOG] /api/user/earnings 실패 응답:`, errorData);
                console.error(`[SERVER LOG] 응답 상태: ${rewardResponse.status}`);

                // 🔥 이제 실패 시 에러를 반환하도록 변경
                return NextResponse.json<ApiResponse<null>>({
                    success: false,
                    error: `수익 기록 저장에 실패했습니다. (상태: ${rewardResponse.status})`
                }, { status: 500 });
            }
        } catch (error) {
            console.error(`--- 🚨 CRITICAL ERROR in /api/user/earnings ---`);
            console.error(`[SERVER LOG] /api/user/earnings 네트워크 오류:`, error);
            console.error(`[SERVER LOG] 오류 타입:`, typeof error);
            console.error(`[SERVER LOG] 오류 메시지:`, error instanceof Error ? error.message : String(error));

            // 🔥 이제 실패 시 에러를 반환하도록 변경
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: `수익 기록 저장 중 네트워크 오류가 발생했습니다: ${error instanceof Error ? error.message : String(error)}`
            }, { status: 500 });
        }

        // Step 3f: 최종 광고 URL 반환
        // 전달받은 검색어를 우선 사용, 없으면 searchId로 조회
        let actualQuery = query || '';

        if (!actualQuery) {
            try {
                const searchResponse = await fetch(`${API_GATEWAY_URL}/api/auction/search/${searchId}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': authHeader,
                    },
                });

                if (searchResponse.ok) {
                    const searchData = await searchResponse.json();
                    actualQuery = searchData.query || searchId;
                    console.log(`✅ [TRACK-CLICK] Retrieved query from API: "${actualQuery}"`);
                } else {
                    console.warn('⚠️ Failed to retrieve search query, using searchId as fallback');
                    actualQuery = searchId;
                }
            } catch (error) {
                console.warn('⚠️ Error retrieving search query:', error);
                actualQuery = searchId;
            }
        } else {
            console.log(`✅ [TRACK-CLICK] Using provided query: "${actualQuery}"`);
        }

        if (adType === 'bidded') {
            // 입찰 광고의 경우 실제 광고 URL 생성
            if (bidId.includes('coupang')) {
                // 쿠팡: /np/search?q=검색어 형식
                finalUrl = `https://www.coupang.com/np/search?q=${encodeURIComponent(actualQuery)}`;
            } else if (bidId.includes('naver')) {
                // 네이버: /search.naver?where=web&query=검색어 형식
                finalUrl = `https://search.naver.com/search.naver?where=web&query=${encodeURIComponent(actualQuery)}`;
            } else if (bidId.includes('google')) {
                // 구글: /search?q=검색어 형식
                finalUrl = `https://www.google.com/search?q=${encodeURIComponent(actualQuery)}`;
            } else {
                // 실제 광고주의 경우: 위에서 이미 조회한 landing_url 사용
                if (bidLandingUrl) {
                    finalUrl = bidLandingUrl;
                    console.log(`✅ [TRACK-CLICK] Using real advertiser landing URL: ${finalUrl}`);
                } else {
                    console.warn(`⚠️ No landing URL found for bid ${bidId}, using fallback`);
                    finalUrl = `https://advertiser.example.com/click/${bidId}`;
                }
            }
        } else {
            // Fallback 광고의 경우 파트너 URL
            finalUrl = `https://partner.example.com/search?q=${encodeURIComponent(actualQuery)}`;
        }

        console.log(`🔗 [TRACK-CLICK] Generated final URL: ${finalUrl}`);

        // 성공 응답
        console.log(`[SERVER LOG] 프론트엔드에 성공 응답 전송 시작`);
        const successResponse = {
            success: true,
            data: {
                finalUrl,
                rewardAmount,
                adType,
                searchId,
                bidId,
                trade_id: bidId  // SLA 검증용 trade_id 추가
            },
            message: `거래가 등록되었으며, SLA 검증 대기 중입니다.`
        };
        console.log(`[SERVER LOG] 성공 응답 데이터:`, successResponse);
        console.log(`--- ✅ /api/track-click API 완료 (성공) ---`);

        return NextResponse.json<ApiResponse<{
            finalUrl: string;
            rewardAmount: number;
            adType: string;
            searchId: string;
            bidId: string;
            trade_id: string;
        }>>(successResponse, { status: 200 });

    } catch (error) {
        console.error(`--- 🚨 CRITICAL ERROR in /api/track-click ---`);
        console.error(`[SERVER LOG] 전체 API 처리 중 심각한 에러 발생:`, error);
        console.error(`[SERVER LOG] 오류 타입:`, typeof error);
        console.error(`[SERVER LOG] 오류 메시지:`, error instanceof Error ? error.message : String(error));
        console.error(`[SERVER LOG] 오류 스택:`, error instanceof Error ? error.stack : 'No stack trace');

        return NextResponse.json<ApiResponse<null>>({
            success: false,
            error: `서버 오류가 발생했습니다: ${error instanceof Error ? error.message : String(error)}`
        }, { status: 500 });
    }
}

// OPTIONS 요청 처리 (CORS)
export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
    });
}
