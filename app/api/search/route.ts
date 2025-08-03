// 검색어 수신, 가치 평가 및 역경매 개시 (프록시)

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const ANALYSIS_SERVICE_URL = process.env.ANALYSIS_SERVICE_URL || 'http://analysis-service:8001';
const AUCTION_SERVICE_URL = process.env.AUCTION_SERVICE_URL || 'http://auction-service:8002';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;

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
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
} 