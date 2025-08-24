import { requireAdminAuth } from '@/lib/admin-auth'
import { NextRequest, NextResponse } from 'next/server'

// 심사 대기 목록 조회
export async function GET(request: NextRequest) {
    try {
        await requireAdminAuth(request)

        const { searchParams } = new URL(request.url)
        const status = searchParams.get('status')

        console.log('=== API 라우트 디버깅 ===')
        console.log('요청 URL:', request.url)
        console.log('Status 파라미터:', status)

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'

        let endpoint = '/admin/pending-reviews'
        if (status === 'rejected') {
            endpoint = '/admin/rejected-advertisers'
        } else if (status === 'approved') {
            endpoint = '/admin/approved-advertisers'
        }

        const fullUrl = `${advertiserServiceUrl}${endpoint}`
        console.log('전체 요청 URL:', fullUrl)

        const response = await fetch(fullUrl)

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

        // 카테고리 path -> id 매핑 (프론트는 id 배열을 기대함)
        try {
            // 광고주 서비스의 카테고리로만 매핑하여 소스 불일치를 방지
            const svcCategoriesRes = await fetch(`${advertiserServiceUrl}/business-categories`)
            if (!svcCategoriesRes.ok) throw new Error(`category fetch ${svcCategoriesRes.status}`)
            const allCategories = await svcCategoriesRes.json()
            const pathToId = new Map<string, number>()
                ; (allCategories as any[]).forEach((c) => pathToId.set(c.path, c.id))

            const transformed = {
                ...data,
                advertisers: Array.isArray(data.advertisers)
                    ? data.advertisers.map((adv: any) => ({
                        ...adv,
                        categories: Array.isArray(adv.categories)
                            ? adv.categories
                                .map((path: string) => pathToId.get(path))
                                .filter((v: number | undefined): v is number => typeof v === 'number')
                            : [],
                    }))
                    : [],
            }

            return NextResponse.json(transformed)
        } catch (mapErr) {
            console.error('카테고리 매핑 실패 (path->id):', mapErr)
            // 매핑 실패 시 원본 반환
            return NextResponse.json(data)
        }

    } catch (error) {
        console.error('Error fetching advertisers:', error)
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

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
        const qs = new URLSearchParams()
        qs.set('advertiser_id', String(advertiser_id))
        qs.set('review_status', String(review_status))
        qs.set('review_notes', String(review_notes || ''))
        qs.set('recommended_bid_min', String(recommended_bid_min))
        qs.set('recommended_bid_max', String(recommended_bid_max))

        const response = await fetch(`${advertiserServiceUrl}/admin/update-review?${qs.toString()}`, {
            method: 'PUT',
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
        const { advertiser_id, keywords, categories } = body as { advertiser_id: number; keywords: string[]; categories: number[] }

        // 광고주 서비스 카테고리(플랫) 조회하여 id -> path 매핑
        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
        const svcCategoriesRes = await fetch(`${advertiserServiceUrl}/business-categories`)
        if (!svcCategoriesRes.ok) {
            return NextResponse.json({ error: 'Failed to load categories for mapping' }, { status: 500 })
        }
        const allCategories: Array<{ id: number; path: string }> = await svcCategoriesRes.json()
        const idToPath = new Map<number, string>()
        allCategories.forEach((c) => idToPath.set(c.id, c.path))
        const categoryPaths: string[] = Array.isArray(categories)
            ? categories.map((id) => idToPath.get(id)).filter((p): p is string => typeof p === 'string')
            : []

        // FastAPI 엔드포인트는 Query 파라미터로 수신함 (List는 키 반복)
        const qs = new URLSearchParams()
        qs.set('advertiser_id', String(advertiser_id))
            ; (keywords || []).forEach((k) => qs.append('keywords', String(k)))
        categoryPaths.forEach((p) => qs.append('categories', p))

        const response = await fetch(`${advertiserServiceUrl}/admin/update-advertiser-data?${qs.toString()}`, {
            method: 'PATCH',
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