import { requireAdminAuth } from '@/lib/admin-auth'
import { NextRequest, NextResponse } from 'next/server'

// 심사 대기 목록 조회
export async function GET(request: NextRequest) {
    try {
        console.log('=== GET /api/admin/advertiser-review ===')
        console.log('Request headers:', Object.fromEntries(request.headers.entries()))
        console.log('Request URL:', request.url)
        console.log('Request method:', request.method)

        const admin = await requireAdminAuth(request)
        console.log('Admin authenticated:', admin.username)

        const { searchParams } = new URL(request.url)
        const status = searchParams.get('status')

        console.log('=== API 라우트 디버깅 ===')
        console.log('요청 URL:', request.url)
        console.log('Status 파라미터:', status)

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'

        // 실제 광고주 서비스 엔드포인트 사용
        let endpoint = '/admin/pending-reviews'
        if (status === 'rejected') {
            endpoint = '/admin/rejected-advertisers'
        } else if (status === 'approved') {
            endpoint = '/admin/approved-advertisers'
        }

        const fullUrl = `${advertiserServiceUrl}${endpoint}`
        console.log('전체 요청 URL:', fullUrl)

        // Authorization 헤더를 광고주 서비스로 전달
        const authHeader = request.headers.get('authorization')
        console.log('전달할 Authorization 헤더:', authHeader)

        const response = await fetch(fullUrl, {
            headers: {
                'Authorization': authHeader || '',
                'Content-Type': 'application/json'
            }
        })

        console.log('응답 상태:', response.status)

        if (!response.ok) {
            console.log('API 응답 실패:', response.status, response.statusText)
            return NextResponse.json(
                { error: 'Failed to fetch advertisers' },
                { status: response.status }
            )
        }

        const data = await response.json()
        console.log('받은 데이터 개수:', data.advertisers?.length || 0)
        console.log('첫 번째 광고주:', data.advertisers?.[0]?.company_name || '없음')

        // 카테고리는 path 문자열 그대로 반환 (AI 분석 결과 직접 표시)
        return NextResponse.json(data)

    } catch (error) {
        console.error('Error fetching advertisers:', error)
        if (error instanceof Error && error.message.includes('Unauthorized')) {
            console.log('Returning 403 Forbidden due to unauthorized access')
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 403 }
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

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
        const qs = new URLSearchParams()
        qs.set('advertiser_id', String(advertiser_id))
        qs.set('review_status', String(review_status))
        qs.set('review_notes', String(review_notes || ''))
        qs.set('recommended_bid_min', String(recommended_bid_min))
        qs.set('recommended_bid_max', String(recommended_bid_max))

        // Authorization 헤더를 광고주 서비스로 전달
        const authHeader = request.headers.get('authorization')
        console.log('PUT 요청 - 전달할 Authorization 헤더:', authHeader)

        const response = await fetch(`${advertiserServiceUrl}/admin/update-review?${qs.toString()}`, {
            method: 'PUT',
            headers: {
                'Authorization': authHeader || '',
                'Content-Type': 'application/json'
            }
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
        const { advertiser_id, keywords, categories } = body as { advertiser_id: number; keywords: string[]; categories: string[] }

        // FastAPI 엔드포인트는 Query 파라미터로 수신함 (List는 키 반복)
        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
        const qs = new URLSearchParams()
        qs.set('advertiser_id', String(advertiser_id))
            ; (keywords || []).forEach((k) => qs.append('keywords', String(k)))
            ; (categories || []).forEach((c) => qs.append('categories', String(c)))

        // Authorization 헤더를 광고주 서비스로 전달
        const authHeader = request.headers.get('authorization')
        console.log('PATCH 요청 - 전달할 Authorization 헤더:', authHeader)

        const response = await fetch(`${advertiserServiceUrl}/admin/update-advertiser-data?${qs.toString()}`, {
            method: 'PATCH',
            headers: {
                'Authorization': authHeader || '',
                'Content-Type': 'application/json'
            }
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