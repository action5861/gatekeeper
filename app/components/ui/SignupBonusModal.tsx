'use client'

import { useEffect } from 'react'
import { X, Gift, Sparkles } from 'lucide-react'

interface SignupBonusModalProps {
  isOpen: boolean
  onClose: () => void
  amount: number
}

export default function SignupBonusModal({ isOpen, onClose, amount }: SignupBonusModalProps) {
  useEffect(() => {
    if (isOpen) {
      // 5초 후 자동으로 닫기
      const timer = setTimeout(() => {
        onClose()
      }, 5000)

      return () => clearTimeout(timer)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 max-w-md w-full mx-4 border border-slate-700 shadow-2xl animate-fadeInUp">
        <div className="text-center">
          {/* Success Icon with Animation */}
          <div className="w-20 h-20 bg-gradient-to-br from-yellow-400/20 to-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
            <Gift className="w-10 h-10 text-yellow-400" />
          </div>
          
          {/* Sparkles Decoration */}
          <div className="flex justify-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse" />
            <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse delay-150" />
            <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse delay-300" />
          </div>
          
          {/* Title */}
          <h3 className="text-2xl font-bold text-slate-100 mb-3">
            🎉 가입을 축하합니다!
          </h3>
          
          {/* Subtitle */}
          <p className="text-slate-300 mb-6 text-lg">
            가입 축하금이 지급되었습니다
          </p>
          
          {/* Amount */}
          <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-xl p-6 mb-6 border border-yellow-500/30">
            <div className="text-4xl font-bold text-yellow-400 mb-2">
              +{amount.toLocaleString()}P
            </div>
            <p className="text-slate-400 text-sm">
              10,000P 이상 모이면 출금하실 수 있습니다
            </p>
          </div>
          
          {/* Message */}
          <p className="text-slate-300 mb-6 text-sm">
            Intendex에 가입해 주셔서 감사합니다.<br />
            앞으로도 많은 이용 부탁드립니다!
          </p>
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg transition-all duration-200 flex items-center space-x-2 mx-auto shadow-lg hover:shadow-xl"
          >
            <X className="w-4 h-4" />
            <span>확인</span>
          </button>
        </div>
      </div>
    </div>
  )
}

