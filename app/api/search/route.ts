// Step 2: 광고 검색 API (검색 버튼 클릭 시)
// 일일 제출 한도 차감 없음, 광고 결과만 반환

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, qualityScore } = body;

    // 사용자 인증 확인
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '인증이 필요합니다.'
      }, { status: 401 });
    }

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


    // 품질 점수 유효성 검사
    if (!qualityScore || typeof qualityScore !== 'number' || qualityScore < 0 || qualityScore > 100) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '품질 점수가 필요합니다. 먼저 검색어를 입력해주세요.'
      }, { status: 400 });
    }


    // API Gateway를 통해 광고 검색 시작
    console.log('Calling auction service via API Gateway with:', { query: query.trim(), valueScore: qualityScore });
    const auctionResponse = await fetch(`${API_GATEWAY_URL}/api/auction/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        query: query.trim(),
        valueScore: qualityScore
      }),
    });

    console.log('Auction service response status:', auctionResponse.status);
    if (!auctionResponse.ok) {
      const errorData = await auctionResponse.json();
      console.error('Auction service error response:', errorData);
      throw new Error(errorData.detail || 'Auction service error');
    }

    const auctionData = await auctionResponse.json();
    const auction = auctionData.data;

    // 성공 응답 - 광고 결과만 반환
    return NextResponse.json<ApiResponse<{ auction: any }>>({
      success: true,
      data: {
        auction
      },
      message: '광고 검색이 완료되었습니다.'
    }, { status: 200 });

  } catch (error) {
    console.error('Search API Error:', error);

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
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 