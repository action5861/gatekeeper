'use client'

import { X as Cancel, Check, ChevronDown, ChevronRight, Edit3, Save, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface Category {
    id: number
    name: string
    path: string
    level: number
    children?: Category[]
}

interface CategorySelectorProps {
    categories: number[]
    onCategoriesChange: (categories: number[]) => void
    maxCategories?: number
}

export default function CategorySelector({
    categories,
    onCategoriesChange,
    maxCategories = 3
}: CategorySelectorProps) {
    const [categoryTree, setCategoryTree] = useState<Category[]>([])
    const [selectedCategories, setSelectedCategories] = useState<number[]>(categories)
    const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set())
    const [isEditing, setIsEditing] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        loadCategories()
    }, [])

    useEffect(() => {
        setSelectedCategories(categories)
    }, [categories])

    const loadCategories = async () => {
        try {
            const response = await fetch('/api/business-categories')
            if (response.ok) {
                const data = await response.json()
                console.log('API 응답 데이터:', data)

                // 이 엔드포인트는 플랫 배열을 반환함
                const flat = data?.categories ?? data
                if (Array.isArray(flat)) {
                    setCategoryTree(buildCategoryTree(flat))
                } else {
                    console.error('Unexpected API response format:', data)
                    setCategoryTree([])
                }
            }
        } catch (error) {
            console.error('Failed to load categories:', error)
            setCategoryTree([])
        } finally {
            setIsLoading(false)
        }
    }

    const buildCategoryTree = (flatCategories: any[]): Category[] => {
        // flatCategories가 배열이 아니거나 비어있으면 빈 배열 반환
        if (!Array.isArray(flatCategories) || flatCategories.length === 0) {
            console.warn('flatCategories is not an array or is empty:', flatCategories)
            return []
        }

        const categoryMap = new Map<number, Category>()
        const rootCategories: Category[] = []

        flatCategories.forEach(cat => {
            if (cat && cat.id) {
                categoryMap.set(cat.id, { ...cat, children: [] })
            }
        })

        flatCategories.forEach(cat => {
            if (cat && cat.id) {
                if (cat.parent_id) {
                    const parent = categoryMap.get(cat.parent_id)
                    if (parent) {
                        parent.children!.push(categoryMap.get(cat.id)!)
                    }
                } else {
                    rootCategories.push(categoryMap.get(cat.id)!)
                }
            }
        })

        return rootCategories
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
        if (!isEditing) return

        setSelectedCategories(prev => {
            if (prev.includes(categoryId)) {
                return prev.filter(id => id !== categoryId)
            }
            // 최대 개수 제한: 초과 시 마지막 항목을 제거하고 새 항목 추가
            if (prev.length >= maxCategories) {
                const next = [...prev]
                next.pop()
                next.push(categoryId)
                return next
            }
            return [...prev, categoryId]
        })
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
        const found = findCategory(categoryTree)
        return found?.name || `ID ${categoryId}`
    }

    const saveChanges = () => {
        onCategoriesChange(selectedCategories)
        setIsEditing(false)
    }

    const cancelChanges = () => {
        setSelectedCategories(categories)
        setIsEditing(false)
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
                        disabled={!isEditing}
                        className={`flex items-center space-x-2 px-2 py-1 rounded text-sm transition-colors ${selectedCategories.includes(category.id)
                            ? 'bg-blue-500 text-white'
                            : 'text-slate-300 hover:bg-slate-700'
                            } ${!isEditing ? 'cursor-default' : ''}`}
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

    if (isLoading) {
        return (
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-slate-300">
                        카테고리 선택 ({selectedCategories.length}/{maxCategories})
                    </h3>
                </div>
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-300">
                    카테고리 선택 ({selectedCategories.length}/{maxCategories})
                </h3>
                <div className="flex items-center space-x-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={saveChanges}
                                className="flex items-center space-x-1 px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                            >
                                <Save className="w-3 h-3" />
                                <span>저장</span>
                            </button>
                            <button
                                onClick={cancelChanges}
                                className="flex items-center space-x-1 px-2 py-1 text-xs bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors"
                            >
                                <Cancel className="w-3 h-3" />
                                <span>취소</span>
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="flex items-center space-x-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                            <Edit3 className="w-3 h-3" />
                            <span>편집</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Selected Categories */}
            {selectedCategories.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-xs font-medium text-slate-400">선택된 카테고리</h4>
                    <div className="space-y-1">
                        {selectedCategories.map(categoryId => (
                            <div
                                key={categoryId}
                                className="flex items-center justify-between p-2 bg-slate-700/50 border border-slate-600 rounded"
                            >
                                <span className="text-slate-300 text-sm">
                                    {getCategoryName(categoryId)}
                                </span>
                                {isEditing && (
                                    <button
                                        onClick={() => selectCategory(categoryId)}
                                        className="text-red-400 hover:text-red-300"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Category Tree */}
            <div className="space-y-2">
                <h4 className="text-xs font-medium text-slate-400">
                    {isEditing ? '카테고리를 선택하세요' : '카테고리 목록'}
                </h4>
                <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-4 max-h-64 overflow-y-auto">
                    {categoryTree.length > 0 ? (
                        renderCategoryTree(categoryTree)
                    ) : (
                        <p className="text-slate-400 text-sm">카테고리를 불러올 수 없습니다</p>
                    )}
                </div>
            </div>

            {/* Status */}
            {!isEditing && selectedCategories.length > 0 && (
                <p className="text-slate-400 text-xs">
                    편집하려면 "편집" 버튼을 클릭하세요
                </p>
            )}
        </div>
    )
} 