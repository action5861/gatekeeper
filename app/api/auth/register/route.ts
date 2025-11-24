// 파일 경로: /app/api/auth/register/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

// 1. 백엔드 Pydantic 모델과 거의 동일한 Zod 스키마 정의
// AI 온보딩: websiteUrl만 필수, 나머지는 선택적 (AI가 자동 생성)
const BusinessSetupSchema = z.object({
    websiteUrl: z.string().url({ message: "올바른 URL 형식이 아닙니다." }).max(500),
    keywords: z.array(z.string().max(50, { message: "키워드는 50자를 초과할 수 없습니다." })).max(100).optional(),
    categories: z.array(z.union([z.number(), z.string()])).max(50).optional(),
    dailyBudget: z.number().int().min(1000).max(10_000_000).optional(),
    bidRange: z.object({
        min: z.number().int().min(50).max(10_000),
        max: z.number().int().min(50).max(10_000),
    }).refine(data => data.max > data.min, {
        message: "최대 입찰가는 최소 입찰가보다 커야 합니다.",
        path: ["max"], // 오류가 발생한 필드를 특정
    }).optional(),
});

// 기본 스키마 (모든 사용자 타입에 공통)
const BaseSchema = z.object({
    userType: z.enum(['advertiser', 'user']),
    email: z.string().email({ message: "올바른 이메일 형식이 아닙니다." }),
    password: z.string().min(8, { message: "비밀번호는 8자 이상이어야 합니다." }),
    username: z.string().min(1, { message: "사용자명은 필수입니다." }).max(50).optional(),
});

// 광고주용 스키마 (기본 + 광고주 필수 필드)
const AdvertiserSchema = BaseSchema.extend({
    userType: z.literal('advertiser'),
    companyName: z.string().min(1, { message: "회사명은 필수입니다." }).max(100),
    businessSetup: BusinessSetupSchema,
});

// 일반 사용자용 스키마 (기본 + 사용자 필수 필드)
const UserSchema = BaseSchema.extend({
    userType: z.literal('user'),
    username: z.string().min(1, { message: "사용자명은 필수입니다." }).max(50),
});

// 통합 스키마 (userType에 따라 조건부 검증)
const ClientSchema = z.discriminatedUnion('userType', [
    AdvertiserSchema,
    UserSchema,
]);

// 2. API 라우트 핸들러 함수
export async function POST(req: NextRequest) {
    try {
        // 클라이언트로부터 받은 데이터 유효성 검사
        const clientData = ClientSchema.parse(await req.json());

        // 3. 실제 백엔드 서버로 보낼 Payload 재구성
        // 이메일에서 @ 기호를 제거하여 username으로 변환 (백엔드 username 규칙: 영문, 숫자, 언더스코어, 한글만 허용)
        const emailUsername = clientData.email.replace('@', '_at_').replace(/[^a-zA-Z0-9_가-힣]/g, '_');

        // userType에 따라 다른 payload 구성
        let backendPayload: any;

        if (clientData.userType === 'advertiser') {
            // 광고주인 경우
            const numericCategories = clientData.businessSetup.categories?.map(c =>
                typeof c === 'string' ? parseInt(c, 10) : c
            );

            backendPayload = {
                username: emailUsername,
                email: clientData.email,
                password: clientData.password,
                company_name: clientData.companyName,
                business_setup: {
                    ...clientData.businessSetup,
                    ...(numericCategories && { categories: numericCategories }),
                },
            };
        } else {
            // 일반 사용자인 경우
            backendPayload = {
                username: clientData.username || emailUsername, // 사용자가 입력한 username 또는 이메일 기반 username
                email: clientData.email,
                password: clientData.password,
            };
        }

        // 광고주인 경우 advertiser-service로, 일반 사용자인 경우 user-service로 라우팅
        const endpoint = clientData.userType === 'advertiser'
            ? '/api/advertiser/register'
            : '/api/auth/register';

        // 실제 백엔드 API 게이트웨이로 요청 전달
        const response = await fetch(`${process.env.API_GATEWAY_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify(backendPayload),
        });

        // 4. 백엔드의 응답을 그대로 클라이언트에게 전달 (에러 메시지 보존)
        const responseData = await response.json().catch(() => ({}));
        return NextResponse.json(responseData, { status: response.status });

    } catch (error: any) {
        // Zod 유효성 검사 실패 시, 상세한 오류 메시지 반환
        if (error instanceof z.ZodError) {
            return NextResponse.json({ detail: error.flatten().fieldErrors }, { status: 422 });
        }
        // 기타 서버 오류 처리
        return NextResponse.json({ detail: "알 수 없는 서버 오류가 발생했습니다." }, { status: 500 });
    }
}