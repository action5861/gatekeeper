import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { userType, email, password, username, companyName, businessSetup } = body

        const serviceUrl = userType === 'advertiser'
            ? process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
            : process.env.USER_SERVICE_URL || 'http://user-service:8005'

        const requestBody = userType === 'advertiser'
            ? {
                username: email, // 사업자는 이메일을 username으로 사용
                email: email,
                password: password,
                company_name: companyName,
                business_setup: businessSetup, // 비즈니스 설정 데이터 추가
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

        // Add userType to the response for frontend routing
        return NextResponse.json({
            ...data,
            userType: userType
        })
    } catch (error) {
        console.error('Registration API error:', error)
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
} 