// Step 1: 실시간 품질 평가 API (사용자 타이핑 시)
// 일일 제출 한도 차감 없음, 분당 호출 제한만 적용

import { verifyUserAuth } from '@/lib/auth';
import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

// 분당 호출 제한을 위한 간단한 메모리 캐시
const rateLimitCache = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_PER_MINUTE = 100; // 분당 100회 제한

function checkRateLimit(identifier: string): boolean {
    const now = Date.now();
    const windowMs = 60 * 1000; // 1분

    const current = rateLimitCache.get(identifier);

    if (!current || now > current.resetTime) {
        // 새로운 윈도우 시작
        rateLimitCache.set(identifier, { count: 1, resetTime: now + windowMs });
        return true;
    }

    if (current.count >= RATE_LIMIT_PER_MINUTE) {
        return false;
    }

    current.count++;
    return true;
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { query } = body;

        console.log(`🔍 [EVALUATE-QUALITY] Received request for query: "${query}"`);

        // 사용자 인증 확인
        const user = await verifyUserAuth(request);
        if (!user) {
            console.log('❌ [EVALUATE-QUALITY] Authentication failed - no valid user token');
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '인증이 필요합니다. 로그인 후 다시 시도해주세요.'
            }, { status: 401 });
        }

        console.log(`✅ [EVALUATE-QUALITY] Authenticated user: ${user.username} (ID: ${user.id})`);

        // 검색어 유효성 검사
        if (!query || typeof query !== 'string' || query.trim().length === 0) {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '검색어를 입력해주세요.'
            }, { status: 400 });
        }

        // 검색어 길이 제한
        if (query.length > 200) {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '검색어는 200자 이내로 입력해주세요.'
            }, { status: 400 });
        }

        // 분당 호출 제한 체크 (IP 기반)
        const clientIP = request.headers.get('x-forwarded-for') ||
            request.headers.get('x-real-ip') ||
            'unknown';

        if (!checkRateLimit(clientIP)) {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'
            }, { status: 429 });
        }

        // Analysis service에 직접 접근 (사용자 인증 정보 포함)
        const ANALYSIS_SERVICE_URL = process.env.ANALYSIS_SERVICE_URL || 'http://localhost:8001';
        const userId = parseInt(user.id, 10); // JWT 토큰의 sub는 보통 문자열이므로 숫자로 변환
        const requestBody = {
            query: query.trim(),
            user_id: userId
        };
        console.log(`🔍 Calling analysis service directly: ${ANALYSIS_SERVICE_URL}/evaluate`);
        console.log(`🔍 Request body:`, JSON.stringify(requestBody));
        const gatewayResponse = await fetch(`${ANALYSIS_SERVICE_URL}/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        console.log(`📊 Analysis service response status: ${gatewayResponse.status}`);
        console.log(`📊 Analysis service response headers:`, Object.fromEntries(gatewayResponse.headers.entries()));

        if (!gatewayResponse.ok) {
            let errorMessage = 'Analysis service error';
            try {
                const errorData = await gatewayResponse.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
                console.error('❌ Analysis service error details:', errorData);
            } catch (parseError) {
                console.error('❌ Failed to parse error response:', parseError);
                errorMessage = `HTTP ${gatewayResponse.status}: ${gatewayResponse.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const analysisData = await gatewayResponse.json();
        console.log('✅ Analysis service response:', analysisData);
        const qualityReport = analysisData.data;

        // 품질 평가 결과만 반환 (경매 시작 없음)
        return NextResponse.json<ApiResponse<{ qualityReport: any }>>({
            success: true,
            data: {
                qualityReport
            },
            message: '품질 평가가 완료되었습니다.'
        }, { status: 200 });

    } catch (error) {
        console.error('Quality Evaluation API Error:', error);

        // API Gateway나 analysis service가 사용 불가능한 경우 클라이언트 사이드 평가로 fallback
        if (error instanceof Error && (
            error.message.includes('fetch') ||
            error.message.includes('ECONNREFUSED') ||
            error.message.includes('timeout') ||
            error.message.includes('Analysis service error')
        )) {
            console.log('🔄 Falling back to client-side quality evaluation');

            // 간단한 클라이언트 사이드 품질 평가
            const fallbackQualityReport = {
                score: Math.min(80, Math.max(20, query.trim().length * 3)), // 기본 점수 계산 (20-80점)
                suggestions: [
                    '서버 연결 문제로 기본 평가를 제공합니다.',
                    '더 정확한 평가를 위해 잠시 후 다시 시도해주세요.'
                ],
                keywords: query.trim().split(' ').slice(0, 5),
                commercialValue: 'medium' as const
            };

            return NextResponse.json<ApiResponse<{ qualityReport: any }>>({
                success: true,
                data: {
                    qualityReport: fallbackQualityReport
                },
                message: '기본 품질 평가가 완료되었습니다.'
            }, { status: 200 });
        }

        // 오류 메시지를 안전하게 처리
        let errorMessage = '알 수 없는 오류';
        if (error instanceof Error) {
            errorMessage = error.message;
        } else if (typeof error === 'object' && error !== null) {
            errorMessage = JSON.stringify(error);
        } else if (typeof error === 'string') {
            errorMessage = error;
        }

        console.error('Quality Evaluation API Error Details:', error);

        return NextResponse.json<ApiResponse<null>>({
            success: false,
            error: `서버 오류가 발생했습니다: ${errorMessage}`
        }, { status: 500 });
    }
}

// OPTIONS 요청 처리 (CORS)
export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
    });
}

