'use client'

import { useEffect } from 'react'
import { X, Gift, CheckCircle } from 'lucide-react'

interface RewardModalProps {
  isOpen: boolean
  onClose: () => void
  amount: number
  message?: string
}

export default function RewardModal({ isOpen, onClose, amount, message }: RewardModalProps) {
  useEffect(() => {
    if (isOpen) {
      // 3초 후 자동으로 닫기
      const timer = setTimeout(() => {
        onClose()
      }, 3000)

      return () => clearTimeout(timer)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4 border border-slate-700 animate-fadeInUp">
        <div className="text-center">
          {/* Success Icon */}
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          
          {/* Title */}
          <h3 className="text-xl font-bold text-slate-100 mb-2">
            🎉 즉시보상 지급완료!
          </h3>
          
          {/* Amount */}
          <div className="text-3xl font-bold text-green-400 mb-4">
            {amount.toLocaleString()}원
          </div>
          
          {/* Message */}
          <p className="text-slate-300 mb-6">
            {message || `1차로 ${amount}원 즉시보상이 지급되었습니다!`}
          </p>
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="px-6 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors duration-200 flex items-center space-x-2 mx-auto"
          >
            <X className="w-4 h-4" />
            <span>닫기</span>
          </button>
        </div>
      </div>
    </div>
  )
} 