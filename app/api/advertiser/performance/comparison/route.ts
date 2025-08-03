import { NextRequest, NextResponse } from 'next/server'

// GET: 자동 vs 수동 입찰 성과 비교
export async function GET(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const { searchParams } = new URL(request.url)
        const timeRange = searchParams.get('timeRange') || 'week'

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

        // 성과 비교 데이터 조회
        const comparisonResponse = await fetch(
            `${advertiserServiceUrl}/performance/comparison/${advertiserId}?timeRange=${timeRange}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            }
        )

        if (!comparisonResponse.ok) {
            return NextResponse.json({ error: 'Failed to get performance comparison' }, { status: comparisonResponse.status })
        }

        const comparisonData = await comparisonResponse.json()

        return NextResponse.json({
            success: true,
            data: comparisonData
        })

    } catch (error) {
        console.error('Error fetching performance comparison:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 