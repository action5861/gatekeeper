'use client'

import { X as Cancel, Edit3, Plus, Save, X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface KeywordEditorProps {
    keywords: string[]
    onKeywordsChange: (keywords: string[]) => void
    maxKeywords?: number
}

export default function KeywordEditor({
    keywords,
    onKeywordsChange,
    maxKeywords = 20
}: KeywordEditorProps) {
    const [editingKeywords, setEditingKeywords] = useState<string[]>(keywords)
    const [newKeyword, setNewKeyword] = useState('')
    const [isEditing, setIsEditing] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        setEditingKeywords(keywords)
    }, [keywords])

    const addKeyword = () => {
        const trimmedKeyword = newKeyword.trim()

        if (!trimmedKeyword) {
            setError('키워드를 입력해주세요')
            return
        }

        if (editingKeywords.includes(trimmedKeyword)) {
            setError('이미 존재하는 키워드입니다')
            return
        }

        if (editingKeywords.length >= maxKeywords) {
            setError(`키워드는 최대 ${maxKeywords}개까지 입력 가능합니다`)
            return
        }

        const updatedKeywords = [...editingKeywords, trimmedKeyword]
        setEditingKeywords(updatedKeywords)
        setNewKeyword('')
        setError(null)
    }

    const removeKeyword = (index: number) => {
        const updatedKeywords = editingKeywords.filter((_, i) => i !== index)
        setEditingKeywords(updatedKeywords)
        setError(null)
    }

    const saveChanges = () => {
        onKeywordsChange(editingKeywords)
        setIsEditing(false)
        setError(null)
    }

    const cancelChanges = () => {
        setEditingKeywords(keywords)
        setIsEditing(false)
        setError(null)
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            addKeyword()
        }
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-300">
                    키워드 관리 ({editingKeywords.length}/{maxKeywords})
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

            {/* Add Keyword Input */}
            {isEditing && (
                <div className="space-y-2">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={newKeyword}
                            onChange={(e) => setNewKeyword(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="새 키워드 입력"
                            className="flex-1 px-3 py-2 text-sm bg-slate-700/50 border border-slate-600 rounded text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={editingKeywords.length >= maxKeywords}
                        />
                        <button
                            onClick={addKeyword}
                            disabled={editingKeywords.length >= maxKeywords || !newKeyword.trim()}
                            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                    {error && (
                        <p className="text-red-400 text-xs">{error}</p>
                    )}
                </div>
            )}

            {/* Keywords List */}
            <div className="space-y-2">
                {editingKeywords.length === 0 ? (
                    <p className="text-slate-400 text-sm">등록된 키워드가 없습니다</p>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {editingKeywords.map((keyword, index) => (
                            <span
                                key={index}
                                className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm ${isEditing
                                        ? 'bg-blue-500/20 border border-blue-500/30 text-blue-300'
                                        : 'bg-slate-700/50 border border-slate-600 text-slate-300'
                                    }`}
                            >
                                <span>{keyword}</span>
                                {isEditing && (
                                    <button
                                        onClick={() => removeKeyword(index)}
                                        className="text-red-400 hover:text-red-300 transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                )}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Status */}
            {!isEditing && editingKeywords.length > 0 && (
                <p className="text-slate-400 text-xs">
                    편집하려면 "편집" 버튼을 클릭하세요
                </p>
            )}
        </div>
    )
} 