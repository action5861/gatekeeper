'use client'

import AuthForm, { AuthFormData } from '@/components/AuthForm'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function LoginPage() {
    const [isLoading, setIsLoading] = useState(false)
    const router = useRouter()

    const handleLogin = async (data: AuthFormData) => {
        setIsLoading(true)

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.message || 'Login failed')
            }

            const result = await response.json()

            // Store token in localStorage
            localStorage.setItem('token', result.access_token)
            localStorage.setItem('userType', data.userType)

            // Redirect based on user type
            if (data.userType === 'advertiser') {
                router.push('/advertiser/dashboard')
            } else {
                router.push('/dashboard')
            }
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
                    mode="login"
                    onSubmit={handleLogin}
                    isLoading={isLoading}
                />
            </div>
        </div>
    )
} 