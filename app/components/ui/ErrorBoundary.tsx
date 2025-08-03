'use client'

import { AlertCircle, RefreshCw } from 'lucide-react'
import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
    children: ReactNode
    fallback?: ReactNode
    onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
    hasError: boolean
    error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = { hasError: false }
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo)

        // 에러 모니터링 로그
        this.logError(error, errorInfo)

        // 부모 컴포넌트에 에러 전달
        this.props.onError?.(error, errorInfo)
    }

    private logError = (error: Error, errorInfo: ErrorInfo) => {
        // 에러 로깅 로직
        const errorLog = {
            message: error.message,
            stack: error.stack,
            componentStack: errorInfo.componentStack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
        }

        // 실제 프로덕션에서는 에러 모니터링 서비스로 전송
        console.error('Error Log:', errorLog)

        // 로컬 스토리지에 에러 히스토리 저장 (최대 10개)
        try {
            const errorHistory = JSON.parse(localStorage.getItem('errorHistory') || '[]')
            errorHistory.unshift(errorLog)
            if (errorHistory.length > 10) {
                errorHistory.pop()
            }
            localStorage.setItem('errorHistory', JSON.stringify(errorHistory))
        } catch (e) {
            console.error('Failed to save error to localStorage:', e)
        }
    }

    private handleRetry = () => {
        this.setState({ hasError: false, error: undefined })
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback
            }

            return (
                <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center justify-center h-64">
                        <div className="flex flex-col items-center space-y-4 text-center">
                            <AlertCircle className="w-12 h-12 text-red-400" />
                            <div>
                                <h3 className="text-lg font-semibold text-red-400 mb-2">
                                    Something went wrong
                                </h3>
                                <p className="text-slate-400 text-sm mb-4 max-w-md">
                                    {this.state.error?.message || 'An unexpected error occurred'}
                                </p>
                                <button
                                    onClick={this.handleRetry}
                                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    <span>Try Again</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

// 함수형 컴포넌트용 에러 처리 훅
export function useErrorHandler() {
    const [error, setError] = React.useState<Error | null>(null)

    const handleError = React.useCallback((error: Error) => {
        console.error('Error caught by useErrorHandler:', error)
        setError(error)

        // 에러 로깅
        const errorLog = {
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
        }

        console.error('Error Log:', errorLog)
    }, [])

    const clearError = React.useCallback(() => {
        setError(null)
    }, [])

    return { error, handleError, clearError }
} 