import { jwtVerify } from 'jose'
import { NextRequest } from 'next/server'

const SECRET_KEY = new TextEncoder().encode(
    process.env.JWT_SECRET_KEY || process.env.SECRET_KEY || 'your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum'
)

// 환경 변수 디버깅
console.log('=== JWT Secret Key Debug ===')
console.log('JWT_SECRET_KEY exists:', !!process.env.JWT_SECRET_KEY)
console.log('SECRET_KEY exists:', !!process.env.SECRET_KEY)
console.log('Using fallback key:', !process.env.JWT_SECRET_KEY && !process.env.SECRET_KEY)
console.log('SECRET_KEY length:', SECRET_KEY.length)

export interface AdminUser {
    id: string
    username: string
    email: string
    role: 'admin'
}

export async function verifyAdminAuth(request: NextRequest): Promise<AdminUser | null> {
    try {
        const authHeader = request.headers.get('authorization')
        console.log('=== Admin Auth Debug ===')
        console.log('Authorization header:', authHeader)
        console.log('SECRET_KEY length:', SECRET_KEY.length)
        console.log('SECRET_KEY first 10 bytes:', Array.from(SECRET_KEY.slice(0, 10)))

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            console.log('No valid authorization header found')
            return null
        }

        const token = authHeader.substring(7)
        console.log('Extracted token length:', token.length)
        console.log('Extracted token first 20 chars:', token.substring(0, 20))
        console.log('Extracted token last 20 chars:', token.substring(token.length - 20))

        const issuer = process.env.JWT_ISSUER || 'digisafe-api'
        const audience = process.env.JWT_AUDIENCE || 'digisafe-client'

        const { payload } = await jwtVerify(token, SECRET_KEY, {
            issuer: issuer,
            audience: audience
        })
        console.log('JWT payload:', payload)
        console.log('JWT payload role:', payload.role)
        console.log('JWT payload sub:', payload.sub)
        console.log('JWT payload username:', payload.username)
        console.log('JWT payload iss (issuer):', payload.iss)
        console.log('JWT payload aud (audience):', payload.aud)
        console.log('JWT payload iat (issued at):', payload.iat)
        console.log('JWT payload exp (expires at):', payload.exp)
        console.log('Current timestamp:', Math.floor(Date.now() / 1000))
        console.log('Token expired?', payload.exp ? payload.exp < Math.floor(Date.now() / 1000) : 'unknown')

        // 관리자 역할 확인
        if (payload.role !== 'admin') {
            console.log('Role mismatch - expected: admin, got:', payload.role)
            return null
        }

        console.log('Admin auth successful')
        return {
            id: payload.sub as string,
            username: payload.username as string,
            email: payload.email as string,
            role: payload.role as 'admin'
        }
    } catch (error) {
        console.error('Admin auth verification failed:', error)
        console.error('Error details:', {
            name: error instanceof Error ? error.name : 'Unknown',
            message: error instanceof Error ? error.message : 'Unknown error',
            stack: error instanceof Error ? error.stack : 'No stack'
        })
        return null
    }
}

export async function requireAdminAuth(request: NextRequest): Promise<AdminUser> {
    console.log('=== requireAdminAuth called ===')
    const admin = await verifyAdminAuth(request)
    if (!admin) {
        console.log('Admin auth failed, throwing 403 error')
        throw new Error('Unauthorized: Admin access required')
    }
    console.log('Admin auth successful, returning admin:', admin.username)
    return admin
} 