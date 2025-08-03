import { requireAdminAuth } from '@/lib/admin-auth'
import { NextRequest, NextResponse } from 'next/server'

// 심사 대기 목록 조회
export async function GET(request: NextRequest) {
    try {
        await requireAdminAuth(request)

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
        const response = await fetch(`${advertiserServiceUrl}/admin/pending-reviews`)

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to fetch pending reviews' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error) {
        console.error('Error fetching pending reviews:', error)
        if (error instanceof Error && error.message.includes('Unauthorized')) {
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 401 }
            )
        }
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

// 심사 결과 업데이트 (승인/거절)
export async function PUT(request: NextRequest) {
    try {
        await requireAdminAuth(request)

        const body = await request.json()
        const { advertiser_id, review_status, review_notes, recommended_bid_min, recommended_bid_max } = body

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
        const response = await fetch(`${advertiserServiceUrl}/admin/update-review`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                advertiser_id,
                review_status,
                review_notes,
                recommended_bid_min,
                recommended_bid_max
            }),
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to update review' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error) {
        console.error('Error updating review:', error)
        if (error instanceof Error && error.message.includes('Unauthorized')) {
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 401 }
            )
        }
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

// 키워드/카테고리 수정
export async function PATCH(request: NextRequest) {
    try {
        await requireAdminAuth(request)

        const body = await request.json()
        const { advertiser_id, keywords, categories } = body

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
        const response = await fetch(`${advertiserServiceUrl}/admin/update-advertiser-data`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                advertiser_id,
                keywords,
                categories
            }),
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to update advertiser data' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error) {
        console.error('Error updating advertiser data:', error)
        if (error instanceof Error && error.message.includes('Unauthorized')) {
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 401 }
            )
        }
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 