import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: { bidId: string } }
) {
    try {
        const bidId = params.bidId;
        const authHeader = request.headers.get('authorization');

        if (!authHeader) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        console.log(`[API] Fetching bid info for: ${bidId}`);

        // API Gateway를 통해 경매 서비스의 bid 정보 조회
        const response = await fetch(`${API_GATEWAY_URL}/api/auction/bid/${bidId}`, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
            },
        });

        if (!response.ok) {
            console.error(`[API] Failed to get bid info: ${response.status}`);
            return NextResponse.json(
                { error: 'Failed to fetch bid information' },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log(`[API] Bid info retrieved:`, data);

        return NextResponse.json(data);

    } catch (error) {
        console.error('[API] Error fetching bid info:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}



