// 검색어 수신, 가치 평가 및 역경매 개시 (프록시)

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const ANALYSIS_SERVICE_URL = process.env.ANALYSIS_SERVICE_URL || 'http://analysis-service:8001';
const AUCTION_SERVICE_URL = process.env.AUCTION_SERVICE_URL || 'http://auction-service:8002';
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8005';

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

    // 1단계: Analysis Service에서 데이터 가치 평가
    const analysisResponse = await fetch(`${ANALYSIS_SERVICE_URL}/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: query.trim() }),
    });

    if (!analysisResponse.ok) {
      throw new Error('Analysis service error');
    }

    const analysisData = await analysisResponse.json();
    const qualityReport = analysisData.data;

    // 2단계: Auction Service에서 역경매 시작
    console.log('Calling auction service with:', { query: query.trim(), valueScore: qualityReport.score });
    const auctionResponse = await fetch(`${AUCTION_SERVICE_URL}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader, // 사용자 정보 전달
      },
      body: JSON.stringify({
        query: query.trim(),
        valueScore: qualityReport.score
      }),
    });

    console.log('Auction service response status:', auctionResponse.status);
    if (!auctionResponse.ok) {
      const errorText = await auctionResponse.text();
      console.error('Auction service error response:', errorText);
      throw new Error('Auction service error');
    }

    const auctionData = await auctionResponse.json();
    const auction = auctionData.data;

    // 3단계: User Service에 검색 데이터 저장 및 통계 업데이트
    try {
      const userServiceResponse = await fetch(`${USER_SERVICE_URL}/search-completed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
        body: JSON.stringify({
          query: query.trim(),
          quality_score: qualityReport.score,
          commercial_value: qualityReport.commercialValue,
          keywords: qualityReport.keywords,
          suggestions: qualityReport.suggestions,
          auction_id: auction.searchId
        }),
      });

      if (userServiceResponse.ok) {
        console.log('✅ Search data saved to user service');
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