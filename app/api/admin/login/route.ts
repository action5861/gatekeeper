import { SignJWT } from 'jose'
import { NextRequest, NextResponse } from 'next/server'

const SECRET_KEY = new TextEncoder().encode(
    process.env.SECRET_KEY || 'your-secret-key-here'
)

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
            // JWT 토큰 생성
            const token = await new SignJWT({
                sub: 'admin',
                username: ADMIN_CREDENTIALS.username,
                email: ADMIN_CREDENTIALS.email,
                role: 'admin'
            })
                .setProtectedHeader({ alg: 'HS256' })
                .setIssuedAt()
                .setExpirationTime('24h')
                .sign(SECRET_KEY)

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