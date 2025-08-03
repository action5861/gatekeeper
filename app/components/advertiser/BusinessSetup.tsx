'use client'

import { AlertCircle, Check, ChevronDown, ChevronRight, Plus, X } from 'lucide-react'
import { useEffect, useState } from 'react'

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

export default function BusinessSetup({ onComplete, onBack, isLoading = false }: BusinessSetupProps) {
    const [websiteUrl, setWebsiteUrl] = useState('')
    const [keywords, setKeywords] = useState<string[]>([])
    const [newKeyword, setNewKeyword] = useState('')
    const [selectedCategories, setSelectedCategories] = useState<number[]>([])
    const [dailyBudget, setDailyBudget] = useState(10000)
    const [bidRange, setBidRange] = useState({ min: 100, max: 3000 })
    const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set())
    const [categories, setCategories] = useState<Category[]>([])
    const [errors, setErrors] = useState<Record<string, string>>({})

    // Load categories from API
    useEffect(() => {
        const loadCategories = async () => {
            try {
                const response = await fetch('/api/business-categories')
                if (response.ok) {
                    const data = await response.json()
                    setCategories(buildCategoryTree(data))
                }
            } catch (error) {
                console.error('Failed to load categories:', error)
            }
        }
        loadCategories()
    }, [])

    const buildCategoryTree = (flatCategories: any[]): Category[] => {
        const categoryMap = new Map<number, Category>()
        const rootCategories: Category[] = []

        // Create category objects
        flatCategories.forEach(cat => {
            categoryMap.set(cat.id, { ...cat, children: [] })
        })

        // Build tree structure
        flatCategories.forEach(cat => {
            if (cat.parent_id) {
                const parent = categoryMap.get(cat.parent_id)
                if (parent) {
                    parent.children!.push(categoryMap.get(cat.id)!)
                }
            } else {
                rootCategories.push(categoryMap.get(cat.id)!)
            }
        })

        return rootCategories
    }

    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {}

        // Website URL validation
        if (!websiteUrl.trim()) {
            newErrors.websiteUrl = '웹사이트 URL을 입력해주세요'
        } else if (!isValidUrl(websiteUrl)) {
            newErrors.websiteUrl = '올바른 URL 형식을 입력해주세요'
        }

        // Keywords validation
        if (keywords.length === 0) {
            newErrors.keywords = '최소 1개의 키워드를 입력해주세요'
        } else if (keywords.length > 20) {
            newErrors.keywords = '키워드는 최대 20개까지 입력 가능합니다'
        }

        // Categories validation
        if (selectedCategories.length === 0) {
            newErrors.categories = '최소 1개의 카테고리를 선택해주세요'
        } else if (selectedCategories.length > 3) {
            newErrors.categories = '카테고리는 최대 3개까지 선택 가능합니다'
        }

        // Budget validation
        if (dailyBudget < 1000) {
            newErrors.dailyBudget = '일일 예산은 최소 1,000원 이상이어야 합니다'
        }

        // Bid range validation
        if (bidRange.min >= bidRange.max) {
            newErrors.bidRange = '최소 입찰가는 최대 입찰가보다 작아야 합니다'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const isValidUrl = (url: string): boolean => {
        try {
            new URL(url.startsWith('http') ? url : `https://${url}`)
            return true
        } catch {
            return false
        }
    }

    const addKeyword = () => {
        const trimmedKeyword = newKeyword.trim()
        if (trimmedKeyword && !keywords.includes(trimmedKeyword) && keywords.length < 20) {
            setKeywords([...keywords, trimmedKeyword])
            setNewKeyword('')
            setErrors(prev => ({ ...prev, keywords: '' }))
        }
    }

    const removeKeyword = (index: number) => {
        setKeywords(keywords.filter((_, i) => i !== index))
    }

    const toggleCategory = (categoryId: number) => {
        setExpandedCategories(prev => {
            const newSet = new Set(prev)
            if (newSet.has(categoryId)) {
                newSet.delete(categoryId)
            } else {
                newSet.add(categoryId)
            }
            return newSet
        })
    }

    const selectCategory = (categoryId: number) => {
        setSelectedCategories(prev => {
            if (prev.includes(categoryId)) {
                return prev.filter(id => id !== categoryId)
            } else if (prev.length < 3) {
                return [...prev, categoryId]
            }
            return prev
        })
        setErrors(prev => ({ ...prev, categories: '' }))
    }

    const getCategoryName = (categoryId: number): string => {
        const findCategory = (cats: Category[]): Category | null => {
            for (const cat of cats) {
                if (cat.id === categoryId) return cat
                if (cat.children) {
                    const found = findCategory(cat.children)
                    if (found) return found
                }
            }
            return null
        }
        return findCategory(categories)?.name || ''
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (validateForm()) {
            onComplete({
                websiteUrl: websiteUrl.trim(),
                keywords,
                categories: selectedCategories,
                dailyBudget,
                bidRange
            })
        }
    }

    const renderCategoryTree = (categories: Category[], level: number = 0) => {
        return categories.map(category => (
            <div key={category.id} className="ml-4">
                <div className="flex items-center space-x-2 py-1">
                    {category.children && category.children.length > 0 && (
                        <button
                            type="button"
                            onClick={() => toggleCategory(category.id)}
                            className="text-slate-400 hover:text-slate-300"
                        >
                            {expandedCategories.has(category.id) ? (
                                <ChevronDown className="w-4 h-4" />
                            ) : (
                                <ChevronRight className="w-4 h-4" />
                            )}
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={() => selectCategory(category.id)}
                        className={`flex items-center space-x-2 px-2 py-1 rounded text-sm transition-colors ${selectedCategories.includes(category.id)
                                ? 'bg-blue-500 text-white'
                                : 'text-slate-300 hover:bg-slate-700'
                            }`}
                    >
                        {selectedCategories.includes(category.id) && (
                            <Check className="w-4 h-4" />
                        )}
                        <span>{category.name}</span>
                    </button>
                </div>
                {category.children && category.children.length > 0 && expandedCategories.has(category.id) && (
                    renderCategoryTree(category.children, level + 1)
                )}
            </div>
        ))
    }

    return (
        <div className="w-full max-w-4xl mx-auto">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8 shadow-2xl">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-slate-100 mb-2">
                        비즈니스 설정
                    </h1>
                    <p className="text-slate-400">
                        광고 효과를 극대화하기 위한 정보를 입력해주세요
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-8">
                    {/* Website URL */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            웹사이트 URL <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="url"
                            value={websiteUrl}
                            onChange={(e) => {
                                setWebsiteUrl(e.target.value)
                                setErrors(prev => ({ ...prev, websiteUrl: '' }))
                            }}
                            className={`w-full px-4 py-3 bg-slate-700/50 border rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${errors.websiteUrl ? 'border-red-500' : 'border-slate-600'
                                }`}
                            placeholder="https://example.com"
                        />
                        {errors.websiteUrl && (
                            <p className="text-red-400 text-sm mt-1 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {errors.websiteUrl}
                            </p>
                        )}
                    </div>

                    {/* Keywords */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            주요 취급 상품/서비스 키워드 <span className="text-red-400">*</span>
                            <span className="text-slate-400 text-xs ml-2">(최대 20개)</span>
                        </label>
                        <div className="space-y-3">
                            <div className="flex space-x-2">
                                <input
                                    type="text"
                                    value={newKeyword}
                                    onChange={(e) => setNewKeyword(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                                    className="flex-1 px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="키워드를 입력하고 Enter 또는 + 버튼을 클릭하세요"
                                    disabled={keywords.length >= 20}
                                />
                                <button
                                    type="button"
                                    onClick={addKeyword}
                                    disabled={keywords.length >= 20 || !newKeyword.trim()}
                                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Plus className="w-4 h-4" />
                                </button>
                            </div>
                            {keywords.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {keywords.map((keyword, index) => (
                                        <span
                                            key={index}
                                            className="flex items-center space-x-1 px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-blue-300"
                                        >
                                            <span className="text-sm">{keyword}</span>
                                            <button
                                                type="button"
                                                onClick={() => removeKeyword(index)}
                                                className="text-blue-400 hover:text-blue-300"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            )}
                            {errors.keywords && (
                                <p className="text-red-400 text-sm flex items-center">
                                    <AlertCircle className="w-4 h-4 mr-1" />
                                    {errors.keywords}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Categories */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            비즈니스 카테고리 <span className="text-red-400">*</span>
                            <span className="text-slate-400 text-xs ml-2">(최대 3개)</span>
                        </label>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-4 max-h-64 overflow-y-auto">
                                {categories.length > 0 ? (
                                    renderCategoryTree(categories)
                                ) : (
                                    <p className="text-slate-400 text-sm">카테고리를 불러오는 중...</p>
                                )}
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-slate-300 mb-2">선택된 카테고리</h4>
                                {selectedCategories.length > 0 ? (
                                    <div className="space-y-2">
                                        {selectedCategories.map(categoryId => (
                                            <div
                                                key={categoryId}
                                                className="flex items-center justify-between p-2 bg-slate-700/50 border border-slate-600 rounded"
                                            >
                                                <span className="text-slate-300 text-sm">
                                                    {getCategoryName(categoryId)}
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={() => selectCategory(categoryId)}
                                                    className="text-red-400 hover:text-red-300"
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-400 text-sm">선택된 카테고리가 없습니다</p>
                                )}
                            </div>
                        </div>
                        {errors.categories && (
                            <p className="text-red-400 text-sm mt-1 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {errors.categories}
                            </p>
                        )}
                    </div>

                    {/* Daily Budget */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            희망 일일 예산 <span className="text-red-400">*</span>
                        </label>
                        <div className="space-y-3">
                            <input
                                type="range"
                                min="1000"
                                max="100000"
                                step="1000"
                                value={dailyBudget}
                                onChange={(e) => {
                                    setDailyBudget(Number(e.target.value))
                                    setErrors(prev => ({ ...prev, dailyBudget: '' }))
                                }}
                                className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer slider"
                            />
                            <div className="flex justify-between text-sm text-slate-400">
                                <span>1,000원</span>
                                <span className="text-slate-300 font-medium">
                                    {dailyBudget.toLocaleString()}원
                                </span>
                                <span>100,000원</span>
                            </div>
                            {errors.dailyBudget && (
                                <p className="text-red-400 text-sm flex items-center">
                                    <AlertCircle className="w-4 h-4 mr-1" />
                                    {errors.dailyBudget}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Bid Range */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            예상 키워드당 입찰가 범위 <span className="text-red-400">*</span>
                        </label>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">최소 입찰가</label>
                                <input
                                    type="number"
                                    min="50"
                                    max={bidRange.max - 100}
                                    value={bidRange.min}
                                    onChange={(e) => {
                                        setBidRange(prev => ({ ...prev, min: Number(e.target.value) }))
                                        setErrors(prev => ({ ...prev, bidRange: '' }))
                                    }}
                                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">최대 입찰가</label>
                                <input
                                    type="number"
                                    min={bidRange.min + 100}
                                    max="10000"
                                    value={bidRange.max}
                                    onChange={(e) => {
                                        setBidRange(prev => ({ ...prev, max: Number(e.target.value) }))
                                        setErrors(prev => ({ ...prev, bidRange: '' }))
                                    }}
                                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                        {errors.bidRange && (
                            <p className="text-red-400 text-sm mt-1 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {errors.bidRange}
                            </p>
                        )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-4 pt-6">
                        <button
                            type="button"
                            onClick={onBack}
                            disabled={isLoading}
                            className="flex-1 px-6 py-3 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
                        >
                            이전
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="flex-1 bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            {isLoading ? (
                                <div className="flex items-center justify-center space-x-2">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                    <span>처리 중...</span>
                                </div>
                            ) : (
                                '완료'
                            )}
                        </button>
                    </div>
                </form>
            </div>

            <style jsx>{`
                .slider::-webkit-slider-thumb {
                    appearance: none;
                    height: 20px;
                    width: 20px;
                    border-radius: 50%;
                    background: #3b82f6;
                    cursor: pointer;
                }
                .slider::-moz-range-thumb {
                    height: 20px;
                    width: 20px;
                    border-radius: 50%;
                    background: #3b82f6;
                    cursor: pointer;
                    border: none;
                }
            `}</style>
        </div>
    )
} 