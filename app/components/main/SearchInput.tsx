// 검색어 입력창 - Premium Glassmorphism Design

'use client'

import { Search, TrendingUp } from 'lucide-react'
import { useState } from 'react'

interface SearchInputProps {
  onQueryChange: (query: string) => void
  onSearchSubmit: (query: string) => void
  isLoading?: boolean
}

export default function SearchInput({ onQueryChange, onSearchSubmit, isLoading = false }: SearchInputProps) {
  const [query, setQuery] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value
    setQuery(newQuery)
    onQueryChange(newQuery)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      onSearchSubmit(query.trim())
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Premium Search Container with Glassmorphism */}
      <div className="bg-white/5 backdrop-blur-md border border-slate-700/50 rounded-2xl p-4 sm:p-6 shadow-2xl shadow-[#64ffda]/10">
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Search Input Field */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={handleInputChange}
              placeholder="검색어를 입력하세요 (예: '아이폰 15 프로 최저가')"
              className="block w-full pl-12 pr-6 py-4 text-base sm:text-lg bg-transparent border-0 border-b-2 border-slate-600 focus:border-[#64ffda] text-white placeholder-slate-400 focus:outline-none transition-colors duration-200"
              disabled={isLoading}
            />
          </div>

          {/* Submit Button - Premium CTA */}
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="w-full flex items-center justify-center space-x-3 px-6 py-4 text-base sm:text-lg bg-[#64ffda] text-[#0a192f] font-bold rounded-xl transition-all duration-200 transform hover:scale-[1.02] hover:shadow-lg hover:shadow-[#64ffda]/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#0a192f]"></div>
                <span>평가 중...</span>
              </>
            ) : (
              <>
                <TrendingUp className="h-6 w-6" />
                <span>검색 시작하기</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Helper Text */}
      <div className="mt-4 text-center">
        <p className="text-sm text-slate-400">
          팁: 가격·브랜드·리뷰 등 상업적 신호를 포함할수록 품질 점수와 입찰가가 올라갑니다.
        </p>
      </div>
    </div>
  )
}
