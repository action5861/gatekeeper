// 인증 관련 유틸리티 함수들

export interface AuthError {
    isTokenExpired: boolean;
    message: string;
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
