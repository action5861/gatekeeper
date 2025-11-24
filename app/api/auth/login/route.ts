import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';
const SECRET_KEY = new TextEncoder().encode(
    process.env.JWT_SECRET_KEY || process.env.SECRET_KEY || 'your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum'
);

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

        // 응답 본문을 안전하게 파싱
        let data: any = {}
        try {
            const text = await response.text()
            const contentType = response.headers.get('content-type')
            
            if (contentType && contentType.includes('application/json')) {
                try {
                    data = JSON.parse(text)
                } catch (parseError) {
                    console.error(`Failed to parse JSON response for ${userType}:`, parseError)
                    console.error(`Response text: ${text.substring(0, 500)}`)
                    data = { detail: text || `Login failed with status ${response.status}` }
                }
            } else {
                console.error(`Non-JSON response for ${userType} (${contentType}):`, text.substring(0, 500))
                try {
                    data = JSON.parse(text)
                } catch {
                    data = { detail: text || `Login failed with status ${response.status}` }
                }
            }
        } catch (readError) {
            console.error(`Failed to read response for ${userType}:`, readError)
            data = { detail: `Failed to read response: ${readError instanceof Error ? readError.message : 'Unknown error'}` }
        }

        if (!response.ok) {
            console.error(`Login failed for ${userType}:`, data)
            return NextResponse.json(
                { message: data.detail || data.message || `Login failed for ${userType}` },
                { status: response.status }
            )
        }

        console.log(`Login successful for ${userType} via API Gateway`)

        // 백엔드에서 받은 토큰을 그대로 사용
        // 광고주의 경우 백엔드 서비스가 이미 advertiser_id를 토큰에 포함하고 있음
        return NextResponse.json({
            access_token: data.access_token,
            token_type: 'bearer',
            userType: userType
        });
    } catch (error) {
        console.error('Login API error:', error)
        return NextResponse.json(
            { message: 'Internal server error - please try again later' },
            { status: 500 }
        )
    }
} 