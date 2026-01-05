'use client'

import { authenticatedFetch } from '@/lib/auth'
import { Plus, Sparkles, Tag, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface Keyword {
    id: number
    keyword: string
    priority: number
    match_type: string
    created_at?: string
}

interface Category {
    id: number
    category_path: string
    category_level: number
    is_primary: boolean
    created_at?: string
}

interface KeywordsCategoriesManagerProps {
    advertiserId?: number
}

export default function KeywordsCategoriesManager({ advertiserId: propAdvertiserId }: KeywordsCategoriesManagerProps) {
    const [keywords, setKeywords] = useState<Keyword[]>([])
    const [categories, setCategories] = useState<Category[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [newKeyword, setNewKeyword] = useState('')
    const [isSaving, setIsSaving] = useState(false)
    const [currentAdvertiserId, setCurrentAdvertiserId] = useState<number | null>(propAdvertiserId || null)

    useEffect(() => {
        fetchData()
    }, [propAdvertiserId])

    const fetchData = async () => {
        if (!propAdvertiserId) {
            // advertiserId가 없으면 /me에서 가져오기
            try {
                const meResponse = await authenticatedFetch('/api/advertiser/me')
                if (meResponse.ok) {
                    const meData = await meResponse.json()
                    if (meData.id) {
                        setCurrentAdvertiserId(meData.id)
                        await fetchKeywordsAndCategories(meData.id)
                    }
                }
            } catch (error) {
                console.error('Failed to fetch advertiser ID:', error)
            }
            setIsLoading(false)
            return
        }

        setCurrentAdvertiserId(propAdvertiserId)
        await fetchKeywordsAndCategories(propAdvertiserId)
        setIsLoading(false)
    }

    const fetchKeywordsAndCategories = async (id: number) => {
        try {
            // 키워드 조회
            const keywordsResponse = await authenticatedFetch(`/api/advertiser/keywords/${id}`)
            if (keywordsResponse.ok) {
                const keywordsData = await keywordsResponse.json()
                setKeywords(keywordsData)
            }

            // 카테고리 조회
            const categoriesResponse = await authenticatedFetch(`/api/advertiser/categories/${id}`)
            if (categoriesResponse.ok) {
                const categoriesData = await categoriesResponse.json()
                setCategories(categoriesData)
            }
        } catch (error) {
            console.error('Failed to fetch keywords/categories:', error)
        }
    }

    const handleAddKeyword = async () => {
        const trimmed = newKeyword.trim()
        if (!trimmed) return

        // 중복 확인
        if (keywords.some(k => k.keyword.toLowerCase() === trimmed.toLowerCase())) {
            alert('이미 추가된 키워드입니다')
            return
        }

        // 임시로 UI에 추가 (실제 저장은 사용자가 명시적으로 요청할 때)
        const tempKeyword: Keyword = {
            id: Date.now(),
            keyword: trimmed,
            priority: 1,
            match_type: 'broad',
        }

        setKeywords([...keywords, tempKeyword])
        setNewKeyword('')
    }

    const handleRemoveKeyword = (id: number) => {
        setKeywords(keywords.filter(k => k.id !== id))
    }

    const handleSave = async () => {
        if (!currentAdvertiserId) {
            alert('광고주 정보를 불러오는 중입니다. 잠시 후 다시 시도해주세요.')
            return
        }

        setIsSaving(true)
        try {
            const response = await authenticatedFetch(`/api/advertiser/keywords/${currentAdvertiserId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(keywords),
            })

            if (response.ok) {
                alert('키워드가 저장되었습니다')
                await fetchKeywordsAndCategories(currentAdvertiserId)
            } else {
                alert('저장에 실패했습니다')
            }
        } catch (error) {
            console.error('Failed to save keywords:', error)
            alert('저장 중 오류가 발생했습니다')
        } finally {
            setIsSaving(false)
        }
    }

    if (isLoading) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* 키워드 관리 */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-semibold text-slate-100 flex items-center gap-2">
                        <Tag className="w-6 h-6 text-blue-400" />
                        광고 키워드
                    </h2>
                    {keywords.length > 0 && (
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                        >
                            {isSaving ? '저장 중...' : '저장'}
                        </button>
                    )}
                </div>

                {/* 키워드 목록 */}
                <div className="flex flex-wrap gap-2 mb-4 min-h-[60px]">
                    {keywords.length > 0 ? (
                        keywords.map((kw) => (
                            <span
                                key={kw.id}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/30"
                            >
                                {kw.keyword}
                                <button
                                    onClick={() => handleRemoveKeyword(kw.id)}
                                    className="text-blue-300/80 hover:text-blue-200 transition-colors"
                                    aria-label={`${kw.keyword} 삭제`}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </span>
                        ))
                    ) : (
                        <p className="text-slate-400 text-sm">추가된 키워드가 없습니다</p>
                    )}
                </div>

                {/* 키워드 추가 */}
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                        placeholder="새 키워드 추가..."
                        className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    />
                    <button
                        onClick={handleAddKeyword}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        추가
                    </button>
                </div>

                <p className="text-xs text-slate-400 mt-3">
                    💡 총 {keywords.length}개의 키워드가 등록되어 있습니다
                </p>
            </div>

            {/* 카테고리 목록 (읽기 전용) */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <h2 className="text-2xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-purple-400" />
                    광고 카테고리
                </h2>

                {categories.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {categories.map((cat) => (
                            <div
                                key={cat.id}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${cat.is_primary
                                        ? 'border-purple-500 bg-purple-500/10'
                                        : 'border-slate-600 bg-slate-700/30'
                                    }`}
                            >
                                <span className="text-slate-100">{cat.category_path}</span>
                                {cat.is_primary && (
                                    <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded">
                                        주요
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-slate-400 text-sm">등록된 카테고리가 없습니다</p>
                )}

                <p className="text-xs text-slate-400 mt-3">
                    💡 총 {categories.length}개의 카테고리가 등록되어 있습니다
                </p>
            </div>
        </div>
    )
}

