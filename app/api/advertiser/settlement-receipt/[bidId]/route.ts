import { NextRequest, NextResponse } from 'next/server'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ bidId: string }> | { bidId: string } }
) {
    try {
        const authHeader = request.headers.get('authorization')

        if (!authHeader) {
            console.error('[SettlementReceipt API] No authorization header')
            return NextResponse.json(
                { message: 'Authorization header required' },
                { status: 401 }
            )
        }

        // Next.js 15 호환: params가 Promise일 수 있음
        const resolvedParams = await Promise.resolve(params)
        const { bidId } = resolvedParams

        if (!bidId) {
            console.error('[SettlementReceipt API] No bidId provided')
            return NextResponse.json(
                { message: 'Bid ID is required' },
                { status: 400 }
            )
        }

        console.log(`[SettlementReceipt API] Fetching receipt for bidId: ${bidId}`)
        const serviceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
        const url = `${serviceUrl}/settlement-receipt/${bidId}`

        console.log(`[SettlementReceipt API] Calling: ${url}`)

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        })

        console.log(`[SettlementReceipt API] Response status: ${response.status}`)

        if (!response.ok) {
            let errorMessage = 'Failed to fetch settlement receipt'
            try {
                const errorData = await response.json()
                errorMessage = errorData.detail || errorData.message || errorMessage
                console.error(`[SettlementReceipt API] Error response:`, errorData)
            } catch (parseError) {
                const errorText = await response.text()
                errorMessage = errorText || `Server error (${response.status})`
                console.error(`[SettlementReceipt API] Failed to parse error:`, errorText)
            }
            return NextResponse.json(
                { message: errorMessage },
                { status: response.status }
            )
        }

        const data = await response.json()
        console.log(`[SettlementReceipt API] Success, data keys:`, Object.keys(data))
        return NextResponse.json(data)
    } catch (error) {
        console.error('[SettlementReceipt API] Exception:', error)
        const errorMessage = error instanceof Error ? error.message : 'Internal server error'
        return NextResponse.json(
            { message: errorMessage },
            { status: 500 }
        )
    }
}

