'use client';

import { Transaction, TransactionStatus } from '@/lib/types';
import { CheckCircle, Clock, FileText, Loader2, RefreshCw, UploadCloud, XCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface Props {
  initialTransactions: Transaction[];
}

const statusStyles = {
  '1차 완료': 'bg-slate-500 text-slate-100',
  '검증 대기중': 'bg-yellow-500 text-yellow-100 animate-pulse',
  '2차 완료': 'bg-green-500 text-green-100',
  '검증 실패': 'bg-red-500 text-red-100',
  'PENDING_VERIFICATION': 'bg-yellow-600 text-yellow-100 animate-pulse',
  'SETTLED': 'bg-green-600 text-green-100',
  'FAILED': 'bg-red-600 text-red-100',
};

const statusLabels = {
  '1차 완료': 'Primary Completed',
  '검증 대기중': 'Verification Pending',
  '2차 완료': 'Secondary Completed',
  '검증 실패': 'Verification Failed',
  'PENDING_VERIFICATION': 'SLA Verification Pending',
  'SETTLED': 'Settled',
  'FAILED': 'Failed',
};

export function TransactionHistory({ initialTransactions }: Props) {
  const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions);
  const [selectedTxnId, setSelectedTxnId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 거래 내역 새로고침 함수
  const refreshTransactions = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch('/api/user/dashboard');
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.transactions || []);
      }
    } catch (error) {
      console.error('Failed to refresh transactions:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // 보상 업데이트 이벤트 리스너
  useEffect(() => {
    const handleRewardUpdate = () => {
      refreshTransactions();
    };

    window.addEventListener('reward-updated', handleRewardUpdate);
    return () => {
      window.removeEventListener('reward-updated', handleRewardUpdate);
    };
  }, []);

  // 초기 거래 내역이 변경되면 업데이트
  useEffect(() => {
    setTransactions(initialTransactions);
  }, [initialTransactions]);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedTxnId) return;

    // 상태를 '검증 대기중'으로 변경
    setTransactions(prev =>
      prev.map(t => (t.id === selectedTxnId ? { ...t, status: '검증 대기중' } : t))
    );

    const formData = new FormData();
    formData.append('transactionId', selectedTxnId);
    formData.append('proof', file);

    try {
      const response = await fetch('/api/rewards/claim', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();

      // 결과에 따라 상태 업데이트
      setTransactions(prev =>
        prev.map(t =>
          t.id === selectedTxnId
            ? { ...t, status: result.status, secondaryReward: result.secondaryReward }
            : t
        )
      );

      // 성공 시 알림
      if (result.status === '2차 완료') {
        alert(`Secondary reward claimed successfully! +${result.secondaryReward?.toLocaleString()}원`);
      } else if (result.status === '검증 실패') {
        alert('Verification failed. Please try again with different proof.');
      }
    } catch (error) {
      console.error('Secondary reward request failed:', error);
      // 에러 시 원래 상태로 복원
      setTransactions(prev =>
        prev.map(t => (t.id === selectedTxnId ? { ...t, status: '1차 완료' } : t))
      );
      alert('Failed to submit proof. Please try again.');
    }

    setSelectedTxnId(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClaimClick = (transactionId: string) => {
    setSelectedTxnId(transactionId);
    fileInputRef.current?.click();
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status: TransactionStatus) => {
    switch (status) {
      case '2차 완료':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case '검증 실패':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case '검증 대기중':
        return <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-slate-100 flex items-center space-x-2">
          <FileText className="w-6 h-6 text-blue-400" />
          <span>Transaction History</span>
        </h2>
        <button
          onClick={refreshTransactions}
          disabled={isRefreshing}
          className="flex items-center space-x-2 px-3 py-1 bg-slate-700 text-slate-300 text-sm rounded-md hover:bg-slate-600 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-600">
              <th className="text-left py-3 px-3 font-medium text-slate-300">Search Query</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Buyer</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Primary Reward</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Secondary Reward</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Status</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Date</th>
              <th className="text-left py-3 px-3 font-medium text-slate-300">Action</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id} className="border-b border-slate-700 hover:bg-slate-700/30 transition-colors">
                <td className="py-3 px-3 text-slate-100 font-medium">
                  {transaction.query}
                </td>
                <td className="py-3 px-3 text-slate-300">
                  {transaction.buyerName}
                </td>
                <td className="py-3 px-3 text-green-400 font-semibold">
                  {transaction.primaryReward.toLocaleString()}원
                </td>
                <td className="py-3 px-3 text-blue-400 font-semibold">
                  {transaction.secondaryReward
                    ? `${transaction.secondaryReward.toLocaleString()}원`
                    : '-'
                  }
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusStyles[transaction.status]}`}>
                      {statusLabels[transaction.status]}
                    </span>
                    {getStatusIcon(transaction.status)}
                  </div>
                </td>
                <td className="py-3 px-3 text-slate-400 text-xs">
                  {formatDate(transaction.timestamp)}
                </td>
                <td className="py-3 px-3">
                  {transaction.status === '1차 완료' && (
                    <button
                      onClick={() => handleClaimClick(transaction.id)}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600 transition-colors"
                    >
                      <UploadCloud className="w-3 h-3" />
                      Submit Proof
                    </button>
                  )}
                  {transaction.status === '검증 대기중' && (
                    <span className="text-yellow-400 text-xs flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Verifying...
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 숨겨진 파일 입력 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf"
        onChange={handleFileSelect}
        className="hidden"
      />

      {transactions.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <p className="text-lg font-medium">No transactions yet</p>
          <p className="text-sm">Complete your first search to see transaction history</p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-slate-600">
        <h4 className="text-lg font-semibold text-slate-100 mb-4">Transaction Summary</h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-700/30 rounded-lg p-3">
            <p className="text-slate-400 text-xs">Total Transactions</p>
            <p className="text-xl font-bold text-slate-100">{transactions.length}</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-3">
            <p className="text-slate-400 text-xs">Completed Secondary</p>
            <p className="text-xl font-bold text-green-400">
              {transactions.filter(t => t.status === '2차 완료').length}
            </p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-3">
            <p className="text-slate-400 text-xs">Pending Verification</p>
            <p className="text-xl font-bold text-yellow-400">
              {transactions.filter(t => t.status === '검증 대기중').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 