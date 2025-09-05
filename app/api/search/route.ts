// 검색어 수신, 가치 평가 및 역경매 개시 (API Gateway를 통한 프록시)

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;

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

    // API Gateway를 통해 검색 처리
    const gatewayResponse = await fetch(`${API_GATEWAY_URL}/api/analysis/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({ query: query.trim() }),
    });

    if (!gatewayResponse.ok) {
      const errorData = await gatewayResponse.json();
      throw new Error(errorData.detail || 'Analysis service error');
    }

    const analysisData = await gatewayResponse.json();
    const qualityReport = analysisData.data;

    // API Gateway를 통해 경매 시작
    console.log('Calling auction service via API Gateway with:', { query: query.trim(), valueScore: qualityReport.score });
    const auctionResponse = await fetch(`${API_GATEWAY_URL}/api/auction/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        query: query.trim(),
        valueScore: qualityReport.score
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

    // API Gateway를 통해 사용자 서비스에 검색 데이터 저장
    try {
      const userServiceResponse = await fetch(`${API_GATEWAY_URL}/api/user/update-daily-submission`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
        body: JSON.stringify({
          quality_score: qualityReport.score
        }),
      });

      if (userServiceResponse.ok) {
        console.log('✅ Search data saved to user service via API Gateway');
      } else {
        console.warn('⚠️ Failed to save search data to user service');
      }
    } catch (error) {
      console.warn('⚠️ User service error (non-critical):', error);
    }

    // 성공 응답
    return NextResponse.json<ApiResponse<{ auction: any; qualityReport: any }>>({
      success: true,
      data: {
        auction,
        qualityReport
      },
      message: '역경매가 성공적으로 시작되었습니다.'
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