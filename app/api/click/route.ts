// 클릭 처리 API - API Gateway를 통한 프록시

import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

console.log('API_GATEWAY_URL:', API_GATEWAY_URL);

export async function GET(request: NextRequest) {
    try {
        // URL에서 searchId와 bidId 추출
        const url = new URL(request.url);
        const pathParts = url.pathname.split('/');

        // /api/click/searchId/bidId 형태에서 searchId와 bidId 추출
        const searchIdIndex = pathParts.indexOf('click') + 1;
        const searchId = pathParts[searchIdIndex];
        const bidId = pathParts[searchIdIndex + 1];

        console.log(`[NEXT.JS] Extracted searchId: ${searchId}, bidId: ${bidId}`);

        if (!searchId || !bidId) {
            return NextResponse.json({
                success: false,
                error: 'searchId와 bidId가 필요합니다.'
            }, { status: 400 });
        }

        // 사용자 인증 확인
        const authHeader = request.headers.get('authorization');
        if (!authHeader) {
            return NextResponse.json({
                success: false,
                error: '인증이 필요합니다.'
            }, { status: 401 });
        }

        console.log(`[NEXT.JS] Proxying click request: /api/click/${searchId}/${bidId}`);

        // API Gateway를 통해 클릭 처리
        const gatewayResponse = await fetch(`${API_GATEWAY_URL}/api/click/${searchId}/${bidId}`, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
            },
            redirect: 'manual', // 리디렉션을 수동으로 처리
        });

        console.log(`[NEXT.JS] Gateway response status: ${gatewayResponse.status}`);

        // 302 리디렉션 응답을 그대로 전달
        if (gatewayResponse.status === 302) {
            const location = gatewayResponse.headers.get('location');
            console.log(`[NEXT.JS] Redirecting to: ${location}`);
            if (location) {
                return NextResponse.redirect(location, 302);
            }
        }

        // 다른 응답은 그대로 전달
        const responseData = await gatewayResponse.text();
        return new NextResponse(responseData, {
            status: gatewayResponse.status,
            headers: {
                'Content-Type': gatewayResponse.headers.get('content-type') || 'application/json',
            },
        });

    } catch (error) {
        console.error('Click API Error:', error);
        return NextResponse.json({
            success: false,
            error: '클릭 처리 중 오류가 발생했습니다.'
        }, { status: 500 });
    }
}

// OPTIONS 요청 처리 (CORS)
export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
    });
}



