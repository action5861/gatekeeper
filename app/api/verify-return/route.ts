// 2단계 평가 API - 사용자 복귀 시 체류 시간 기반 최종 평가

import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { trade_id, dwell_time } = body;

        if (!trade_id || dwell_time === undefined) {
            return NextResponse.json({
                success: false,
                error: 'trade_id와 dwell_time이 필요합니다.'
            }, { status: 400 });
        }

        console.log(`🔙 [Verify Return] User returned for trade_id: ${trade_id}, dwell_time: ${dwell_time}s`);

        // 사용자 인증 확인
        const authHeader = request.headers.get('authorization');
        if (!authHeader) {
            return NextResponse.json({
                success: false,
                error: '인증이 필요합니다.'
            }, { status: 401 });
        }

        // Verification Service로 2차 평가 요청
        const verificationResponse = await fetch(`${API_GATEWAY_URL}/api/verification/verify-return`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': authHeader,
            },
            body: JSON.stringify({
                trade_id,
                dwell_time
            }),
        });

        if (!verificationResponse.ok) {
            const errorText = await verificationResponse.text();
            console.error(`[Verify Return] Verification service error:`, errorText);
            throw new Error('Verification service error');
        }

        const verificationData = await verificationResponse.json();
        console.log(`✅ [Verify Return] Verification complete:`, verificationData);

        return NextResponse.json(verificationData, { status: 200 });

    } catch (error) {
        console.error('[verify-return] API Error:', error);
        return NextResponse.json({
            success: false,
            error: '서버 오류가 발생했습니다.'
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








