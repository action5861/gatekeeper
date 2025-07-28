import { NextResponse } from 'next/server';

// OCR 및 외부 API 연동을 통한 검증 과정을 시뮬레이션합니다.
const simulateVerification = (): Promise<{ success: boolean; reward: number }> => {
  return new Promise(resolve => {
    setTimeout(() => {
      const isSuccess = Math.random() > 0.3; // 70% 성공 확률
      resolve({
        success: isSuccess,
        reward: isSuccess ? Math.floor(Math.random() * 500 + 500) : 0, // 500-1000원 사이의 2차 보상
      });
    }, 2000); // 2초의 처리 시간 흉내
  });
};

export async function POST(request: Request) {
  const formData = await request.formData();
  const transactionId = formData.get('transactionId');
  const proofFile = formData.get('proof');

  if (!transactionId || !proofFile) {
    return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });
  }

  console.log(`2차 보상 요청 접수: ${transactionId}, 증빙 파일: ${(proofFile as File).name}`);

  const verificationResult = await simulateVerification();

  if (verificationResult.success) {
    return NextResponse.json({
      status: '2차 완료',
      secondaryReward: verificationResult.reward,
    });
  } else {
    return NextResponse.json({
      status: '검증 실패',
    });
  }
} 