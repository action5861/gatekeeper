'use client'

import AuthForm, { AuthFormData } from '@/components/AuthForm'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function RegisterPage() {
    const [isLoading, setIsLoading] = useState(false)
    const router = useRouter()

    const handleRegister = async (data: AuthFormData) => {
        setIsLoading(true)

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                // 실패 시, 응답 본문을 파싱하여 상세한 에러 메시지 생성
                let errorMessage = `Error: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    console.error('❌ Registration error response:', errorData);

                    // 백엔드에서 보낸 'detail' 정보를 추가
                    if (errorData.detail) {
                        if (typeof errorData.detail === 'object' && !Array.isArray(errorData.detail)) {
                            // Zod validation error format (flattened field errors)
                            const fieldErrors = Object.entries(errorData.detail)
                                .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
                                .join('; ');
                            errorMessage += `\nDetails: ${fieldErrors}`;
                        } else if (Array.isArray(errorData.detail)) {
                            // FastAPI validation error format
                            console.error('❌ Validation errors:', errorData.detail);
                            const validationErrors = errorData.detail.map((err: any) =>
                                `${err.loc?.join('.') || 'field'}: ${err.msg || err.message || 'validation error'}`
                            ).join(', ');
                            errorMessage += `\nDetails: ${validationErrors}`;
                        } else {
                            errorMessage += `\nDetails: ${errorData.detail}`;
                        }
                    } else if (errorData.message) {
                        errorMessage += `\nDetails: ${errorData.message}`;
                    } else if (errorData.error) {
                        errorMessage += `\nDetails: ${errorData.error}`;
                    }
                } catch (parseError) {
                    // 응답 본문이 JSON이 아닌 경우
                    console.error('Failed to parse error response:', parseError);
                    errorMessage += '\nCould not parse error response body.';
                }
                throw new Error(errorMessage);
            }

            const result = await response.json()

            // 광고주인 경우 자동 로그인 후 AI 분석 결과 확인 페이지로 이동
            if (data.userType === 'advertiser') {
                // 자동 로그인 수행
                try {
                    const loginResponse = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                        },
                        body: JSON.stringify({
                            userType: 'advertiser',
                            email: data.email,
                            password: data.password,
                        }),
                    })

                    if (loginResponse.ok) {
                        const loginResult = await loginResponse.json()
                        
                        // 토큰 저장
                        if (loginResult.access_token) {
                            localStorage.setItem('token', loginResult.access_token)
                            localStorage.setItem('userType', 'advertiser')
                            
                            // AI 분석 결과 확인 페이지로 리다이렉트
                            router.push('/advertiser/review-suggestions')
                            return
                        }
                    }
                } catch (loginError) {
                    console.error('Auto-login failed:', loginError)
                    // 자동 로그인 실패 시 기존 플로우로
                }
                
                // 자동 로그인 실패 시 기존 메시지 표시 후 로그인 페이지로
                if (result.review_message) {
                    alert(`${result.message}\n\n${result.review_message}\n\n로그인 후 AI 분석 결과를 확인하실 수 있습니다.`)
                } else {
                    alert('회원가입이 완료되었습니다. 로그인 후 AI 분석 결과를 확인하세요.')
                }
                localStorage.removeItem('selectedUserType')
                router.push('/login')
            } else {
                // 일반 사용자인 경우 기존 플로우
                alert('회원가입이 완료되었습니다. 로그인해주세요.')
                localStorage.removeItem('selectedUserType')
                router.push('/login')
            }
        } catch (error) {
            // 생성된 상세 에러 메시지를 콘솔이나 사용자 UI(토스트 메시지 등)에 표시
            console.error('Registration failed:', error instanceof Error ? error.message : 'Unknown error');
            // 사용자에게 에러 메시지 표시
            alert(error instanceof Error ? error.message : '회원가입 중 오류가 발생했습니다.');
            throw error;
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <AuthForm
                    mode="register"
                    onSubmit={handleRegister}
                    isLoading={isLoading}
                />
            </div>
        </div>
    )
} 