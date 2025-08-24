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

        // 에러 로깅 서비스에 전송 (예: Sentry, LogRocket 등)
        if (this.props.onError) {
            this.props.onError(error, errorInfo)
        }
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: undefined })
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback
            }

            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
                    <div className="max-w-md mx-auto text-center p-8">
                        <div className="w-20 h-20 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="w-10 h-10 text-white" />
                        </div>

                        <h2 className="text-2xl font-bold text-slate-100 mb-4">
                            오류가 발생했습니다
                        </h2>

                        <p className="text-slate-400 mb-6">
                            페이지를 불러오는 중 문제가 발생했습니다.
                            다시 시도해주세요.
                        </p>

                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <details className="mb-6 text-left">
                                <summary className="text-slate-300 cursor-pointer mb-2">
                                    개발자 정보 (클릭하여 확장)
                                </summary>
                                <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-4 text-sm">
                                    <p className="text-red-400 font-mono mb-2">
                                        {this.state.error.name}: {this.state.error.message}
                                    </p>
                                    <pre className="text-slate-400 text-xs overflow-auto">
                                        {this.state.error.stack}
                                    </pre>
                                </div>
                            </details>
                        )}

                        <div className="space-y-4">
                            <button
                                onClick={this.handleRetry}
                                className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl hover:from-blue-600 hover:to-cyan-600 transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-500/20 flex items-center justify-center space-x-2"
                            >
                                <RefreshCw className="w-5 h-5" />
                                <span>다시 시도</span>
                            </button>

                            <button
                                onClick={() => window.location.reload()}
                                className="w-full px-6 py-3 border-2 border-slate-600 text-slate-300 rounded-xl hover:bg-slate-700 hover:border-slate-500 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-slate-500/20"
                            >
                                페이지 새로고침
                            </button>
                        </div>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

// 함수형 컴포넌트용 에러 바운더리 훅
export function withErrorBoundary<P extends object>(
    Component: React.ComponentType<P>,
    fallback?: ReactNode,
    onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback} onError={onError}>
                <Component {...props} />
            </ErrorBoundary>
        )
    }
} 