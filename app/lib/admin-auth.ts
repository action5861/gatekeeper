import { jwtVerify } from 'jose'
import { NextRequest } from 'next/server'

const SECRET_KEY = new TextEncoder().encode(
    process.env.SECRET_KEY || 'your-secret-key-here'
)

export interface AdminUser {
    id: string
    username: string
    email: string
    role: 'admin'
}

export async function verifyAdminAuth(request: NextRequest): Promise<AdminUser | null> {
    try {
        const authHeader = request.headers.get('authorization')
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return null
        }

        const token = authHeader.substring(7)
        const { payload } = await jwtVerify(token, SECRET_KEY)

        // 관리자 역할 확인
        if (payload.role !== 'admin') {
            return null
        }

        return {
            id: payload.sub as string,
            username: payload.username as string,
            email: payload.email as string,
            role: payload.role as 'admin'
        }
    } catch (error) {
        console.error('Admin auth verification failed:', error)
        return null
    }
}

export async function requireAdminAuth(request: NextRequest): Promise<AdminUser> {
    const admin = await verifyAdminAuth(request)
    if (!admin) {
        throw new Error('Unauthorized: Admin access required')
    }
    return admin
} 