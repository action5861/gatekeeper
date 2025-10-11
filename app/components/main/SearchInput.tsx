// 검색어 입력창

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
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Search Input Field */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Enter your search intent (e.g., 'iPhone 15 Pro Max best price')"
            className="block w-full pl-10 pr-4 py-3 border border-slate-600 rounded-lg bg-slate-800 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            disabled={isLoading}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Evaluating...</span>
            </>
          ) : (
            <>
              <TrendingUp className="h-5 w-5" />
              <span>List & Start Auction</span>
            </>
          )}
        </button>
      </form>

      {/* Helper Text */}
      <div className="mt-4 text-center">
        <p className="text-sm text-slate-400">
          Tip: Include commercial signals like price, brand, or review to boost quality score and bid value.
        </p>
      </div>
    </div>
  )
} 