// 사용자 대시보드 데이터 (수익, 품질 이력)

import { NextResponse } from 'next/server';
import { calculateDynamicLimit } from '@/lib/simulation';

// 임시 저장소 (실제로는 데이터베이스 사용)
let totalEarnings = 1500;

// 거래 내역을 가져오는 함수
async function getTransactions() {
  try {
    console.log('Fetching transactions from reward API...');
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/reward`, {
      method: 'GET',
      cache: 'no-store'
    });
    if (response.ok) {
      const data = await response.json();
      console.log('Fetched transactions:', data.transactions?.length || 0);
      return data.transactions || [];
    }
  } catch (error) {
    console.error('Failed to fetch transactions:', error);
  }
  return [];
}

export async function GET() {
  const userQualityScore = 75; // 가상 사용자 품질 점수
  const submissionLimit = calculateDynamicLimit(userQualityScore);
  
  // 거래 내역 가져오기
  const transactions = await getTransactions();
  console.log('Dashboard returning transactions:', transactions.length);

  return NextResponse.json({
    earnings: {
      total: totalEarnings,
      primary: 1200,
      secondary: 300,
    },
    qualityHistory: [
      { name: 'Week 1', score: 65 },
      { name: 'Week 2', score: 70 },
      { name: 'Week 3', score: 72 },
      { name: 'Week 4', score: userQualityScore },
    ],
    submissionLimit: submissionLimit,
    transactions: transactions,
  });
}

// 보상 누적을 위한 POST 메서드 추가
export async function POST(request: Request) {
  try {
    const { amount } = await request.json();
    
    // 총 수익에 보상 금액 추가
    totalEarnings += amount;
    
    return NextResponse.json({
      success: true,
      message: `보상 ${amount}원이 대시보드에 누적되었습니다.`,
      newTotal: totalEarnings
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      message: '보상 누적 중 오류가 발생했습니다.'
    }, { status: 500 });
  }
} 