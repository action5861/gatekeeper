import { NextRequest, NextResponse } from 'next/server'

export async function PUT(request: NextRequest) {
    try {
        const authHeader = request.headers.get('authorization')

        if (!authHeader) {
            return NextResponse.json(
                { message: 'Authorization header required' },
                { status: 401 }
            )
        }

        const body = await request.json()
        const serviceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'

        const response = await fetch(`${serviceUrl}/update-account-info`, {
            method: 'PUT',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { message: data.detail || 'Failed to update account info' },
                { status: response.status }
            )
        }

        return NextResponse.json(data)
    } catch (error) {
        console.error('Advertiser update account info API error:', error)
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
}
