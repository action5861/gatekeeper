// 인증 관련 유틸리티 함수들
import { jwtVerify } from 'jose';
import { NextRequest } from 'next/server';

const SECRET_KEY = new TextEncoder().encode(
    process.env.JWT_SECRET_KEY || process.env.SECRET_KEY || 'your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum'
)

export interface AuthError {
    isTokenExpired: boolean;
    message: string;
}

export interface User {
    id: string;
    username: string;
    email: string;
    userType: 'user' | 'advertiser';
}

/**
 * JWT 토큰에서 사용자 정보를 추출합니다.
 * JWT의 sub 필드는 이메일이므로, 이를 통해 실제 user_id를 조회합니다.
 */
export async function verifyUserAuth(request: NextRequest): Promise<User | null> {
    try {
        const authHeader = request.headers.get('authorization')

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            console.log('No valid authorization header found')
            return null
        }

        const token = authHeader.substring(7)
        const issuer = process.env.JWT_ISSUER || 'digisafe-api'
        const audience = process.env.JWT_AUDIENCE || 'digisafe-client'

        const { payload } = await jwtVerify(token, SECRET_KEY, {
            issuer: issuer,
            audience: audience
        })

        console.log('JWT payload:', payload)

        // JWT의 sub는 이메일이므로, 이를 통해 실제 user_id를 조회
        const email = payload.sub as string
        if (!email) {
            console.error('No email found in JWT payload')
            return null
        }

        // JWT 토큰에서 직접 user_id 추출 (User service에서 user_id를 포함하도록 수정됨)
        const userId = payload.user_id as number || payload.userId as number
        const username = payload.username as string
        const userType = payload.userType as string

        console.log('JWT payload extracted:', {
            email,
            userId,
            username,
            userType
        })

        // user_id가 없으면 fallback으로 1 사용 (기존 사용자)
        const finalUserId = userId ? userId.toString() : '1'

        return {
            id: finalUserId,
            username: username || email.split('@')[0],
            email: email,
            userType: (userType as 'user' | 'advertiser') || 'user'
        }
    } catch (error) {
        console.error('User auth verification failed:', error)
        return null
    }
}

/**
 * API 응답에서 토큰 만료 오류를 확인합니다.
 */
export function checkTokenExpiry(response: Response, responseData?: any): AuthError | null {
    if (response.status === 401) {
        const errorMessage = responseData?.detail || responseData?.error || '인증이 필요합니다.';

        if (errorMessage.includes('expired') || errorMessage.includes('Token has expired')) {
            return {
                isTokenExpired: true,
                message: '로그인이 만료되었습니다. 다시 로그인해주세요.'
            };
        }

        return {
            isTokenExpired: false,
            message: errorMessage
        };
    }

    return null;
}

/**
 * 토큰 만료 시 로그아웃 처리 및 로그인 페이지로 리다이렉트
 */
export function handleTokenExpiry(): void {
    if (typeof window === 'undefined') return;

    // 토큰 및 사용자 정보 제거
    localStorage.removeItem('token');
    localStorage.removeItem('userType');

    // 로그인 페이지로 리다이렉트
    window.location.href = '/login';
}

/**
 * API 요청 시 토큰을 포함한 헤더를 생성합니다.
 */
export function getAuthHeaders(): Record<string, string> {
    if (typeof window === 'undefined') return {};

    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/**
 * 인증된 API 요청을 위한 fetch 래퍼
 * 토큰 만료 시 자동으로 로그인 페이지로 리다이렉트
 */
export async function authenticatedFetch(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
    };

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // 토큰 만료 확인
    if (response.status === 401) {
        try {
            const responseData = await response.json();
            const authError = checkTokenExpiry(response, responseData);

            if (authError?.isTokenExpired) {
                console.warn('토큰이 만료되었습니다. 로그인 페이지로 리다이렉트합니다.');
                handleTokenExpiry();
                throw new Error(authError.message);
            }
        } catch (parseError) {
            // JSON 파싱 실패 시에도 토큰 만료로 간주
            console.warn('인증 오류가 발생했습니다. 로그인 페이지로 리다이렉트합니다.');
            handleTokenExpiry();
            throw new Error('인증이 필요합니다.');
        }
    }

    return response;
}
