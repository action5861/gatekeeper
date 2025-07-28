// 2차 보상을 위한 활동 증빙 제출 및 처리

import { NextRequest, NextResponse } from 'next/server';
import { ApiResponse } from '@/lib/types';

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

    // (시뮬레이션) 처리 지연
    await new Promise(resolve => setTimeout(resolve, 2000));

    // (시뮬레이션) 70% 확률로 검증 성공, 30% 확률로 검증 실패
    const isVerificationSuccess = Math.random() < 0.7;

    if (isVerificationSuccess) {
      // 검증 성공: 2차 보상 지급
      const secondaryRewardAmount = Math.floor(Math.random() * 3000) + 500; // 500~3500원 랜덤
      
      return NextResponse.json<ApiResponse<{ 
        searchId: string; 
        secondaryRewardAmount: number; 
        verificationStatus: 'success' 
      }>>({
        success: true,
        data: {
          searchId,
          secondaryRewardAmount,
          verificationStatus: 'success'
        },
        message: '검증 성공: 2차 보상이 지급되었습니다.'
      }, { status: 200 });

    } else {
      // 검증 실패
      return NextResponse.json<ApiResponse<{ 
        searchId: string; 
        verificationStatus: 'failed';
        reason: string;
      }>>({
        success: false,
        data: {
          searchId,
          verificationStatus: 'failed',
          reason: '제출된 증빙 자료가 기준에 미달합니다.'
        },
        message: '검증 실패'
      }, { status: 400 });
    }

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