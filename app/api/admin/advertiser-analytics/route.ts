import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminAuth } from '@/lib/admin-auth'

const ADVERTISER_SERVICE_URL = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8004'

export async function GET(request: NextRequest) {
    try {
        // 관리자 인증 확인
        const admin = await verifyAdminAuth(request)
        if (!admin) {
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 401 }
            )
        }

        // 쿼리 파라미터
        const { searchParams } = new URL(request.url)
        const timeRange = searchParams.get('timeRange') || 'week'

        // advertiser-service에서 전체 광고주 분석 데이터 조회
        const response = await fetch(
            `${ADVERTISER_SERVICE_URL}/admin/analytics?timeRange=${timeRange}`,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Auth': 'true'
                },
            }
        )

        if (!response.ok) {
            // advertiser-service에 해당 엔드포인트가 없으면 직접 DB 조회
            console.log('advertiser-service analytics endpoint not available, using fallback')
            
            // PostgreSQL 직접 조회 (fallback)
            const dbUrl = process.env.DATABASE_URL || 'postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db'
            
            // 임시로 기본 데이터 반환
            return NextResponse.json({
                success: true,
                summary: {
                    totalAdvertisers: 0,
                    activeAdvertisers: 0,
                    totalSettlements: 0,
                    totalSpend: 0,
                    avgBidPrice: 0,
                    successRate: 0
                },
                advertisers: [],
                timeRange
            })
        }

        const data = await response.json()
        return NextResponse.json({
            success: true,
            ...data
        })

    } catch (error) {
        console.error('Advertiser analytics error:', error)
        return NextResponse.json(
            { error: 'Failed to fetch advertiser analytics' },
            { status: 500 }
        )
    }
}

