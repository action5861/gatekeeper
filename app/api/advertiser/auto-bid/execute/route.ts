import { NextRequest, NextResponse } from 'next/server'

// POST: 자동 입찰 실행
export async function POST(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const body = await request.json()
        const {
            search_query,
            quality_score,
            match_type,
            match_score,
            competitor_count
        } = body

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'

        // 광고주 ID 조회
        const advertiserResponse = await fetch(`${advertiserServiceUrl}/me`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })

        if (!advertiserResponse.ok) {
            return NextResponse.json({ error: 'Failed to get advertiser info' }, { status: advertiserResponse.status })
        }

        const advertiserData = await advertiserResponse.json()
        const advertiserId = advertiserData.id

        // 자동 입찰 실행
        const executeResponse = await fetch(
            `${advertiserServiceUrl}/auto-bid/execute`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search_query,
                    quality_score,
                    match_type,
                    match_score,
                    competitor_count
                }),
            }
        )

        if (!executeResponse.ok) {
            const errorData = await executeResponse.json()
            return NextResponse.json(errorData, { status: executeResponse.status })
        }

        const executeData = await executeResponse.json()

        return NextResponse.json({
            success: true,
            data: executeData
        })

    } catch (error) {
        console.error('Error executing auto bid:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 