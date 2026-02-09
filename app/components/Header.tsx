// 공통 헤더

'use client'

import { ArrowLeft, BarChart3, Building2, ChevronDown, HelpCircle, LogOut, Menu, Settings, TrendingUp, User, UserPlus, X } from 'lucide-react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'

export default function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const [showDropdown, setShowDropdown] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const mobileMenuRef = useRef<HTMLDivElement>(null)

  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userType, setUserType] = useState<'user' | 'advertiser' | null>(null)

  const syncAuthState = () => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('token')
    const storedUserType = localStorage.getItem('userType') as 'user' | 'advertiser' | null
    setIsAuthenticated(!!token)
    setUserType(storedUserType)
  }

  const handleLogout = () => {
    if (typeof window === 'undefined') return
    localStorage.removeItem('token')
    localStorage.removeItem('userType')
    setIsAuthenticated(false)
    setUserType(null)
    router.push('/login')
  }

  const handleSignIn = (userType: 'user' | 'advertiser') => {
    if (typeof window === 'undefined') return
    setShowDropdown(false)
    setMobileMenuOpen(false)
    // Store the selected user type in localStorage for the login page
    localStorage.setItem('selectedUserType', userType)
    router.push('/login')
  }

  const closeMobileMenu = () => setMobileMenuOpen(false)

  const goBack = () => {
    setMobileMenuOpen(false)
    router.back()
  }

  const showBackButton = pathname !== '/'

  useEffect(() => {
    syncAuthState()
    if (typeof window === 'undefined') return
    const handleStorage = () => syncAuthState()
    window.addEventListener('storage', handleStorage)
    return () => {
      window.removeEventListener('storage', handleStorage)
    }
  }, [])

  useEffect(() => {
    syncAuthState()
  }, [pathname])

  const navItems = useMemo(() => {
    if (userType === 'advertiser') {
      return [
        {
          name: 'Exchange',
          href: '/',
          icon: TrendingUp
        },
        {
          name: 'Advertiser Dashboard',
          href: '/advertiser/dashboard',
          icon: BarChart3
        },
        {
          name: 'Auto Bidding',
          href: '/advertiser/auto-bidding',
          icon: Settings
        },
        {
          name: 'Review Suggestions',
          href: '/advertiser/review-suggestions',
          icon: HelpCircle
        }
      ]
    }

    return [
      {
        name: 'Exchange',
        href: '/',
        icon: TrendingUp
      },
      {
        name: 'Dashboard',
        href: '/dashboard',
        icon: BarChart3
      },
      {
        name: 'How It Works',
        href: '/how-it-works',
        icon: HelpCircle
      }
    ]
  }, [userType])

  // Close dropdown and mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (dropdownRef.current && !dropdownRef.current.contains(target)) {
        setShowDropdown(false)
      }
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(target)) {
        setMobileMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const navLinkClass = (isActive: boolean) =>
    `flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 min-h-[44px] ${isActive
      ? 'bg-blue-600 text-white shadow-lg'
      : 'text-slate-300 hover:text-white hover:bg-slate-700'
    }`

  return (
    <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50 animate-slideDown" ref={mobileMenuRef}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Back (mobile, when not home) + Logo */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {showBackButton && (
              <button
                type="button"
                onClick={goBack}
                className="md:hidden flex items-center justify-center w-10 h-10 min-h-[44px] min-w-[44px] shrink-0 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                aria-label="뒤로 가기"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <Link href="/" className="flex items-center space-x-3 hover:scale-105 transition-transform duration-200 min-w-0">
              <div className="w-8 h-8 shrink-0 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent truncate">
                Intendex
              </h1>
            </Link>
          </div>

          {/* Desktop Navigation (md+) */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <div key={item.name} className="hover:scale-105 active:scale-95 transition-transform duration-200">
                  <Link href={item.href} className={navLinkClass(isActive)}>
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                </div>
              )
            })}

            {isAuthenticated ? (
              <div className="hover:scale-105 active:scale-95 transition-transform duration-200">
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 min-h-[44px] text-slate-300 hover:text-white hover:bg-red-600"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            ) : (
              <>
                <Link
                  href="/register"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 min-h-[44px] text-slate-300 hover:text-white hover:bg-slate-700"
                >
                  <UserPlus className="w-4 h-4" />
                  <span className="font-medium">Sign up</span>
                </Link>
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowDropdown(!showDropdown)}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 min-h-[44px] text-slate-300 hover:text-white hover:bg-slate-700"
                  >
                    <span className="font-medium">Sign In</span>
                    <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  {showDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl backdrop-blur-sm animate-fadeIn">
                      <div className="py-2">
                        <button
                          onClick={() => handleSignIn('user')}
                          className="w-full flex items-center space-x-3 px-4 py-3 min-h-[44px] text-left text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                        >
                          <User className="w-4 h-4" />
                          <span>User Sign In</span>
                        </button>
                        <button
                          onClick={() => handleSignIn('advertiser')}
                          className="w-full flex items-center space-x-3 px-4 py-3 min-h-[44px] text-left text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                        >
                          <Building2 className="w-4 h-4" />
                          <span>Advertiser Sign In</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </nav>

          {/* Mobile: Hamburger button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex items-center justify-center w-12 h-12 min-h-[44px] min-w-[44px] rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile dropdown menu (below header, full width) */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-700 bg-slate-800/95 backdrop-blur-sm animate-fadeIn">
            <nav className="py-2 flex flex-col gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={closeMobileMenu}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 min-h-[44px] ${isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700'
                      }`}
                  >
                    <Icon className="w-5 h-5 shrink-0" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                )
              })}
              {isAuthenticated ? (
                <button
                  onClick={() => { closeMobileMenu(); handleLogout(); }}
                  className="flex items-center space-x-3 px-4 py-3 min-h-[44px] w-full text-left rounded-lg text-slate-300 hover:text-white hover:bg-red-600 transition-all duration-200"
                >
                  <LogOut className="w-5 h-5 shrink-0" />
                  <span className="font-medium">Logout</span>
                </button>
              ) : (
                <>
                  <Link
                    href="/register"
                    onClick={closeMobileMenu}
                    className="flex items-center space-x-3 px-4 py-3 min-h-[44px] w-full text-left rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                  >
                    <UserPlus className="w-5 h-5 shrink-0" />
                    <span className="font-medium">회원가입 (Sign up)</span>
                  </Link>
                  <button
                    onClick={() => { setShowDropdown(!showDropdown); }}
                    className="flex items-center space-x-3 px-4 py-3 min-h-[44px] w-full text-left rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                  >
                    <span className="font-medium">Sign In</span>
                    <ChevronDown className={`w-5 h-5 shrink-0 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  {showDropdown && (
                    <div className="px-4 pb-2 flex flex-col gap-1">
                      <button
                        onClick={() => handleSignIn('user')}
                        className="flex items-center space-x-3 px-4 py-3 min-h-[44px] w-full text-left rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                      >
                        <User className="w-5 h-5 shrink-0" />
                        <span>User Sign In</span>
                      </button>
                      <button
                        onClick={() => handleSignIn('advertiser')}
                        className="flex items-center space-x-3 px-4 py-3 min-h-[44px] w-full text-left rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-all duration-200"
                      >
                        <Building2 className="w-5 h-5 shrink-0" />
                        <span>Advertiser Sign In</span>
                      </button>
                    </div>
                  )}
                </>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  )
} 