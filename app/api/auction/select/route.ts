// 사용자의 입찰 선택 처리 (프록시)

import { ApiResponse } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

const AUCTION_SERVICE_URL = process.env.AUCTION_SERVICE_URL || 'http://auction-service:8002';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { searchId, selectedBidId } = body;

    // 입력값 유효성 검사
    if (!searchId || typeof searchId !== 'string') {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '유효하지 않은 검색 ID입니다.'
      }, { status: 400 });
    }

    if (!selectedBidId || typeof selectedBidId !== 'string') {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: '선택된 입찰 ID가 유효하지 않습니다.'
      }, { status: 400 });
    }

    // Auction Service에 요청 전달
    const auctionResponse = await fetch(`${AUCTION_SERVICE_URL}/select`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ searchId, selectedBidId }),
    });

    if (!auctionResponse.ok) {
      throw new Error('Auction service error');
    }

    const auctionData = await auctionResponse.json();

    return NextResponse.json<ApiResponse<{ rewardAmount: number; searchId: string; selectedBidId: string }>>({
      success: true,
      data: auctionData.data,
      message: auctionData.message
    }, { status: 200 });

  } catch (error) {
    console.error('Auction Select API Error:', error);

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