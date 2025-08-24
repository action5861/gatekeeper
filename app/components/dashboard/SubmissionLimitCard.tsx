// 제출 한도 표시 카드

'use client'

import { ErrorFallback } from '@/components/ui/ErrorFallback';
import { SubmissionLimitSkeleton } from '@/components/ui/Skeleton';
import { useSubmissionData } from '@/lib/hooks/useDashboardData';
import { logComponentError } from '@/lib/utils/errorMonitor';
import { AlertCircle, FileCheck2, Target, TrendingUp } from 'lucide-react';

interface SubmissionLimitData {
  level: 'Excellent' | 'Very Good' | 'Good' | 'Average' | 'Below Average' | 'Poor' | 'Very Poor';
  dailyMax: number;
}

interface DailySubmissionData {
  count: number;
  limit: number;
  remaining: number;
  qualityScoreAvg: number;
}

const levelStyles = {
  'Excellent': 'bg-blue-500 text-white',
  'Very Good': 'bg-green-600 text-white',
  'Good': 'bg-green-500 text-white',
  'Average': 'bg-yellow-500 text-black',
  'Below Average': 'bg-orange-500 text-white',
  'Poor': 'bg-red-500 text-white',
  'Very Poor': 'bg-red-600 text-white',
};

const levelDescriptions = {
  'Excellent': 'Excellent quality - 300% daily limit (15 submissions)',
  'Very Good': 'Very good quality - 200% daily limit (10 submissions)',
  'Good': 'Good quality - 160% daily limit (8 submissions)',
  'Average': 'Average quality - 120% daily limit (6 submissions)',
  'Below Average': 'Below average quality - 100% daily limit (5 submissions)',
  'Poor': 'Poor quality - 60% daily limit (3 submissions)',
  'Very Poor': 'Very poor quality - 40% daily limit (2 submissions)',
};

export default function SubmissionLimitCard() {
  const { submissionLimit: limitData, dailySubmission, isLoading, error, refetch } = useSubmissionData();

  // 에러 처리
  if (error) {
    logComponentError(
      error instanceof Error ? error : new Error(error.toString()),
      'SubmissionLimitCard',
      undefined,
      { limitData, dailySubmission }
    );
  }

  // 로딩 상태
  if (isLoading) {
    return <SubmissionLimitSkeleton />;
  }

  // 에러 상태
  if (error) {
    return (
      <ErrorFallback
        error={error}
        componentName="Submission Limit"
        onRetry={refetch}
      />
    );
  }

  // 데이터가 없는 경우
  if (!limitData) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center space-y-4">
            <FileCheck2 className="w-8 h-8 text-slate-400" />
            <p className="text-slate-400">제출 한도 데이터가 없습니다</p>
          </div>
        </div>
      </div>
    )
  }

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'Excellent':
        return <TrendingUp className="w-5 h-5" />;
      case 'Very Good':
        return <TrendingUp className="w-5 h-5" />;
      case 'Good':
        return <FileCheck2 className="w-5 h-5" />;
      case 'Average':
        return <AlertCircle className="w-5 h-5" />;
      case 'Below Average':
        return <AlertCircle className="w-5 h-5" />;
      case 'Poor':
        return <AlertCircle className="w-5 h-5" />;
      case 'Very Poor':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <FileCheck2 className="w-5 h-5" />;
    }
  };

  // 사용률 계산
  const usagePercentage = dailySubmission ? (dailySubmission.count / dailySubmission.limit) * 100 : 0;
  const isNearLimit = usagePercentage >= 80;
  const isAtLimit = usagePercentage >= 100;

  // 개인화된 팁 생성
  const getPersonalizedTips = () => {
    const tips = [];

    if (dailySubmission) {
      if (dailySubmission.qualityScoreAvg < 70) {
        tips.push("품질 점수를 70점 이상으로 높이면 한도가 증가합니다");
      }
      if (dailySubmission.count < 5) {
        tips.push("더 많은 검색어를 제출하여 경험을 쌓아보세요");
      }
      if (isNearLimit) {
        tips.push("오늘 한도에 거의 도달했습니다. 내일 다시 시도해보세요");
      }
    }

    // 기본 팁
    if (tips.length === 0) {
      tips.push("상업적 키워드를 포함한 검색어를 작성하세요");
      tips.push("일관된 검색 품질을 유지하세요");
      tips.push("검증 과정을 신속하게 완료하세요");
    }

    return tips;
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <FileCheck2 className="w-6 h-6 text-purple-400" />
        <span>Daily Submission Limit</span>
      </h3>

      {/* Level Badge */}
      <div className="mb-6">
        <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full ${levelStyles[limitData.level]}`}>
          {getLevelIcon(limitData.level)}
          <span className="font-semibold">{limitData.level}</span>
        </div>
        <p className="text-sm text-slate-400 mt-2">
          {levelDescriptions[limitData.level]}
        </p>
      </div>

      {/* Limit Display */}
      <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-lg p-4 border border-purple-500/30 mb-6">
        <div className="text-center">
          <p className="text-slate-400 text-sm mb-1">Daily Maximum</p>
          <p className="text-4xl font-bold text-purple-400">
            {limitData.dailyMax}
          </p>
          <p className="text-slate-300 text-sm">submissions per day</p>
        </div>
      </div>

      {/* Progress Bar */}
      {dailySubmission && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-300">Today's Usage</span>
            <span className={`text-sm ${isAtLimit ? 'text-red-400' : isNearLimit ? 'text-yellow-400' : 'text-slate-400'}`}>
              {dailySubmission.count} / {dailySubmission.limit}
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${isAtLimit
                ? 'bg-red-500'
                : isNearLimit
                  ? 'bg-yellow-500'
                  : 'bg-gradient-to-r from-purple-500 to-blue-500'
                }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            ></div>
          </div>
          {dailySubmission.remaining > 0 && (
            <p className="text-xs text-slate-400 mt-1">
              {dailySubmission.remaining} submissions remaining today
            </p>
          )}
        </div>
      )}

      {/* Quality Score Display */}
      {dailySubmission && (
        <div className="mb-6 bg-slate-700/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-slate-300">Today's Avg Quality</span>
            </div>
            <span className={`font-semibold ${dailySubmission.qualityScoreAvg >= 90 ? 'text-blue-400' :
              dailySubmission.qualityScoreAvg >= 70 ? 'text-green-400' :
                dailySubmission.qualityScoreAvg >= 50 ? 'text-yellow-400' : 'text-red-400'
              }`}>
              {dailySubmission.qualityScoreAvg}점
            </span>
          </div>
        </div>
      )}

      {/* Personalized Tips */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-slate-100 mb-3 flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-blue-400" />
          <span>Personalized Tips</span>
        </h4>
        <ul className="space-y-2 text-sm text-slate-300">
          {getPersonalizedTips().map((tip, index) => (
            <li key={index} className="flex items-start space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
} 