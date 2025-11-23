'use client'

import { useState, useEffect } from 'react'
import { X, Wallet, AlertCircle, TrendingUp, Target, CheckCircle, Loader2 } from 'lucide-react'

interface WithdrawalModalProps {
  isOpen: boolean
  onClose: () => void
  totalEarnings: number
  onSuccess?: () => void
}

const MIN_WITHDRAWAL_AMOUNT = 10000

export default function WithdrawalModal({ isOpen, onClose, totalEarnings, onSuccess }: WithdrawalModalProps) {
  const [requestAmount, setRequestAmount] = useState<number>(0)
  const [bankName, setBankName] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [accountHolder, setAccountHolder] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const canWithdraw = totalEarnings >= MIN_WITHDRAWAL_AMOUNT
  const remainingToGoal = Math.max(0, MIN_WITHDRAWAL_AMOUNT - totalEarnings)

  useEffect(() => {
    if (isOpen) {
      // Reset form when modal opens
      setRequestAmount(0)
      setBankName('')
      setAccountNumber('')
      setAccountHolder('')
      setError(null)
      setSuccess(false)
      // Set default amount to max if sufficient balance
      if (canWithdraw && totalEarnings >= MIN_WITHDRAWAL_AMOUNT) {
        setRequestAmount(Math.max(MIN_WITHDRAWAL_AMOUNT, totalEarnings))
      }
    }
  }, [isOpen, totalEarnings, canWithdraw])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    // Validation
    if (!canWithdraw) {
      setError(`최소 출금 금액은 ${MIN_WITHDRAWAL_AMOUNT.toLocaleString()} Points입니다.`)
      return
    }

    if (requestAmount < MIN_WITHDRAWAL_AMOUNT) {
      setError(`최소 출금 금액은 ${MIN_WITHDRAWAL_AMOUNT.toLocaleString()} Points입니다.`)
      return
    }

    if (requestAmount > totalEarnings) {
      setError('출금 금액이 잔액을 초과할 수 없습니다.')
      return
    }

    if (!bankName.trim() || !accountNumber.trim() || !accountHolder.trim()) {
      setError('모든 필드를 입력해주세요.')
      return
    }

    setIsSubmitting(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.')
      }

      const response = await fetch('/api/settlement/withdraw', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_amount: requestAmount,
          bank_name: bankName.trim(),
          account_number: accountNumber.trim(),
          account_holder: accountHolder.trim(),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.message || '출금 요청 처리 중 오류가 발생했습니다.')
      }

      setSuccess(true)
      setTimeout(() => {
        onSuccess?.()
        onClose()
      }, 2000)

    } catch (err) {
      setError(err instanceof Error ? err.message : '출금 요청 처리 중 오류가 발생했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 rounded-xl border border-slate-700 w-full max-w-md max-h-[90vh] overflow-y-auto m-4 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center space-x-3">
            <Wallet className="w-6 h-6 text-green-400" />
            <h2 className="text-xl font-bold text-slate-100">출금 요청</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
            aria-label="닫기"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Current Balance */}
          <div className="bg-gradient-to-r from-green-600/20 to-blue-600/20 rounded-lg p-4 border border-green-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">현재 잔액</p>
                <p className="text-2xl font-bold text-green-400">
                  {totalEarnings.toLocaleString()}P
                </p>
              </div>
              <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                <Wallet className="w-6 h-6 text-green-400" />
              </div>
            </div>
          </div>

          {/* Motivation Message (if insufficient balance) */}
          {!canWithdraw && (
            <div className="bg-gradient-to-r from-yellow-600/20 to-orange-600/20 rounded-lg p-5 border border-yellow-500/30">
              <div className="flex items-start space-x-3">
                <Target className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-yellow-400 mb-2">
                    출금까지 얼마 남지 않았어요! 💪
                  </h3>
                  <p className="text-slate-300 text-sm mb-3">
                    최소 출금 금액은 <span className="font-bold text-yellow-400">{MIN_WITHDRAWAL_AMOUNT.toLocaleString()} Points</span>입니다.
                  </p>
                  <div className="bg-slate-800/50 rounded-lg p-3 mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-slate-400 text-sm">목표까지 남은 금액</span>
                      <span className="text-xl font-bold text-yellow-400">
                        {remainingToGoal.toLocaleString()}P
                      </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full transition-all"
                        style={{
                          width: `${Math.min((totalEarnings / MIN_WITHDRAWAL_AMOUNT) * 100, 100)}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 mt-2 text-center">
                      {Math.round((totalEarnings / MIN_WITHDRAWAL_AMOUNT) * 100)}% 달성
                    </p>
                  </div>
                  <div className="flex items-start space-x-2 bg-slate-800/30 rounded-lg p-3">
                    <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-slate-200 font-medium mb-1">
                        조금만 더 활동하시면 출금할 수 있어요!
                      </p>
                      <p className="text-xs text-slate-400">
                        검색어를 더 많이 제출하거나 품질 점수를 높이면 더 빨리 목표에 도달할 수 있습니다.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <div>
                <p className="text-green-400 font-semibold">출금 요청이 접수되었습니다!</p>
                <p className="text-slate-300 text-sm mt-1">
                  처리 완료까지 약 1-2일이 소요됩니다.
                </p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Withdrawal Form (only show if can withdraw) */}
          {canWithdraw && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Amount Input */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  출금 금액
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min={MIN_WITHDRAWAL_AMOUNT}
                    max={totalEarnings}
                    value={requestAmount || ''}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 0
                      setRequestAmount(Math.min(Math.max(value, 0), totalEarnings))
                    }}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={`최소 ${MIN_WITHDRAWAL_AMOUNT.toLocaleString()} Points`}
                    disabled={isSubmitting}
                    required
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
                    P
                  </div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-slate-400">
                    최소: {MIN_WITHDRAWAL_AMOUNT.toLocaleString()}P
                  </p>
                  <button
                    type="button"
                    onClick={() => setRequestAmount(totalEarnings)}
                    className="text-xs text-blue-400 hover:text-blue-300 underline"
                    disabled={isSubmitting}
                  >
                    전체 출금
                  </button>
                </div>
              </div>

              {/* Bank Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  은행명
                </label>
                <input
                  type="text"
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="예: 카카오뱅크, 토스뱅크"
                  disabled={isSubmitting}
                  required
                />
              </div>

              {/* Account Number */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  계좌번호
                </label>
                <input
                  type="text"
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="계좌번호를 입력하세요"
                  disabled={isSubmitting}
                  required
                />
              </div>

              {/* Account Holder */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  예금주명
                </label>
                <input
                  type="text"
                  value={accountHolder}
                  onChange={(e) => setAccountHolder(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="예금주 실명을 입력하세요"
                  disabled={isSubmitting}
                  required
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>처리 중...</span>
                  </>
                ) : (
                  <>
                    <Wallet className="w-5 h-5" />
                    <span>출금 요청하기</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* Info Message */}
          <div className="bg-slate-800/50 rounded-lg p-4">
            <p className="text-xs text-slate-400 leading-relaxed">
              💡 출금 요청은 영업일 기준 1-2일 내에 처리됩니다. 처리 완료 시 등록하신 계좌로 입금됩니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

