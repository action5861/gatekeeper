import { NextRequest, NextResponse } from 'next/server'

export async function GET(
    request: NextRequest,
    { params }: { params: { advertiserId: string } }
) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const advertiserId = params.advertiserId
        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'

        const response = await fetch(`${advertiserServiceUrl}/keywords/${advertiserId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to fetch keywords' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Error fetching keywords:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

export async function PUT(
    request: NextRequest,
    { params }: { params: { advertiserId: string } }
) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const advertiserId = params.advertiserId
        const keywords = await request.json()

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'

        const response = await fetch(`${advertiserServiceUrl}/keywords/${advertiserId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(keywords),
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to update keywords' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Error updating keywords:', error)
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
}

