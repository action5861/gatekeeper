'use client'

import { AlertCircle, Building2, Check, DollarSign, Globe, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { ErrorBoundary } from '../ui/ErrorBoundary'

interface BusinessSetupProps {
    onComplete: (data: BusinessSetupData) => void
    onBack: () => void
    isLoading?: boolean
}

export interface BusinessSetupData {
    websiteUrl: string
    keywords: string[]
    categories: number[]
    dailyBudget: number
    bidRange: {
        min: number
        max: number
    }
}

interface Category {
    id: number
    name: string
    path: string
    level: number
    children?: Category[]
}

interface FormState {
    websiteUrl: string
    keywords: string[]
    categories: number[]
    dailyBudget: number
    bidRange: {
        min: number
        max: number
    }
}

function BusinessSetup({ onComplete, onBack, isLoading = false }: BusinessSetupProps) {
    const [formData, setFormData] = useState<FormState>({
        websiteUrl: '',
        keywords: [],
        categories: [],
        dailyBudget: 10000,
        bidRange: { min: 100, max: 3000 }
    })
    const [newKeyword, setNewKeyword] = useState('')
    const [categories, setCategories] = useState<Category[]>([])
    const [isLoadingCategories, setIsLoadingCategories] = useState(true)
    const [categoriesError, setCategoriesError] = useState<string>('')
    const [errors, setErrors] = useState<Record<string, string>>({})

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                setIsLoadingCategories(true)
                setCategoriesError('')
                const response = await fetch('/api/business-categories')
                if (!response.ok) throw new Error('카테고리를 불러오는데 실패했습니다')
                const data = await response.json()
                setCategories(data.categories || [])
            } catch (error) {
                setCategoriesError('카테고리 데이터를 불러올 수 없어 기본 값을 사용합니다')
                const fallback: Category[] = [
                    {
                        id: 1, name: '전자제품', path: '전자제품', level: 1, children: [
                            { id: 11, name: '스마트폰', path: '전자제품 > 스마트폰', level: 2 },
                            { id: 12, name: '노트북', path: '전자제품 > 노트북', level: 2 },
                            { id: 13, name: '태블릿', path: '전자제품 > 태블릿', level: 2 },
                        ]
                    },
                    {
                        id: 2, name: '패션', path: '패션', level: 1, children: [
                            { id: 21, name: '남성의류', path: '패션 > 남성의류', level: 2 },
                            { id: 22, name: '여성의류', path: '패션 > 여성의류', level: 2 },
                        ]
                    },
                ]
                setCategories(fallback)
            } finally {
                setIsLoadingCategories(false)
            }
        }
        fetchCategories()
    }, [])

    const isValidUrl = useCallback((url: string): boolean => {
        if (!url.trim()) return false
        try {
            const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`)
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
        } catch {
            return false
        }
    }, [])

    const isKeywordDuplicate = useCallback((keyword: string): boolean => {
        return formData.keywords.some(k => k.toLowerCase() === keyword.toLowerCase())
    }, [formData.keywords])

    const isValidKeyword = useCallback((keyword: string): boolean => {
        const trimmed = keyword.trim()
        return trimmed.length >= 2 && trimmed.length <= 50 && /^[가-힣a-zA-Z0-9\s]+$/.test(trimmed)
    }, [])

    const addKeyword = useCallback(() => {
        const trimmed = newKeyword.trim()
        if (!trimmed) return
        if (!isValidKeyword(trimmed)) { setErrors(prev => ({ ...prev, keywords: '2-50자의 한글/영문/숫자만 입력 가능' })); return }
        if (isKeywordDuplicate(trimmed)) { setErrors(prev => ({ ...prev, keywords: '이미 추가된 키워드입니다' })); return }
        if (formData.keywords.length >= 20) { setErrors(prev => ({ ...prev, keywords: '최대 20개까지 입력 가능합니다' })); return }
        setFormData(prev => ({ ...prev, keywords: [...prev.keywords, trimmed] }))
        setNewKeyword('')
        setErrors(prev => ({ ...prev, keywords: '' }))
    }, [newKeyword, formData.keywords, isValidKeyword, isKeywordDuplicate])

    const removeKeyword = useCallback((index: number) => {
        setFormData(prev => ({ ...prev, keywords: prev.keywords.filter((_, i) => i !== index) }))
    }, [])

    const flatCategories = useMemo(() => {
        const result: Category[] = []
        const walk = (nodes: Category[], level: number) => {
            nodes.forEach(n => {
                result.push({ ...n, level })
                if (n.children && n.children.length) walk(n.children, level + 1)
            })
        }
        walk(categories, 1)
        return result
    }, [categories])

    const validateAll = (): boolean => {
        const newErrors: Record<string, string> = {}
        if (!formData.websiteUrl.trim() || !isValidUrl(formData.websiteUrl)) newErrors.websiteUrl = '올바른 URL을 입력하세요'
        if (formData.keywords.length < 1) newErrors.keywords = '키워드를 1개 이상 입력하세요'
        if (formData.categories.length < 1) newErrors.categories = '카테고리를 1개 이상 선택하세요'
        if (formData.dailyBudget < 1000 || formData.dailyBudget > 1000000) newErrors.dailyBudget = '예산은 1,000~1,000,000원'
        if (formData.bidRange.min < 50 || formData.bidRange.max > 10000 || formData.bidRange.min >= formData.bidRange.max) newErrors.bidRange = '입찰가 범위를 확인하세요'
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = () => {
        if (!validateAll()) return
        onComplete({
            websiteUrl: formData.websiteUrl.trim(),
            keywords: formData.keywords,
            categories: formData.categories,
            dailyBudget: formData.dailyBudget,
            bidRange: formData.bidRange
        })
    }

    return (
        <div className="business-setup min-h-screen w-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100">
            <div className="max-w-3xl w-full mx-auto px-4 py-8 sm:py-12">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-r from-blue-500 to-green-500">
                        <Globe className="w-6 h-6 text-white" />
                    </div>
                    <h1 className="mt-4 text-3xl sm:text-4xl font-bold">비즈니스 설정</h1>
                    <p className="mt-2 text-slate-400">핵심 정보만 간단히 입력하세요</p>
                </div>

                <div className="space-y-6">
                    <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-4 sm:p-6">
                        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Globe className="w-5 h-5" /> 웹사이트</h2>
                        <input
                            type="url"
                            value={formData.websiteUrl}
                            onChange={(e) => { setFormData(prev => ({ ...prev, websiteUrl: e.target.value })); setErrors(prev => ({ ...prev, websiteUrl: '' })) }}
                            placeholder="https://example.com"
                            className={`w-full px-4 py-3 rounded-xl bg-slate-900/60 border ${errors.websiteUrl ? 'border-red-500' : 'border-slate-600'} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                            aria-invalid={!!errors.websiteUrl}
                            aria-describedby={errors.websiteUrl ? 'website-error' : undefined}
                        />
                        {errors.websiteUrl && (
                            <p id="website-error" className="mt-2 text-sm text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" />{errors.websiteUrl}</p>
                        )}
                    </section>

                    <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-4 sm:p-6">
                        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Building2 className="w-5 h-5" /> 키워드</h2>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={newKeyword}
                                onChange={(e) => setNewKeyword(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                                placeholder="키워드를 입력 후 Enter"
                                className="flex-1 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-green-500"
                                aria-invalid={!!errors.keywords}
                            />
                            <button type="button" onClick={addKeyword} className="px-4 py-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white disabled:opacity-50" disabled={!newKeyword.trim()}>추가</button>
                        </div>
                        {errors.keywords && (
                            <p className="mt-2 text-sm text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" />{errors.keywords}</p>
                        )}
                        {formData.keywords.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                                {formData.keywords.map((k, i) => (
                                    <span key={`${k}-${i}`} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-500/15 text-green-300 border border-green-500/30">
                                        {k}
                                        <button type="button" onClick={() => removeKeyword(i)} className="text-green-300/80 hover:text-green-200">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                        <p className="mt-2 text-sm text-slate-400">{formData.keywords.length}/20</p>
                    </section>

                    <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-4 sm:p-6">
                        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Check className="w-5 h-5" /> 카테고리</h2>
                        {isLoadingCategories ? (
                            <p className="text-slate-400">불러오는 중...</p>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {flatCategories.map(cat => {
                                    const isSelected = formData.categories.includes(cat.id)
                                    return (
                                        <label key={cat.id} className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${isSelected ? 'border-purple-500 bg-purple-500/10' : 'border-slate-600 hover:border-slate-500'}`}>
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => {
                                                    setFormData(prev => {
                                                        const exists = prev.categories.includes(cat.id)
                                                        if (exists) return { ...prev, categories: prev.categories.filter(id => id !== cat.id) }
                                                        if (prev.categories.length >= 5) return prev
                                                        return { ...prev, categories: [...prev.categories, cat.id] }
                                                    })
                                                    setErrors(prev => ({ ...prev, categories: '' }))
                                                }}
                                                className="accent-purple-500"
                                            />
                                            <span className={`text-sm ${cat.level > 1 ? 'ml-2' : ''}`}>{cat.name}</span>
                                        </label>
                                    )
                                })}
                            </div>
                        )}
                        {categoriesError && <p className="mt-2 text-sm text-yellow-400">{categoriesError}</p>}
                        {errors.categories && (<p className="mt-2 text-sm text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" />{errors.categories}</p>)}
                        <p className="mt-2 text-sm text-slate-400">{formData.categories.length}/5 선택됨</p>
                    </section>

                    <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-4 sm:p-6">
                        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><DollarSign className="w-5 h-5" /> 예산/입찰</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">일일 예산</label>
                                <input type="number" min={1000} max={1000000} step={1000} value={formData.dailyBudget} onChange={(e) => { setFormData(prev => ({ ...prev, dailyBudget: Number(e.target.value) })); setErrors(prev => ({ ...prev, dailyBudget: '' })) }} className="w-full px-3 py-2 rounded-xl bg-slate-900/60 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-orange-500" />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">최소 입찰가</label>
                                <input type="number" min={50} max={formData.bidRange.max - 1} value={formData.bidRange.min} onChange={(e) => { setFormData(prev => ({ ...prev, bidRange: { ...prev.bidRange, min: Number(e.target.value) } })); setErrors(prev => ({ ...prev, bidRange: '' })) }} className="w-full px-3 py-2 rounded-xl bg-slate-900/60 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-orange-500" />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">최대 입찰가</label>
                                <input type="number" min={formData.bidRange.min + 1} max={10000} value={formData.bidRange.max} onChange={(e) => { setFormData(prev => ({ ...prev, bidRange: { ...prev.bidRange, max: Number(e.target.value) } })); setErrors(prev => ({ ...prev, bidRange: '' })) }} className="w-full px-3 py-2 rounded-xl bg-slate-900/60 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-orange-500" />
                            </div>
                        </div>
                        {(errors.dailyBudget || errors.bidRange) && (
                            <p className="mt-2 text-sm text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" />{errors.dailyBudget || errors.bidRange}</p>
                        )}
                    </section>
                </div>

                <div className="mt-8 flex gap-3 justify-center">
                    <button type="button" onClick={onBack} disabled={isLoading} className="px-5 py-3 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50">이전</button>
                    <button type="button" onClick={handleSubmit} disabled={isLoading} className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-green-500 text-white font-semibold disabled:opacity-50">설정 완료</button>
                </div>
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
                // 실제 프로덕션에서는 에러 모니터링 서비스로 전송
            }}
        >
            <BusinessSetup {...props} />
        </ErrorBoundary>
    )
} 