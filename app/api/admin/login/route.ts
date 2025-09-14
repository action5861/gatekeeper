import { SignJWT } from 'jose'
import { NextRequest, NextResponse } from 'next/server'

const SECRET_KEY = new TextEncoder().encode(
    process.env.JWT_SECRET_KEY || process.env.SECRET_KEY || 'your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum'
)

// 환경 변수 디버깅
console.log('=== Admin Login JWT Secret Key Debug ===')
console.log('JWT_SECRET_KEY exists:', !!process.env.JWT_SECRET_KEY)
console.log('SECRET_KEY exists:', !!process.env.SECRET_KEY)
console.log('Using fallback key:', !process.env.JWT_SECRET_KEY && !process.env.SECRET_KEY)
console.log('SECRET_KEY length:', SECRET_KEY.length)

// 관리자 계정 정보 (실제 운영에서는 데이터베이스에서 관리)
const ADMIN_CREDENTIALS = {
    username: 'admin',
    password: 'admin123', // 실제 운영에서는 해시된 비밀번호 사용
    email: 'admin@example.com'
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { username, password } = body

        // 입력 검증
        if (!username || !password) {
            return NextResponse.json(
                { error: '사용자명과 비밀번호를 입력해주세요.' },
                { status: 400 }
            )
        }

        // 관리자 인증
        if (username === ADMIN_CREDENTIALS.username && password === ADMIN_CREDENTIALS.password) {
            console.log('=== Admin Login Success ===')
            console.log('Creating JWT token for admin:', username)

            // JWT 토큰 생성
            const expireMinutes = parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || '30')
            const issuer = process.env.JWT_ISSUER || 'digisafe-api'
            const audience = process.env.JWT_AUDIENCE || 'digisafe-client'

            console.log('Token expiration time:', `${expireMinutes} minutes`)
            console.log('JWT Issuer:', issuer)
            console.log('JWT Audience:', audience)

            const token = await new SignJWT({
                username: ADMIN_CREDENTIALS.username,
                email: ADMIN_CREDENTIALS.email,
                role: 'admin'
            })
                .setProtectedHeader({ alg: 'HS256' })
                .setSubject('admin')
                .setIssuedAt()
                .setExpirationTime(`${expireMinutes}m`)
                .setIssuer(issuer)     // ✅ iss 클레임 (발행자) 설정
                .setAudience(audience) // ✅ aud 클레임 (대상) 설정
                .sign(SECRET_KEY)

            console.log('JWT token created:', token.substring(0, 20) + '...')
            console.log('Token length:', token.length)

            return NextResponse.json({
                success: true,
                message: '관리자 로그인 성공',
                access_token: token,
                user: {
                    username: ADMIN_CREDENTIALS.username,
                    email: ADMIN_CREDENTIALS.email,
                    role: 'admin'
                }
            })
        } else {
            return NextResponse.json(
                { error: '잘못된 사용자명 또는 비밀번호입니다.' },
                { status: 401 }
            )
        }

    } catch (error) {
        console.error('Admin login error:', error)
        return NextResponse.json(
            { error: '서버 오류가 발생했습니다.' },
            { status: 500 }
        )
    }
} 