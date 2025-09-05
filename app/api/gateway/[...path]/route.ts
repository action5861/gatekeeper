// API Gateway 프록시 라우트
// 모든 API 요청을 API Gateway로 전달

import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: { path: string[] } }
) {
    return proxyRequest(request, params.path, 'GET');
}

export async function POST(
    request: NextRequest,
    { params }: { params: { path: string[] } }
) {
    return proxyRequest(request, params.path, 'POST');
}

export async function PUT(
    request: NextRequest,
    { params }: { params: { path: string[] } }
) {
    return proxyRequest(request, params.path, 'PUT');
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: { path: string[] } }
) {
    return proxyRequest(request, params.path, 'DELETE');
}

async function proxyRequest(
    request: NextRequest,
    pathSegments: string[],
    method: string
) {
    try {
        const path = '/' + pathSegments.join('/');
        const url = new URL(path, API_GATEWAY_URL);

        // 쿼리 파라미터 전달
        request.nextUrl.searchParams.forEach((value, key) => {
            url.searchParams.set(key, value);
        });

        // 요청 헤더 복사 (중요한 헤더들만)
        const headers: Record<string, string> = {};
        const importantHeaders = [
            'authorization',
            'content-type',
            'accept',
            'user-agent',
            'x-request-id'
        ];

        importantHeaders.forEach(header => {
            const value = request.headers.get(header);
            if (value) {
                headers[header] = value;
            }
        });

        // 요청 본문 처리
        let body: string | undefined;
        if (method !== 'GET' && method !== 'HEAD') {
            try {
                body = await request.text();
            } catch (error) {
                console.warn('Failed to read request body:', error);
            }
        }

        // API Gateway로 요청 전달
        const response = await fetch(url.toString(), {
            method,
            headers,
            body,
        });

        // 응답 헤더 복사
        const responseHeaders = new Headers();
        response.headers.forEach((value, key) => {
            responseHeaders.set(key, value);
        });

        // 응답 본문 처리
        const responseBody = await response.text();
        let jsonBody;
        try {
            jsonBody = JSON.parse(responseBody);
        } catch {
            jsonBody = responseBody;
        }

        return NextResponse.json(jsonBody, {
            status: response.status,
            headers: responseHeaders,
        });

    } catch (error) {
        console.error('API Gateway proxy error:', error);
        return NextResponse.json(
            {
                success: false,
                error: 'API Gateway 연결 오류가 발생했습니다.'
            },
            { status: 503 }
        );
    }
}
