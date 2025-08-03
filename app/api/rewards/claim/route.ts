import { NextResponse } from 'next/server';

const VERIFICATION_SERVICE_URL = process.env.VERIFICATION_SERVICE_URL || 'http://verification-service:8004';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const transactionId = formData.get('transactionId');
    const proofFile = formData.get('proof');

    if (!transactionId || !proofFile) {
      return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });
    }

    console.log(`2차 보상 요청 접수: ${transactionId}, 증빙 파일: ${(proofFile as File).name}`);

    // Verification Service에 요청 전달
    const verificationFormData = new FormData();
    verificationFormData.append('transactionId', transactionId as string);
    verificationFormData.append('proof', proofFile as File);

    const verificationResponse = await fetch(`${VERIFICATION_SERVICE_URL}/claim`, {
      method: 'POST',
      body: verificationFormData,
    });

    if (!verificationResponse.ok) {
      throw new Error('Verification service error');
    }

    const verificationData = await verificationResponse.json();
    return NextResponse.json(verificationData);
  } catch (error) {
    console.error('Claim API error:', error);
    return NextResponse.json({
      status: '검증 실패',
    }, { status: 500 });
  }
} 