import { NextRequest, NextResponse } from 'next/server';

const PAYMENT_SERVICE_URL = process.env.PAYMENT_SERVICE_URL || 'http://localhost:8003';
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://localhost:8005';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { bidId, amount, query, buyerName } = body;

    console.log('Reward API called with full body:', body);
    console.log('Reward API called with:', { bidId, amount, query, buyerName });

    // Payment Service에 요청 전달
    const paymentResponse = await fetch(`${PAYMENT_SERVICE_URL}/reward`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ bidId, amount, query, buyerName }),
    });

    if (!paymentResponse.ok) {
      throw new Error('Payment service error');
    }

    const paymentData = await paymentResponse.json();

    // 보상 지급 성공 시 User Service에 수익 업데이트 요청
    if (paymentData.success) {
      try {
        await fetch(`${USER_SERVICE_URL}/earnings`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ amount }),
        });
      } catch (error) {
        console.error('User service update failed:', error);
      }
    }

    return NextResponse.json(paymentData);
  } catch (error) {
    console.error('Reward API error:', error);
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