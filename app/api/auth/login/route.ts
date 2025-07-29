import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { userType, email, password } = body

        const serviceUrl = userType === 'advertiser'
            ? process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
            : process.env.USER_SERVICE_URL || 'http://localhost:8005'

        const response = await fetch(`${serviceUrl}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
            }),
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { message: data.detail || 'Login failed' },
                { status: response.status }
            )
        }

        return NextResponse.json(data)
    } catch (error) {
        console.error('Login API error:', error)
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
} 