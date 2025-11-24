import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    try {
        // 클라이언트의 Authorization 헤더 가져오기
        const authHeader = request.headers.get('authorization');

        if (!authHeader) {
            return NextResponse.json(
                { detail: '인증이 필요합니다.' },
                { status: 401 }
            );
        }

        // 요청 본문 읽기
        const body = await request.json();

        // API Gateway를 통해 advertiser-service로 요청 전달
        const response = await fetch(
            `${process.env.API_GATEWAY_URL}/api/advertiser/confirm-suggestions`,
            {
                method: 'POST',
                headers: {
                    'Authorization': authHeader,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            }
        );

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('Confirm Suggestions API error:', error);
        return NextResponse.json(
            { detail: '설정 확정 중 오류가 발생했습니다.' },
            { status: 500 }
        );
    }
}

