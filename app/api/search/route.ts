// 검색어 수신, 가치 평가 및 역경매 개시

import { NextRequest, NextResponse } from 'next/server';
import { evaluateDataValue, startReverseAuction } from '@/lib/simulation';
import { Auction, QualityReport, ApiResponse } from '@/lib/types';

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

    // 1단계: 데이터 가치 평가
    const qualityReport: QualityReport = evaluateDataValue(query);

    // 2단계: 역경매 시작
    const bids = startReverseAuction(query, qualityReport.score);

    // 3단계: 경매 정보 생성
    const searchId = `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 30 * 60 * 1000); // 30분 후 만료

    const auction: Auction = {
      searchId,
      query: query.trim(),
      bids,
      status: 'active',
      createdAt: now,
      expiresAt
    };

    // 성공 응답
    return NextResponse.json<ApiResponse<{ auction: Auction; qualityReport: QualityReport }>>({
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