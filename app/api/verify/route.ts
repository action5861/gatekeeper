// 2차 보상을 위한 활동 증빙 제출 및 처리 (프록시)

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const VERIFICATION_SERVICE_URL = process.env.VERIFICATION_SERVICE_URL || 'http://verification-service:8004';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { searchId, proof } = body;

    // 입력값 유효성 검사
    if (!searchId || typeof searchId !== 'string') {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '유효하지 않은 검색 ID입니다.'
      }, { status: 400 });
    }

    if (!proof) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '증빙 자료를 제출해주세요.'
      }, { status: 400 });
    }

    // Verification Service에 요청 전달
    const verificationResponse = await fetch(`${VERIFICATION_SERVICE_URL}/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ searchId, proof }),
    });

    if (!verificationResponse.ok) {
      throw new Error('Verification service error');
    }

    const verificationData = await verificationResponse.json();

    return NextResponse.json<ApiResponse<any>>({
      success: verificationData.success,
      data: verificationData.data,
      message: verificationData.message
    }, { status: verificationData.success ? 200 : 400 });

  } catch (error) {
    console.error('Verify API Error:', error);

    return NextResponse.json<ApiResponse<null>>({
      success: false,
      error: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
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
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
} 