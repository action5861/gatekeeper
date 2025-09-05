import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { userType, email, password } = body

        // Validate required fields
        if (!userType || !email || !password) {
            return NextResponse.json(
                { message: 'Missing required fields: userType, email, and password are required' },
                { status: 400 }
            )
        }

        console.log(`Attempting login for ${userType} via API Gateway`)

        const requestBody = userType === 'advertiser'
            ? { username: email, password: password }  // 사업자는 이메일을 username으로 사용
            : { email: email, password: password }

        // API Gateway를 통해 로그인 처리
        const gatewayPath = userType === 'advertiser'
            ? '/api/advertiser/login'
            : '/api/auth/login';

        const response = await fetch(`${API_GATEWAY_URL}${gatewayPath}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        })

        const data = await response.json()

        if (!response.ok) {
            console.error(`Login failed for ${userType}:`, data)
            return NextResponse.json(
                { message: data.detail || `Login failed for ${userType}` },
                { status: response.status }
            )
        }

        console.log(`Login successful for ${userType} via API Gateway`)

        // Add userType to the response for frontend routing
        return NextResponse.json({
            ...data,
            userType: userType
        })
    } catch (error) {
        console.error('Login API error:', error)
        return NextResponse.json(
            { message: 'Internal server error - please try again later' },
            { status: 500 }
        )
    }
} 