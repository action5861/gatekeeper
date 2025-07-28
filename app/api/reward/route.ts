import { NextRequest, NextResponse } from 'next/server';
import { mockTransactions } from '@/lib/simulation';

// 전역 거래 내역 저장소 (실제로는 데이터베이스 사용)
let transactions = [
  {
    id: 'txn_1001',
    query: '아이폰16',
    buyerName: '쿠팡',
    primaryReward: 175,
    status: '1차 완료' as const,
    timestamp: '2025-07-20T09:10:00Z',
  },
  {
    id: 'txn_1002',
    query: '제주도 항공권',
    buyerName: '네이버',
    primaryReward: 250,
    status: '2차 완료' as const,
    secondaryReward: 1250,
    timestamp: '2025-07-19T14:30:00Z',
  },
  {
    id: 'txn_1003',
    query: '나이키 운동화',
    buyerName: 'Google',
    primaryReward: 90,
    status: '검증 실패' as const,
    timestamp: '2025-07-18T18:00:00Z',
  },
];

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { bidId, amount, query, buyerName } = body;

    console.log('Reward API called with full body:', body);
    console.log('Reward API called with:', { bidId, amount, query, buyerName });

    // 실제 환경에서는 여기서 결제 처리나 보상 지급 로직을 구현
    // 현재는 시뮬레이션으로 즉시 성공 응답
    
    // 보상 지급 시뮬레이션 (90% 성공률)
    const isSuccess = Math.random() > 0.1;
    
    if (isSuccess) {
      // 새로운 거래 내역 생성
      const newTransaction = {
        id: `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        query: query || 'Unknown Search',
        buyerName: buyerName || 'Unknown Buyer',
        primaryReward: amount,
        status: '1차 완료' as const,
        timestamp: new Date().toISOString(),
      };

      console.log('Creating new transaction:', newTransaction);

      // 거래 내역에 추가
      transactions.unshift(newTransaction); // 최신 거래를 맨 위에 추가

      console.log('Updated transactions count:', transactions.length);

      // 대시보드에 보상 누적
      try {
        await fetch(`${request.nextUrl.origin}/api/user/dashboard`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ amount }),
        });
      } catch (error) {
        console.error('Dashboard update failed:', error);
      }

      return NextResponse.json({
        success: true,
        message: `즉시 보상 ${amount}원이 지급되었습니다!`,
        amount: amount,
        transactionId: newTransaction.id,
        transaction: newTransaction
      });
    } else {
      return NextResponse.json({
        success: false,
        message: '보상 지급 중 오류가 발생했습니다. 다시 시도해주세요.',
        error: 'PAYMENT_ERROR'
      }, { status: 400 });
    }
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
  console.log('GET transactions called, count:', transactions.length);
  return NextResponse.json({
    success: true,
    transactions: transactions
  });
} 