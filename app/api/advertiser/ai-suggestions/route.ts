import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    try {
        // 클라이언트의 Authorization 헤더 가져오기
        const authHeader = request.headers.get('authorization');

        if (!authHeader) {
            return NextResponse.json(
                { detail: '인증이 필요합니다.' },
                { status: 401 }
            );
        }

        // API Gateway를 통해 advertiser-service로 요청 전달
        const response = await fetch(
            `${process.env.API_GATEWAY_URL}/api/advertiser/ai-suggestions`,
            {
                method: 'GET',
                headers: {
                    'Authorization': authHeader,
                    'Content-Type': 'application/json',
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('AI Suggestions API error:', error);
        return NextResponse.json(
            { detail: 'AI 제안 조회 중 오류가 발생했습니다.' },
            { status: 500 }
        );
    }
}

