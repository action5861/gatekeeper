import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
    try {
        const authHeader = request.headers.get('authorization')

        if (!authHeader) {
            return NextResponse.json(
                { message: 'Authorization header required' },
                { status: 401 }
            )
        }

        const serviceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'

        const response = await fetch(`${serviceUrl}/dashboard`, {
            method: 'GET',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { message: data.detail || 'Failed to fetch dashboard data' },
                { status: response.status }
            )
        }

        return NextResponse.json(data)
    } catch (error) {
        console.error('Advertiser dashboard API error:', error)
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
} 