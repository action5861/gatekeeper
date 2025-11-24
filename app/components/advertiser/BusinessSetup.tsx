'use client'

import { AlertCircle, Globe, Sparkles } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ErrorBoundary } from '../ui/ErrorBoundary'

interface BusinessSetupProps {
    onComplete: (data: BusinessSetupData) => void
    onBack: () => void
    isLoading?: boolean
}

export interface BusinessSetupData {
    websiteUrl: string
}

function BusinessSetup({ onComplete, onBack, isLoading = false }: BusinessSetupProps) {
    const [websiteUrl, setWebsiteUrl] = useState('')
    const [error, setError] = useState('')
    const router = useRouter()

    const isValidUrl = (url: string): boolean => {
        if (!url.trim()) return false
        try {
            const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`)
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
        } catch {
            return false
        }
    }

    const handleSubmit = () => {
        setError('')

        if (!websiteUrl.trim() || !isValidUrl(websiteUrl)) {
            setError('올바른 웹사이트 URL을 입력하세요')
            return
        }

        onComplete({ websiteUrl: websiteUrl.trim() })
    }

    return (
        <div className="business-setup min-h-screen w-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100">
            <div className="max-w-2xl w-full mx-auto px-4 py-12">
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-blue-500 to-green-500 mb-4">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
                        AI 기반 광고 설정
                    </h1>
                    <p className="text-xl text-slate-300">
                        웹사이트 URL만 입력하면 AI가 최적의 광고 설정을 자동으로 생성합니다
                    </p>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 mb-8">
                    <div className="mb-6">
                        <label className="flex items-center gap-2 text-lg font-semibold mb-3">
                            <Globe className="w-5 h-5 text-blue-400" />
                            웹사이트 URL
                        </label>
                        <input
                            type="url"
                            value={websiteUrl}
                            onChange={(e) => {
                                setWebsiteUrl(e.target.value)
                                setError('')
                            }}
                            placeholder="https://example.com"
                            className={`w-full px-5 py-4 rounded-xl bg-slate-900/60 border ${error ? 'border-red-500' : 'border-slate-600'
                                } text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all`}
                            aria-invalid={!!error}
                            aria-describedby={error ? 'url-error' : undefined}
                        />
                        {error && (
                            <p id="url-error" className="mt-2 text-sm text-red-400 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4" />
                                {error}
                            </p>
                        )}
                    </div>

                    <div className="bg-blue-900/20 border border-blue-700/30 rounded-xl p-6">
                        <h3 className="font-semibold text-blue-300 mb-3 flex items-center gap-2">
                            <Sparkles className="w-5 h-5" />
                            AI가 자동으로 생성하는 항목
                        </h3>
                        <ul className="space-y-2 text-slate-300">
                            <li className="flex items-start gap-2">
                                <span className="text-green-400 mt-1">✓</span>
                                <span>최적화된 광고 키워드 (최대 20개)</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-green-400 mt-1">✓</span>
                                <span>비즈니스에 적합한 카테고리</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-green-400 mt-1">✓</span>
                                <span>비즈니스 요약 및 분석</span>
                            </li>
                        </ul>
                        <p className="mt-4 text-sm text-slate-400">
                            💡 분석 완료 후 결과를 확인하고 수정할 수 있습니다
                        </p>
                    </div>
                </div>

                <div className="flex gap-4 justify-center">
                    <button
                        type="button"
                        onClick={onBack}
                        disabled={isLoading}
                        className="px-8 py-4 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition-all font-semibold"
                    >
                        이전
                    </button>
                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={isLoading || !websiteUrl.trim()}
                        className="px-10 py-4 rounded-xl bg-gradient-to-r from-blue-500 to-green-500 text-white font-bold text-lg disabled:opacity-50 hover:shadow-lg hover:shadow-blue-500/50 transition-all disabled:hover:shadow-none"
                    >
                        {isLoading ? (
                            <span className="flex items-center gap-2">
                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                처리 중...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <Sparkles className="w-5 h-5" />
                                AI 분석 시작하기
                            </span>
                        )}
                    </button>
                </div>

                <p className="text-center text-sm text-slate-500 mt-8">
                    분석은 약 30-60초가 소요되며, 완료 후 대시보드에서 결과를 확인할 수 있습니다
                </p>
            </div>
        </div>
    )
}

// 에러 바운더리로 감싼 컴포넌트 내보내기
export default function BusinessSetupWithErrorBoundary(props: BusinessSetupProps) {
    return (
        <ErrorBoundary
            onError={(error, errorInfo) => {
                console.error('BusinessSetup 에러:', error, errorInfo)
            }}
        >
            <BusinessSetup {...props} />
        </ErrorBoundary>
    )
}
