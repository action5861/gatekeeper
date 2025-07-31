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
            console.log('Attempting login with data:', { userType: data.userType, email: data.email })

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })

            const result = await response.json()

            if (!response.ok) {
                throw new Error(result.message || 'Login failed')
            }

            // Validate response
            if (!result.access_token) {
                throw new Error('No access token received from server')
            }

            // Store token in localStorage
            localStorage.setItem('token', result.access_token)
            localStorage.setItem('userType', result.userType || data.userType)

            console.log('Login successful, redirecting to:', result.userType === 'advertiser' ? '/advertiser/dashboard' : '/dashboard')

            // Redirect based on user type from backend response
            if (result.userType === 'advertiser' || data.userType === 'advertiser') {
                console.log('Redirecting advertiser to /advertiser/dashboard')
                router.push('/advertiser/dashboard')
            } else {
                console.log('Redirecting user to /dashboard')
                router.push('/dashboard')
            }
        } catch (error) {
            console.error('Login error:', error)

            // Provide user-friendly error messages
            let errorMessage = 'Login failed. Please try again.'

            if (error instanceof Error) {
                if (error.message.includes('Incorrect username or password')) {
                    errorMessage = 'Incorrect username or password. Please check your credentials.'
                } else if (error.message.includes('No access token')) {
                    errorMessage = 'Authentication failed. Please try again.'
                } else if (error.message.includes('Internal server error')) {
                    errorMessage = 'Server is temporarily unavailable. Please try again later.'
                } else {
                    errorMessage = error.message
                }
            }

            throw new Error(errorMessage)
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