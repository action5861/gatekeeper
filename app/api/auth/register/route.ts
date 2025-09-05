import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        console.log('🔐 Registration API called via API Gateway')
        const body = await request.json()
        const { userType, email, password, username, companyName, businessSetup } = body

        console.log('📝 Registration data:', { userType, email, username: username || email })

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

        console.log('📤 Request body:', { ...requestBody, password: '[HIDDEN]' })

        // API Gateway를 통해 등록 처리
        const gatewayPath = userType === 'advertiser'
            ? '/api/advertiser/register'
            : '/api/auth/register';

        console.log('🚀 Sending request to API Gateway...')
        const response = await fetch(`${API_GATEWAY_URL}${gatewayPath}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        })

        console.log('📥 Response status:', response.status)
        console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()))

        const data = await response.json()
        console.log('📥 Response data:', data)

        if (!response.ok) {
            console.log('❌ Service returned error:', data)
            return NextResponse.json(
                { message: data.detail || 'Registration failed' },
                { status: response.status }
            )
        }

        console.log('✅ Registration successful via API Gateway')
        // Add userType to the response for frontend routing
        return NextResponse.json({
            ...data,
            userType: userType
        })
    } catch (error) {
        console.error('💥 Registration API error:', error)
        console.error('💥 Error type:', typeof error)
        console.error('💥 Error message:', error instanceof Error ? error.message : 'Unknown error')
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        )
    }
} 