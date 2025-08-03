import { NextRequest, NextResponse } from 'next/server'

// GET: 자동 입찰 성과 분석
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

        // 자동 입찰 분석 데이터 조회
        const analyticsResponse = await fetch(
            `${advertiserServiceUrl}/analytics/auto-bidding/${advertiserId}?timeRange=${timeRange}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            }
        )

        if (!analyticsResponse.ok) {
            return NextResponse.json({ error: 'Failed to get analytics data' }, { status: analyticsResponse.status })
        }

        const analyticsData = await analyticsResponse.json()

        return NextResponse.json({
            success: true,
            data: analyticsData
        })

    } catch (error) {
        console.error('Error fetching analytics data:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 