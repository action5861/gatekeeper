import { NextRequest, NextResponse } from 'next/server'

// POST: 머신러닝 기반 최적 입찰가 계산
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
            competitor_count,
            budget_remaining
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

        // 최적 입찰가 계산
        const optimizationResponse = await fetch(
            `${advertiserServiceUrl}/auto-bid/optimize`,
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
                    competitor_count,
                    budget_remaining
                }),
            }
        )

        if (!optimizationResponse.ok) {
            return NextResponse.json({ error: 'Failed to optimize bid' }, { status: optimizationResponse.status })
        }

        const optimizationData = await optimizationResponse.json()

        return NextResponse.json({
            success: true,
            data: optimizationData
        })

    } catch (error) {
        console.error('Error optimizing bid:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 