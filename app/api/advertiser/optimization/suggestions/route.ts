import { NextRequest, NextResponse } from 'next/server'

// GET: 머신러닝 기반 최적화 제안
export async function GET(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

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

        // 최적화 제안 조회
        const suggestionsResponse = await fetch(
            `${advertiserServiceUrl}/optimization/suggestions/${advertiserId}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            }
        )

        if (!suggestionsResponse.ok) {
            return NextResponse.json({ error: 'Failed to get optimization suggestions' }, { status: suggestionsResponse.status })
        }

        const suggestionsData = await suggestionsResponse.json()

        return NextResponse.json({
            success: true,
            data: suggestionsData
        })

    } catch (error) {
        console.error('Error fetching optimization suggestions:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 