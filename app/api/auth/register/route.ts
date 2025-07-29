import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { userType, email, password, username, companyName } = body

        const serviceUrl = userType === 'advertiser'
            ? process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
            : process.env.USER_SERVICE_URL || 'http://localhost:8005'

        const requestBody = userType === 'advertiser'
            ? {
                username: username || email, // Use provided username or fallback to email
                email: email,
                password: password,
                company_name: companyName,
            }
            : {
                username: username || email, // Use provided username or fallback to email
                email: email,
                password: password,
            }

        const response = await fetch(`${serviceUrl}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        })

        const data = await response.json()

        if (!response.ok) {
            return NextResponse.json(
                { message: data.detail || 'Registration failed' },
                { status: response.status }
            )
        }

        return NextResponse.json(data)
    } catch (error) {
        console.error('Registration API error:', error)
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
} 