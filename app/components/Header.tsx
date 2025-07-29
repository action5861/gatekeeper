// 공통 헤더

'use client'

import { BarChart3, Building2, ChevronDown, LogOut, TrendingUp, User } from 'lucide-react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'

export default function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const navItems = [
    {
      name: 'Exchange',
      href: '/',
      icon: TrendingUp
    },
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: BarChart3
    }
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userType')
    router.push('/login')
  }

  const handleSignIn = (userType: 'user' | 'advertiser') => {
    setShowDropdown(false)
    // Store the selected user type in localStorage for the login page
    localStorage.setItem('selectedUserType', userType)
    router.push('/login')
  }

  const isAuthenticated = typeof window !== 'undefined' && localStorage.getItem('token')

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50 animate-slideDown">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3 hover:scale-105 transition-transform duration-200">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
              Real-time Search Data Exchange
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href

              return (
                <div key={item.name} className="hover:scale-105 active:scale-95 transition-transform duration-200">
                  <Link
                    href={item.href}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700'
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                </div>
              )
            })}

            {/* Sign In Dropdown or Logout Button */}
            {isAuthenticated ? (
              <div className="hover:scale-105 active:scale-95 transition-transform duration-200">
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 text-slate-300 hover:text-white hover:bg-red-600"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            ) : (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 text-slate-300 hover:text-white hover:bg-slate-700"
                >
                  <span className="font-medium">Sign In</span>
                  <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu */}
                {showDropdown && (
                  <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl backdrop-blur-sm animate-fadeIn">
                    <div className="py-2">
                      <button
                        onClick={() => handleSignIn('user')}
                        className="w-full flex items-center space-x-3 px-4 py-3 text-left text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                      >
                        <User className="w-4 h-4" />
                        <span>User Sign In</span>
                      </button>
                      <button
                        onClick={() => handleSignIn('advertiser')}
                        className="w-full flex items-center space-x-3 px-4 py-3 text-left text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                      >
                        <Building2 className="w-4 h-4" />
                        <span>Advertiser Sign In</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
} 