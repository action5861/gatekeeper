import { NextRequest, NextResponse } from 'next/server';

const PAYMENT_SERVICE_URL = process.env.PAYMENT_SERVICE_URL || 'http://payment-service:8003';
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8005';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return NextResponse.json({
        success: false,
        message: 'Authorization required'
      }, { status: 401 });
    }

    const body = await request.json();
    const { bidId, amount, query, buyerName } = body;

    console.log('🎯 Reward API called with JWT for user');

    // Payment Service에 JWT와 함께 요청 전달
    const paymentResponse = await fetch(`${PAYMENT_SERVICE_URL}/reward`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,  // 🔥 JWT 토큰 전달
      },
      body: JSON.stringify({ bidId, amount, query, buyerName }),
    });

    if (!paymentResponse.ok) {
      throw new Error('Payment service error');
    }

    const paymentData = await paymentResponse.json();
    return NextResponse.json(paymentData);
  } catch (error) {
    console.error('💥 Reward API error:', error);
    return NextResponse.json({
      success: false,
      message: '서버 오류가 발생했습니다.',
      error: 'SERVER_ERROR'
    }, { status: 500 });
  }
}

// 거래 내역 조회 API
export async function GET() {
  try {
    const paymentResponse = await fetch(`${PAYMENT_SERVICE_URL}/transactions`);

    if (!paymentResponse.ok) {
      throw new Error('Payment service error');
    }

    const paymentData = await paymentResponse.json();
    console.log('GET transactions called, count:', paymentData.transactions?.length || 0);

    return NextResponse.json(paymentData);
  } catch (error) {
    console.error('Failed to fetch transactions:', error);
    return NextResponse.json({
      success: true,
      transactions: []
    });
  }
} 