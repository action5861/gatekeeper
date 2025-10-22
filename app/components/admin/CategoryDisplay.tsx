'use client'

import { Edit3, Save, Tag, X } from 'lucide-react'
import { useState } from 'react'

interface CategoryDisplayProps {
    categories: string[]
    onCategoriesChange: (categories: string[]) => void
    maxCategories?: number
}

export default function CategoryDisplay({
    categories,
    onCategoriesChange,
    maxCategories = 5
}: CategoryDisplayProps) {
    const [isEditing, setIsEditing] = useState(false)
    const [editingCategories, setEditingCategories] = useState<string[]>(categories)
    const [newCategory, setNewCategory] = useState('')

    const handleAddCategory = () => {
        const trimmed = newCategory.trim()
        if (!trimmed) return

        if (editingCategories.includes(trimmed)) {
            alert('이미 추가된 카테고리입니다')
            return
        }

        if (editingCategories.length >= maxCategories) {
            alert(`최대 ${maxCategories}개까지만 추가할 수 있습니다`)
            return
        }

        setEditingCategories([...editingCategories, trimmed])
        setNewCategory('')
    }

    const handleRemoveCategory = (category: string) => {
        setEditingCategories(editingCategories.filter(c => c !== category))
    }

    const handleSave = () => {
        onCategoriesChange(editingCategories)
        setIsEditing(false)
    }

    const handleCancel = () => {
        setEditingCategories(categories)
        setNewCategory('')
        setIsEditing(false)
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-300">
                    카테고리 ({editingCategories.length}/{maxCategories})
                </h3>
                <div className="flex items-center space-x-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleSave}
                                className="flex items-center space-x-1 px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                            >
                                <Save className="w-3 h-3" />
                                <span>저장</span>
                            </button>
                            <button
                                onClick={handleCancel}
                                className="flex items-center space-x-1 px-2 py-1 text-xs bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors"
                            >
                                <X className="w-3 h-3" />
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

            {/* Category List */}
            <div className="space-y-2">
                {editingCategories.length === 0 ? (
                    <p className="text-slate-400 text-sm">등록된 카테고리가 없습니다</p>
                ) : (
                    editingCategories.map((category, index) => (
                        <div
                            key={index}
                            className="flex items-center justify-between p-3 bg-slate-700/50 border border-slate-600 rounded"
                        >
                            <div className="flex items-center space-x-2">
                                <Tag className="w-4 h-4 text-blue-400" />
                                <span className="text-slate-300">{category}</span>
                            </div>
                            {isEditing && (
                                <button
                                    onClick={() => handleRemoveCategory(category)}
                                    className="text-red-400 hover:text-red-300"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Add Category Input */}
            {isEditing && editingCategories.length < maxCategories && (
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={newCategory}
                        onChange={(e) => setNewCategory(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddCategory()}
                        placeholder="새 카테고리 입력..."
                        className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                        onClick={handleAddCategory}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                        추가
                    </button>
                </div>
            )}

            {/* Help Text */}
            {!isEditing && (
                <p className="text-slate-400 text-xs">
                    편집하려면 "편집" 버튼을 클릭하세요
                </p>
            )}
        </div>
    )
}



