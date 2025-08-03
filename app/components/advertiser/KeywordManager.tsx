'use client'

import { Hash, Plus, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface Keyword {
    id: number
    keyword: string
    priority: number
    match_type: 'exact' | 'phrase' | 'broad'
    status: 'active' | 'paused'
}

interface KeywordManagerProps {
    keywords: Keyword[]
    excludedKeywords: string[]
    onKeywordsChange: (keywords: Keyword[]) => void
    onExcludedKeywordsChange: (excludedKeywords: string[]) => void
    isLoading?: boolean
}

export default function KeywordManager({
    keywords,
    excludedKeywords,
    onKeywordsChange,
    onExcludedKeywordsChange,
    isLoading = false
}: KeywordManagerProps) {
    const [localKeywords, setLocalKeywords] = useState<Keyword[]>(keywords)
    const [localExcludedKeywords, setLocalExcludedKeywords] = useState<string[]>(excludedKeywords)
    const [newKeyword, setNewKeyword] = useState('')
    const [newExcludedKeyword, setNewExcludedKeyword] = useState('')
    const [editingKeyword, setEditingKeyword] = useState<Keyword | null>(null)
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        setLocalKeywords(keywords)
        setLocalExcludedKeywords(excludedKeywords)
    }, [keywords, excludedKeywords])

    const handleAddKeyword = () => {
        if (!newKeyword.trim()) return

        const keywordExists = localKeywords.some(k => k.keyword.toLowerCase() === newKeyword.toLowerCase())
        if (keywordExists) {
            alert('이미 존재하는 키워드입니다.')
            return
        }

        const newKeywordObj: Keyword = {
            id: Date.now(),
            keyword: newKeyword.trim(),
            priority: 3,
            match_type: 'broad',
            status: 'active'
        }

        setLocalKeywords([...localKeywords, newKeywordObj])
        setNewKeyword('')
    }

    const handleRemoveKeyword = (id: number) => {
        setLocalKeywords(localKeywords.filter(k => k.id !== id))
    }

    const handleUpdateKeyword = (id: number, field: keyof Keyword, value: any) => {
        setLocalKeywords(localKeywords.map(k =>
            k.id === id ? { ...k, [field]: value } : k
        ))
    }

    const handleAddExcludedKeyword = () => {
        if (!newExcludedKeyword.trim()) return

        const keywordExists = localExcludedKeywords.some(k => k.toLowerCase() === newExcludedKeyword.toLowerCase())
        if (keywordExists) {
            alert('이미 존재하는 제외 키워드입니다.')
            return
        }

        setLocalExcludedKeywords([...localExcludedKeywords, newExcludedKeyword.trim()])
        setNewExcludedKeyword('')
    }

    const handleRemoveExcludedKeyword = (keyword: string) => {
        setLocalExcludedKeywords(localExcludedKeywords.filter(k => k !== keyword))
    }

    const handleSave = async () => {
        setIsSaving(true)
        try {
            await onKeywordsChange(localKeywords)
            await onExcludedKeywordsChange(localExcludedKeywords)
        } finally {
            setIsSaving(false)
        }
    }

    const getMatchTypeColor = (matchType: string) => {
        switch (matchType) {
            case 'exact': return 'text-green-400'
            case 'phrase': return 'text-yellow-400'
            case 'broad': return 'text-blue-400'
            default: return 'text-slate-400'
        }
    }

    const getPriorityColor = (priority: number) => {
        if (priority >= 4) return 'text-red-400'
        if (priority >= 3) return 'text-yellow-400'
        return 'text-green-400'
    }

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                    <Hash className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-slate-100">키워드 관리</h3>
                    <p className="text-sm text-slate-400">자동 입찰에 사용할 키워드를 관리하세요</p>
                </div>
            </div>

            <div className="space-y-6">
                {/* 키워드 추가 */}
                <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">키워드 추가</h4>
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={newKeyword}
                            onChange={(e) => setNewKeyword(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                            placeholder="새 키워드 입력"
                            disabled={isLoading || isSaving}
                            className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                        <button
                            onClick={handleAddKeyword}
                            disabled={isLoading || isSaving || !newKeyword.trim()}
                            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* 키워드 목록 */}
                <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">
                        등록된 키워드 ({localKeywords.length}개)
                    </h4>
                    {localKeywords.length === 0 ? (
                        <div className="text-center py-8 text-slate-400">
                            <Hash className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>등록된 키워드가 없습니다</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {localKeywords.map((keyword) => (
                                <div key={keyword.id} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-slate-200 font-medium">{keyword.keyword}</span>
                                            <span className={`text-xs px-2 py-1 rounded ${getMatchTypeColor(keyword.match_type)} bg-slate-600/50`}>
                                                {keyword.match_type}
                                            </span>
                                            <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(keyword.priority)} bg-slate-600/50`}>
                                                우선순위 {keyword.priority}
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveKeyword(keyword.id)}
                                            className="text-red-400 hover:text-red-300 transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <label className="text-slate-400">매치 타입</label>
                                            <select
                                                value={keyword.match_type}
                                                onChange={(e) => handleUpdateKeyword(keyword.id, 'match_type', e.target.value)}
                                                disabled={isLoading || isSaving}
                                                className="w-full mt-1 px-2 py-1 bg-slate-600/50 border border-slate-500 rounded text-slate-200 text-xs"
                                            >
                                                <option value="broad">Broad</option>
                                                <option value="phrase">Phrase</option>
                                                <option value="exact">Exact</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-slate-400">우선순위</label>
                                            <select
                                                value={keyword.priority}
                                                onChange={(e) => handleUpdateKeyword(keyword.id, 'priority', Number(e.target.value))}
                                                disabled={isLoading || isSaving}
                                                className="w-full mt-1 px-2 py-1 bg-slate-600/50 border border-slate-500 rounded text-slate-200 text-xs"
                                            >
                                                <option value={1}>1 (낮음)</option>
                                                <option value={2}>2</option>
                                                <option value={3}>3 (보통)</option>
                                                <option value={4}>4</option>
                                                <option value={5}>5 (높음)</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 제외 키워드 */}
                <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">제외 키워드</h4>
                    <div className="flex space-x-2 mb-3">
                        <input
                            type="text"
                            value={newExcludedKeyword}
                            onChange={(e) => setNewExcludedKeyword(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAddExcludedKeyword()}
                            placeholder="제외할 키워드 입력"
                            disabled={isLoading || isSaving}
                            className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                        />
                        <button
                            onClick={handleAddExcludedKeyword}
                            disabled={isLoading || isSaving || !newExcludedKeyword.trim()}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>

                    {localExcludedKeywords.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {localExcludedKeywords.map((keyword, index) => (
                                <span
                                    key={index}
                                    className="flex items-center space-x-1 px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-full text-sm text-red-300"
                                >
                                    <span>{keyword}</span>
                                    <button
                                        onClick={() => handleRemoveExcludedKeyword(keyword)}
                                        className="text-red-400 hover:text-red-300 transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* 키워드 통계 */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">키워드 통계</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                            <p className="text-slate-400">총 키워드</p>
                            <p className="text-slate-200 font-semibold">{localKeywords.length}개</p>
                        </div>
                        <div>
                            <p className="text-slate-400">제외 키워드</p>
                            <p className="text-slate-200 font-semibold">{localExcludedKeywords.length}개</p>
                        </div>
                        <div>
                            <p className="text-slate-400">활성 키워드</p>
                            <p className="text-slate-200 font-semibold">
                                {localKeywords.filter(k => k.status === 'active').length}개
                            </p>
                        </div>
                    </div>
                </div>

                {/* 저장 버튼 */}
                <button
                    onClick={handleSave}
                    disabled={isLoading || isSaving}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSaving ? '저장 중...' : '키워드 설정 저장'}
                </button>
            </div>

            {/* 로딩 상태 */}
            {isLoading && (
                <div className="mt-4 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>
                    <span className="ml-2 text-sm text-slate-400">로딩 중...</span>
                </div>
            )}
        </div>
    )
} 