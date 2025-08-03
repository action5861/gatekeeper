import { NextRequest, NextResponse } from 'next/server'

// GET: 현재 자동 입찰 설정 조회
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

        // 자동 입찰 설정 조회
        const settingsResponse = await fetch(`${advertiserServiceUrl}/auto-bid-settings/${advertiserId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })

        if (!settingsResponse.ok) {
            return NextResponse.json({ error: 'Failed to get auto bid settings' }, { status: settingsResponse.status })
        }

        const settings = await settingsResponse.json()

        // 키워드 목록 조회
        const keywordsResponse = await fetch(`${advertiserServiceUrl}/keywords/${advertiserId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })

        const keywords = keywordsResponse.ok ? await keywordsResponse.json() : []

        return NextResponse.json({
            success: true,
            data: {
                autoBidSettings: settings,
                keywords: keywords,
            }
        })

    } catch (error) {
        console.error('Error fetching auto bid settings:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

// PUT: 자동 입찰 설정 업데이트
export async function PUT(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const body = await request.json()
        const {
            isEnabled,
            dailyBudget,
            maxBidPerKeyword,
            minQualityScore,
            keywords,
            excludedKeywords
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

        // 자동 입찰 설정 업데이트
        const settingsResponse = await fetch(`${advertiserServiceUrl}/auto-bid-settings/${advertiserId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_enabled: isEnabled,
                daily_budget: dailyBudget,
                max_bid_per_keyword: maxBidPerKeyword,
                min_quality_score: minQualityScore,
                excluded_keywords: excludedKeywords
            }),
        })

        if (!settingsResponse.ok) {
            return NextResponse.json({ error: 'Failed to update auto bid settings' }, { status: settingsResponse.status })
        }

        // 키워드 업데이트
        if (keywords && keywords.length > 0) {
            const keywordsResponse = await fetch(`${advertiserServiceUrl}/keywords/${advertiserId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keywords }),
            })

            if (!keywordsResponse.ok) {
                return NextResponse.json({ error: 'Failed to update keywords' }, { status: keywordsResponse.status })
            }
        }

        return NextResponse.json({
            success: true,
            message: '자동 입찰 설정이 업데이트되었습니다.'
        })

    } catch (error) {
        console.error('Error updating auto bid settings:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

// POST: 제외 키워드 추가/삭제
export async function POST(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const body = await request.json()
        const { action, keyword } = body // action: 'add' | 'remove'

        if (!action || !keyword) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
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

        // 제외 키워드 업데이트
        const response = await fetch(`${advertiserServiceUrl}/excluded-keywords/${advertiserId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action, keyword }),
        })

        if (!response.ok) {
            return NextResponse.json({ error: 'Failed to update excluded keywords' }, { status: response.status })
        }

        const result = await response.json()

        return NextResponse.json({
            success: true,
            message: action === 'add' ? '제외 키워드가 추가되었습니다.' : '제외 키워드가 삭제되었습니다.',
            data: result
        })

    } catch (error) {
        console.error('Error updating excluded keywords:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 