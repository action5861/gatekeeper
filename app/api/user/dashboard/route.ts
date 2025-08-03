// 사용자 대시보드 데이터 (프록시)

import { NextRequest, NextResponse } from 'next/server';

const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8005';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')

    if (!authHeader) {
      return NextResponse.json(
        { message: 'Authorization header required' },
        { status: 401 }
      )
    }

    console.log('Forwarding dashboard request with auth:', authHeader)

    const userResponse = await fetch(`${USER_SERVICE_URL}/dashboard`, {
      headers: {
        'Authorization': authHeader,  // 🔥 JWT 토큰 전달
        'Content-Type': 'application/json',
      },
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
    console.log('Dashboard data retrieved:', userData)

    return NextResponse.json(userData);
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);

    // 🚨 임시: 에러 시 기본 데이터 반환 (개발용)
    return NextResponse.json({
      earnings: {
        total: 0,
        primary: 0,
        secondary: 0,
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

// POST 메서드는 제거 (User Service에서 직접 처리) 