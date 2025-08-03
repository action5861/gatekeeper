// 일일 제출 현황 업데이트 (프록시)

import { NextRequest, NextResponse } from 'next/server';

const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8005';

export async function POST(request: NextRequest) {
    try {
        const authHeader = request.headers.get('authorization')

        if (!authHeader) {
            return NextResponse.json(
                { message: 'Authorization header required' },
                { status: 401 }
            )
        }

        const body = await request.json()
        const { quality_score } = body

        if (!quality_score) {
            return NextResponse.json(
                { message: 'Quality score is required' },
                { status: 400 }
            )
        }

        console.log('Forwarding submission update request:', { quality_score })

        const userResponse = await fetch(`${USER_SERVICE_URL}/submission`, {
            method: 'POST',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ quality_score }),
        });

        console.log('User service response status:', userResponse.status)

        if (!userResponse.ok) {
            if (userResponse.status === 401) {
                return NextResponse.json(
                    { message: 'Unauthorized' },
                    { status: 401 }
                )
            }
            throw new Error('User service error');
        }

        const userData = await userResponse.json();
        console.log('Submission updated:', userData)

        return NextResponse.json(userData);
    } catch (error) {
        console.error('Failed to update submission:', error);
        return NextResponse.json(
            { message: 'Failed to update submission' },
            { status: 500 }
        );
    }
} 