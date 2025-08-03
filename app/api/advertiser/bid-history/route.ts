import { NextRequest, NextResponse } from 'next/server'

// GET: 입찰 내역 조회
export async function GET(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const { searchParams } = new URL(request.url)
        const timeRange = searchParams.get('timeRange') || 'week'
        const filter = searchParams.get('filter') || 'all'
        const resultFilter = searchParams.get('resultFilter') || 'all'

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

        // 입찰 내역 조회
        const bidHistoryResponse = await fetch(
            `${advertiserServiceUrl}/bid-history/${advertiserId}?timeRange=${timeRange}&filter=${filter}&resultFilter=${resultFilter}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            }
        )

        if (!bidHistoryResponse.ok) {
            return NextResponse.json({ error: 'Failed to get bid history' }, { status: bidHistoryResponse.status })
        }

        const bidHistory = await bidHistoryResponse.json()

        // 통계 계산
        const totalBids = bidHistory.length
        const wonBids = bidHistory.filter((bid: any) => bid.result === 'won').length
        const lostBids = bidHistory.filter((bid: any) => bid.result === 'lost').length
        const pendingBids = bidHistory.filter((bid: any) => bid.result === 'pending').length
        const successRate = totalBids > 0 ? (wonBids / totalBids) * 100 : 0
        const totalSpent = bidHistory.filter((bid: any) => bid.result === 'won').reduce((sum: number, bid: any) => sum + bid.bidAmount, 0)
        const averageBidAmount = totalBids > 0 ? bidHistory.reduce((sum: number, bid: any) => sum + bid.bidAmount, 0) / totalBids : 0
        const autoBidCount = bidHistory.filter((bid: any) => bid.isAutoBid).length
        const manualBidCount = bidHistory.filter((bid: any) => !bid.isAutoBid).length

        // ROI 계산 (예시: 클릭당 평균 수익 5000원 가정)
        const totalClicks = wonBids // 성공한 입찰 = 클릭으로 가정
        const totalRevenue = totalClicks * 5000 // 예시 수익
        const roi = totalSpent > 0 ? ((totalRevenue - totalSpent) / totalSpent) * 100 : 0

        return NextResponse.json({
            success: true,
            data: {
                bidHistory: bidHistory,
                statistics: {
                    totalBids,
                    wonBids,
                    lostBids,
                    pendingBids,
                    successRate,
                    totalSpent,
                    averageBidAmount,
                    autoBidCount,
                    manualBidCount,
                    totalClicks,
                    totalRevenue,
                    roi
                }
            }
        })

    } catch (error) {
        console.error('Error fetching bid history:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 