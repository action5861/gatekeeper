// 품질 점수 업데이트 (프록시)

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
        const { score, week_label } = body

        if (!score || !week_label) {
            return NextResponse.json(
                { message: 'Score and week_label are required' },
                { status: 400 }
            )
        }

        console.log('Forwarding quality score update request:', { score, week_label })

        const userResponse = await fetch(`${USER_SERVICE_URL}/quality-score`, {
            method: 'POST',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ score, week_label }),
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
        console.log('Quality score updated:', userData)

        return NextResponse.json(userData);
    } catch (error) {
        console.error('Failed to update quality score:', error);
        return NextResponse.json(
            { message: 'Failed to update quality score' },
            { status: 500 }
        );
    }
} 