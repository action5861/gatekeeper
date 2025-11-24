// 광고주 사이트로의 즉시 리다이렉트 (2단계 평가 모델 - 1차 평가)

import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

// 리다이렉트 시작 (광고주 사이트로 즉시 이동)
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const tradeId = searchParams.get('trade_id');
        const dest = searchParams.get('dest');

        if (!tradeId || !dest) {
            return NextResponse.json({
                success: false,
                error: 'trade_id와 dest 파라미터가 필요합니다.'
            }, { status: 400 });
        }

        console.log(`🔗 [Redirect] Immediate redirect for trade_id: ${tradeId} to ${dest}`);

        // 1차 평가 요청: PENDING_RETURN 상태로 업데이트
        const authHeader = request.headers.get('authorization');

        try {
            const response = await fetch(`${API_GATEWAY_URL}/api/verification/update-pending-return`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(authHeader && { 'Authorization': authHeader }),
                },
                body: JSON.stringify({ trade_id: tradeId }),
            });

            if (response.ok) {
                console.log(`✅ [Redirect] Status updated to PENDING_RETURN for trade_id: ${tradeId}`);
            }
        } catch (err) {
            console.error('Failed to update pending return status:', err);
            // 에러가 나도 리다이렉트는 계속 진행
        }

        // 즉시 광고주 사이트로 리다이렉트 (307 Temporary Redirect)
        return NextResponse.redirect(dest, 307);

    } catch (error) {
        console.error('[track-redirect] Error:', error);
        return NextResponse.json({
            success: false,
            error: '서버 오류가 발생했습니다.'
        }, { status: 500 });
    }
}

