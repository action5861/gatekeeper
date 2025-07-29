// 사용자 대시보드 데이터 (프록시)

import { NextRequest, NextResponse } from 'next/server';

const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://localhost:8005';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')

    if (!authHeader) {
      return NextResponse.json(
        { message: 'Authorization header required' },
        { status: 401 }
      )
    }

    const userResponse = await fetch(`${USER_SERVICE_URL}/dashboard`, {
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
    });

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
    return NextResponse.json(userData);
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    return NextResponse.json({
      earnings: {
        total: 1500,
        primary: 1200,
        secondary: 300,
      },
      qualityHistory: [
        { name: 'Week 1', score: 65 },
        { name: 'Week 2', score: 70 },
        { name: 'Week 3', score: 72 },
        { name: 'Week 4', score: 75 },
      ],
      submissionLimit: {
        level: 'Good',
        dailyMax: 20
      },
      transactions: [],
    });
  }
}

// 보상 누적을 위한 POST 메서드
export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const { amount } = await request.json();

    const userResponse = await fetch(`${USER_SERVICE_URL}/earnings`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ amount }),
    });

    if (!userResponse.ok) {
      throw new Error('User service error');
    }

    const userData = await userResponse.json();
    return NextResponse.json(userData);
  } catch (error) {
    return NextResponse.json({
      success: false,
      message: '보상 누적 중 오류가 발생했습니다.'
    }, { status: 500 });
  }
} 