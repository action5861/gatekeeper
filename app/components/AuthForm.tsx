'use client'

import { Building2, Eye, EyeOff, Lock, Mail, User } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import BusinessSetup, { BusinessSetupData } from './advertiser/BusinessSetup'

interface AuthFormProps {
    mode: 'login' | 'register'
    onSubmit: (data: AuthFormData) => Promise<void>
    isLoading?: boolean
}

export interface AuthFormData {
    userType: 'user' | 'advertiser'
    email: string
    password: string
    username?: string
    companyName?: string
    businessSetup?: BusinessSetupData
}

export default function AuthForm({ mode, onSubmit, isLoading = false }: AuthFormProps) {
    const [userType, setUserType] = useState<'user' | 'advertiser'>('user')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [username, setUsername] = useState('')
    const [companyName, setCompanyName] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [showBusinessSetup, setShowBusinessSetup] = useState(false)
    const [businessSetupData, setBusinessSetupData] = useState<BusinessSetupData | null>(null)

    // Check for pre-selected user type from header or URL params
    useEffect(() => {
        if (typeof window !== 'undefined') {
            // First check URL params
            const urlParams = new URLSearchParams(window.location.search)
            const typeFromUrl = urlParams.get('type')

            if (typeFromUrl === 'user' || typeFromUrl === 'advertiser') {
                console.log('AuthForm: Setting userType from URL param:', typeFromUrl)
                setUserType(typeFromUrl)
                // Clear the URL param
                const newUrl = window.location.pathname
                window.history.replaceState({}, '', newUrl)
                return
            }

            // Fallback to localStorage
            const selectedUserType = localStorage.getItem('selectedUserType')
            console.log('AuthForm: Checking for selectedUserType:', selectedUserType)
            if (selectedUserType === 'user' || selectedUserType === 'advertiser') {
                console.log('AuthForm: Setting userType to:', selectedUserType)
                setUserType(selectedUserType)
                // Clear the stored selection after using it
                localStorage.removeItem('selectedUserType')
            }
        }
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        // Validate form data
        if (!email.trim() || !password.trim()) {
            setError('Please fill in all required fields')
            return
        }

        if (mode === 'register') {
            if (userType === 'user' && !username.trim()) {
                setError('Username is required for user registration')
                return
            }
            if (userType === 'advertiser' && !companyName.trim()) {
                setError('Company name is required for advertiser registration')
                return
            }
        }

        // For advertiser registration, show business setup first
        if (mode === 'register' && userType === 'advertiser') {
            setShowBusinessSetup(true)
            return
        }

        try {
            const formData: AuthFormData = {
                userType,
                email: email.trim(),
                password,
                ...(mode === 'register' && userType === 'user' && { username: username.trim() }),
                ...(mode === 'register' && userType === 'advertiser' && { companyName: companyName.trim() })
            }

            console.log('Submitting form data:', { userType: formData.userType, email: formData.email, mode })

            await onSubmit(formData)
        } catch (err) {
            console.error('Form submission error:', err)
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }

    const handleBusinessSetupComplete = async (data: BusinessSetupData) => {
        setBusinessSetupData(data)
        setShowBusinessSetup(false)

        try {
            const formData: AuthFormData = {
                userType,
                email: email.trim(),
                password,
                companyName: companyName.trim(),
                businessSetup: data
            }

            console.log('Submitting advertiser form data with business setup:', formData)

            await onSubmit(formData)
        } catch (err) {
            console.error('Form submission error:', err)
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }

    const handleBusinessSetupBack = () => {
        setShowBusinessSetup(false)
        setBusinessSetupData(null)
    }

    // Show business setup if needed
    if (showBusinessSetup) {
        return (
            <BusinessSetup
                onComplete={handleBusinessSetupComplete}
                onBack={handleBusinessSetupBack}
                isLoading={isLoading}
            />
        )
    }

    return (
        <div className="w-full max-w-md mx-auto">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8 shadow-2xl">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-green-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <Building2 className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-100 mb-2">
                        {mode === 'login' ? 'Welcome Back' : 'Create Account'}
                    </h1>
                    <p className="text-slate-400">
                        {mode === 'login'
                            ? 'Sign in to your account to continue'
                            : 'Join DigiSafe to get started'
                        }
                    </p>
                </div>

                {/* User Type Tabs */}
                <div className="flex bg-slate-700/50 rounded-lg p-1 mb-6">
                    <button
                        type="button"
                        onClick={() => {
                            setUserType('user')
                            setEmail('')
                            setPassword('')
                            setError('') // Clear any previous errors
                        }}
                        disabled={isLoading}
                        className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md transition-all duration-200 ${userType === 'user'
                            ? 'bg-blue-600 text-white shadow-lg'
                            : 'text-slate-300 hover:text-white hover:bg-slate-600'
                            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <User className="w-4 h-4" />
                        <span className="font-medium">User</span>
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            setUserType('advertiser')
                            setEmail('')
                            setPassword('')
                            setError('') // Clear any previous errors
                        }}
                        disabled={isLoading}
                        className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md transition-all duration-200 ${userType === 'advertiser'
                            ? 'bg-green-600 text-white shadow-lg'
                            : 'text-slate-300 hover:text-white hover:bg-slate-600'
                            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <Building2 className="w-4 h-4" />
                        <span className="font-medium">Advertiser</span>
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Username field for user registration only */}
                    {mode === 'register' && userType === 'user' && (
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                                Username
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    id="username"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                                    placeholder="Enter your username"
                                />
                            </div>
                        </div>
                    )}

                    {/* Company Name field for advertiser registration */}
                    {mode === 'register' && userType === 'advertiser' && (
                        <div>
                            <label htmlFor="companyName" className="block text-sm font-medium text-slate-300 mb-2">
                                Company Name
                            </label>
                            <div className="relative">
                                <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    id="companyName"
                                    type="text"
                                    value={companyName}
                                    onChange={(e) => setCompanyName(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                                    placeholder="Enter your company name"
                                />
                            </div>
                        </div>
                    )}

                    {/* Email/Username field */}
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                            {mode === 'login' && userType === 'advertiser' ? 'Username' : 'Email'}
                        </label>
                        <div className="relative">
                            {mode === 'login' && userType === 'advertiser' ? (
                                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                            ) : (
                                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                            )}
                            <input
                                id="email"
                                type={mode === 'login' && userType === 'advertiser' ? 'text' : 'email'}
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full pl-10 pr-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                                placeholder={mode === 'login' && userType === 'advertiser' ? 'Enter your username' : 'Enter your email'}
                            />
                        </div>
                    </div>

                    {/* Password field */}
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                            Password
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full pl-10 pr-12 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                                placeholder="Enter your password"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-300 transition-colors duration-200"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Submit button */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    >
                        {isLoading ? (
                            <div className="flex items-center justify-center space-x-2">
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                <span>Processing...</span>
                            </div>
                        ) : (
                            mode === 'login' ? 'Sign In' : 'Create Account'
                        )}
                    </button>
                </form>

                {/* Footer */}
                <div className="mt-8 text-center">
                    <p className="text-slate-400">
                        {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
                        <Link
                            href={mode === 'login' ? `/register?type=${userType}` : '/login'}
                            className="text-blue-400 hover:text-blue-300 font-medium transition-colors duration-200"
                        >
                            {mode === 'login' ? 'Sign up' : 'Sign in'}
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    )
} 