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
                },
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.message || 'Registration failed')
            }

            const result = await response.json()

            // 회원가입 성공 후 로그인 페이지로 리다이렉트
            alert('회원가입이 완료되었습니다. 로그인해주세요.')
            router.push('/login')
        } catch (error) {
            throw error
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