// 빠른 품질 평가 API (Legacy만 사용, ~0.1초)
// 점진적 UI를 위한 1단계 평가

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const ANALYSIS_SERVICE_URL = process.env.ANALYSIS_SERVICE_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { query } = body;

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

        console.log(`⚡ [QUICK-EVALUATE] 빠른 평가 요청: "${query}"`);

        // Analysis service의 quick 엔드포인트 호출
        const response = await fetch(`${ANALYSIS_SERVICE_URL}/evaluate-quick`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query.trim() }),
        });

        if (!response.ok) {
            throw new Error(`Analysis service error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`⚡ [QUICK-EVALUATE] 빠른 평가 완료: ${data.data?.score}점`);

        return NextResponse.json({
            success: true,
            data: {
                qualityReport: data.data,
                stage: 'quick'
            },
            message: '빠른 평가가 완료되었습니다.'
        }, { status: 200 });

    } catch (error) {
        console.error('Quick Evaluation API Error:', error);

        // Fallback: 클라이언트 사이드 간단 평가
        try {
            const body = await request.clone().json();
            const query = body.query?.trim() || '';
            
            // 간단한 점수 계산
            let score = 10;
            if (query.length >= 15) score += 40;
            else if (query.length >= 10) score += 30;
            else if (query.length >= 7) score += 20;
            else if (query.length >= 5) score += 15;
            else if (query.length >= 3) score += 10;

            const commercialValue = score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low';

            return NextResponse.json({
                success: true,
                data: {
                    qualityReport: {
                        score,
                        suggestions: ['AI 정밀 분석을 진행 중입니다...'],
                        keywords: query.split(' ').filter((w: string) => w.length >= 2),
                        commercialValue,
                    },
                    stage: 'quick'
                },
                message: '기본 평가가 완료되었습니다.'
            }, { status: 200 });
        } catch {
            return NextResponse.json<ApiResponse<null>>({
                success: false,
                error: '평가 중 오류가 발생했습니다.'
            }, { status: 500 });
        }
    }
}

// OPTIONS 요청 처리 (CORS)
export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
    });
}

