'use client'

import { AlertCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import React from 'react'

interface ErrorFallbackProps {
    error?: string | Error | null
    componentName?: string
    onRetry?: () => void
    showRetry?: boolean
    className?: string
}

export function ErrorFallback({
    error,
    componentName = 'Component',
    onRetry,
    showRetry = true,
    className = '',
}: ErrorFallbackProps) {
    const errorMessage = error instanceof Error ? error.message : error || 'An unexpected error occurred'
    const isNetworkError = errorMessage.toLowerCase().includes('network') ||
        errorMessage.toLowerCase().includes('fetch') ||
        errorMessage.toLowerCase().includes('connection')

    return (
        <div className={`bg-slate-800/50 rounded-xl p-6 border border-slate-700 ${className}`}>
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center space-y-4 text-center">
                    {isNetworkError ? (
                        <WifiOff className="w-12 h-12 text-orange-400" />
                    ) : (
                        <AlertCircle className="w-12 h-12 text-red-400" />
                    )}

                    <div>
                        <h3 className="text-lg font-semibold text-red-400 mb-2">
                            {isNetworkError ? 'Network Error' : `${componentName} Error`}
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 max-w-md">
                            {errorMessage}
                        </p>

                        {showRetry && onRetry && (
                            <button
                                onClick={onRetry}
                                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                <span>Try Again</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

// 네트워크 에러 전용 컴포넌트
export function NetworkErrorFallback({ onRetry, className = '' }: { onRetry?: () => void; className?: string }) {
    return (
        <div className={`bg-slate-800/50 rounded-xl p-6 border border-slate-700 ${className}`}>
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center space-y-4 text-center">
                    <WifiOff className="w-12 h-12 text-orange-400" />
                    <div>
                        <h3 className="text-lg font-semibold text-orange-400 mb-2">
                            Connection Lost
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 max-w-md">
                            Please check your internet connection and try again
                        </p>
                        {onRetry && (
                            <button
                                onClick={onRetry}
                                className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
                            >
                                <Wifi className="w-4 h-4" />
                                <span>Reconnect</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

// 데이터 없음 상태 컴포넌트
export function EmptyStateFallback({
    title = 'No Data Available',
    message = 'There is no data to display at the moment',
    icon: Icon = AlertCircle,
    className = '',
}: {
    title?: string
    message?: string
    icon?: React.ComponentType<{ className?: string }>
    className?: string
}) {
    return (
        <div className={`bg-slate-800/50 rounded-xl p-6 border border-slate-700 ${className}`}>
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center space-y-4 text-center">
                    <Icon className="w-12 h-12 text-slate-400" />
                    <div>
                        <h3 className="text-lg font-semibold text-slate-300 mb-2">
                            {title}
                        </h3>
                        <p className="text-slate-400 text-sm max-w-md">
                            {message}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

// 로딩 실패 상태 컴포넌트
export function LoadingErrorFallback({
    onRetry,
    className = '',
}: {
    onRetry?: () => void
    className?: string
}) {
    return (
        <div className={`bg-slate-800/50 rounded-xl p-6 border border-slate-700 ${className}`}>
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center space-y-4 text-center">
                    <AlertCircle className="w-12 h-12 text-yellow-400" />
                    <div>
                        <h3 className="text-lg font-semibold text-yellow-400 mb-2">
                            Loading Failed
                        </h3>
                        <p className="text-slate-400 text-sm mb-4 max-w-md">
                            Failed to load data. Please try again.
                        </p>
                        {onRetry && (
                            <button
                                onClick={onRetry}
                                className="flex items-center space-x-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                <span>Reload</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
} 