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
    <div className="w-full max-w-5xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Search Input Field */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-6 w-6 text-slate-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Enter your search intent (e.g., 'iPhone 15 Pro Max best price')"
            className="block w-full pl-12 pr-6 py-5 text-lg border border-slate-600 rounded-xl bg-slate-800 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            disabled={isLoading}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full flex items-center justify-center space-x-3 px-8 py-5 text-lg bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 disabled:from-slate-600 disabled:to-slate-600 text-white font-bold rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
              <span>Evaluating...</span>
            </>
          ) : (
            <>
              <TrendingUp className="h-6 w-6" />
              <span>List & Start Auction</span>
            </>
          )}
        </button>
      </form>

      {/* Helper Text */}
      <div className="mt-6 text-center">
        <p className="text-base text-slate-400">
          Tip: Include commercial signals like price, brand, or review to boost quality score and bid value.
        </p>
      </div>
    </div>
  )
} 