'use client'

import { ExternalLink, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

interface WebsitePreviewProps {
    url: string
    title?: string
}

export default function WebsitePreview({ url, title }: WebsitePreviewProps) {
    const [isVisible, setIsVisible] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleLoad = () => {
        setIsLoading(false)
        setError(null)
    }

    const handleError = () => {
        setIsLoading(false)
        setError('웹사이트를 불러올 수 없습니다.')
    }

    const togglePreview = () => {
        if (!isVisible) {
            setIsLoading(true)
            setError(null)
        }
        setIsVisible(!isVisible)
    }

    const openInNewTab = () => {
        window.open(url, '_blank', 'noopener,noreferrer')
    }

    const formatUrl = (url: string) => {
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            return `https://${url}`
        }
        return url
    }

    return (
        <div className="bg-slate-800/50 rounded-lg border border-slate-700">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
                <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-medium text-slate-300">
                        {title || '웹사이트 미리보기'}
                    </h3>
                    <span className="text-xs text-slate-400 truncate max-w-xs">
                        {url}
                    </span>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={openInNewTab}
                        className="p-1 text-slate-400 hover:text-slate-300 transition-colors"
                        title="새 탭에서 열기"
                    >
                        <ExternalLink className="w-4 h-4" />
                    </button>
                    <button
                        onClick={togglePreview}
                        className="p-1 text-slate-400 hover:text-slate-300 transition-colors"
                        title={isVisible ? '미리보기 숨기기' : '미리보기 보기'}
                    >
                        {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            {/* Preview Content */}
            {isVisible && (
                <div className="relative">
                    {isLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                        </div>
                    )}

                    {error ? (
                        <div className="p-8 text-center">
                            <div className="text-red-400 text-sm mb-2">
                                <EyeOff className="w-8 h-8 mx-auto mb-2" />
                                {error}
                            </div>
                            <button
                                onClick={openInNewTab}
                                className="text-blue-400 hover:text-blue-300 text-sm underline"
                            >
                                새 탭에서 열어보기
                            </button>
                        </div>
                    ) : (
                        <div className="relative w-full h-96">
                            <iframe
                                src={formatUrl(url)}
                                className="w-full h-full border-0"
                                onLoad={handleLoad}
                                onError={handleError}
                                sandbox="allow-scripts allow-same-origin allow-forms"
                                title="Website Preview"
                            />
                        </div>
                    )}
                </div>
            )}

            {/* Placeholder when not visible */}
            {!isVisible && (
                <div className="p-8 text-center">
                    <Eye className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400 text-sm">
                        미리보기를 보려면 눈 모양 버튼을 클릭하세요
                    </p>
                </div>
            )}
        </div>
    )
} 