// SLA 검증 요청 API (Verification Service로 프록시)

import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        console.log(`[verify-delivery] Proxying SLA verification request:`, body);

        // 사용자 인증 확인
        const authHeader = request.headers.get('authorization');
        if (!authHeader) {
            return NextResponse.json({
                success: false,
                error: '인증이 필요합니다.'
            }, { status: 401 });
        }

        // Verification Service로 요청 전달
        const verificationResponse = await fetch(`${API_GATEWAY_URL}/api/verification/verify-delivery`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': authHeader,
            },
            body: JSON.stringify(body),
        });

        if (!verificationResponse.ok) {
            const errorText = await verificationResponse.text();
            console.error(`[verify-delivery] Verification service error:`, errorText);
            throw new Error('Verification service error');
        }

        const verificationData = await verificationResponse.json();
        console.log(`[verify-delivery] Verification response:`, verificationData);

        return NextResponse.json(verificationData, { status: 200 });

    } catch (error) {
        console.error('[verify-delivery] API Error:', error);
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

