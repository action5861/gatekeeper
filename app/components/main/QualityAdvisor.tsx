// 실시간 품질 점수 및 개선 제안

'use client'

import { getQualityGrade } from '@/lib/simulation'
import { QualityReport } from '@/lib/types'
import { AlertCircle, ArrowRight, CheckCircle, Lightbulb, Sparkles, TrendingUp } from 'lucide-react'
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'

interface QualityAdvisorProps {
  qualityReport: QualityReport | null
  onQueryReplace?: (newQuery: string) => void  // ⭐ 검색어 교체 콜백
}

export default function QualityAdvisor({ qualityReport, onQueryReplace }: QualityAdvisorProps) {
  if (!qualityReport) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeIn">
        <h3 className="text-2xl font-semibold mb-4 text-slate-100 flex items-center space-x-2">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <span>Quality Assessment</span>
        </h3>
        <div className="text-center py-8">
          <p className="text-slate-400">Enter a search query to see quality assessment</p>
        </div>
      </div>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10B981' // green
    if (score >= 60) return '#F59E0B' // yellow
    if (score >= 40) return '#F97316' // orange
    return '#EF4444' // red
  }

  // 원형 차트 데이터 생성
  const chartData = [
    { name: 'Score', value: qualityReport.score, color: getScoreColor(qualityReport.score) },
    { name: 'Remaining', value: 100 - qualityReport.score, color: '#374151' }
  ]

  const getScoreLabel = (score: number) => {
    return getQualityGrade(score)
  }

  const getCommercialValueColor = (value: string) => {
    switch (value) {
      case 'high': return 'text-green-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-fadeInUp">
      <h3 className="text-2xl font-semibold mb-6 text-slate-100 flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Quality Assessment</span>
      </h3>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Score Chart */}
        <div className="flex flex-col items-center space-y-4">
          <div className="relative w-32 h-32">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={60}
                  paddingAngle={0}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-3xl font-bold text-slate-100">{qualityReport.score}</div>
                <div className="text-sm text-slate-400">points</div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className={`text-lg font-semibold ${getScoreColor(qualityReport.score)}`}>
              {getScoreLabel(qualityReport.score)}
            </div>
            <div className={`text-sm ${getCommercialValueColor(qualityReport.commercialValue)}`}>
              Commercial Value: {qualityReport.commercialValue.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Suggestions */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-slate-100 flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span>Improvement Suggestions</span>
          </h4>

          {qualityReport.suggestions.length > 0 ? (
            <ul className="space-y-3">
              {qualityReport.suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start space-x-3 p-3 bg-slate-700/30 rounded-lg">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                  <span className="text-slate-300 text-sm leading-relaxed">{suggestion}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-4">
              <AlertCircle className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-slate-400 text-sm">No suggestions available</p>
            </div>
          )}

          {/* Keywords */}
          {qualityReport.keywords.length > 0 && (
            <div className="mt-4">
              <h5 className="text-sm font-medium text-slate-300 mb-2">Detected Keywords:</h5>
              <div className="flex flex-wrap gap-2">
                {qualityReport.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-600/20 text-blue-300 text-xs rounded-md border border-blue-600/30"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ⭐ AI 개선 제안 (30점 미만 또는 low 값인 경우) */}
      {qualityReport.needsImprovement && qualityReport.aiSuggestions && qualityReport.aiSuggestions.length > 0 && (
        <div className="mt-6 p-6 bg-gradient-to-r from-amber-900/20 to-orange-900/20 rounded-xl border border-amber-600/30 animate-fadeInUp">
          <div className="flex items-center space-x-2 mb-4">
            <Lightbulb className="w-6 h-6 text-amber-400" />
            <h4 className="text-xl font-semibold text-amber-400">
              AI가 더 나은 검색어를 추천합니다
            </h4>
          </div>

          <p className="text-slate-300 mb-4 text-sm">
            ⚠️ 현재 검색어는 광고주 관심도가 낮아 보상이 적을 수 있습니다.
            아래 검색어를 클릭하면 자동으로 교체됩니다.
          </p>

          <div className="space-y-3">
            {qualityReport.aiSuggestions.map((suggestion, index) => {
              const scoreImprovement = suggestion.score ? suggestion.score - qualityReport.score : 0;
              const isRecommended = suggestion.score && suggestion.score >= 75;

              return (
                <button
                  key={index}
                  onClick={() => onQueryReplace && onQueryReplace(suggestion.query)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 hover:scale-102 hover:shadow-lg ${isRecommended
                      ? 'bg-gradient-to-r from-green-900/30 to-emerald-900/30 border-green-500/50 hover:border-green-400'
                      : 'bg-slate-800/50 border-slate-600 hover:border-blue-500'
                    }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {isRecommended && (
                          <Sparkles className="w-4 h-4 text-green-400" />
                        )}
                        <span className={`font-semibold ${isRecommended ? 'text-green-400' : 'text-blue-400'}`}>
                          {suggestion.query}
                        </span>
                        {isRecommended && (
                          <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                            추천
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-4 text-sm">
                        {suggestion.score && (
                          <span className="text-slate-300">
                            점수: <span className="font-semibold text-white">{suggestion.score}</span>/100
                            {scoreImprovement > 0 && (
                              <span className="text-green-400 ml-1">
                                (+{scoreImprovement}점 ⬆️)
                              </span>
                            )}
                          </span>
                        )}
                        {suggestion.commercialValue && (
                          <span className={`${getCommercialValueColor(suggestion.commercialValue)}`}>
                            {suggestion.commercialValue.toUpperCase()}
                          </span>
                        )}
                      </div>

                      <p className="text-slate-400 text-xs mt-1">
                        💡 {suggestion.reason}
                      </p>
                    </div>

                    <ArrowRight className="w-5 h-5 text-slate-400 mt-1 ml-2 flex-shrink-0" />
                  </div>
                </button>
              );
            })}
          </div>

          <p className="text-xs text-slate-500 mt-4 text-center">
            💡 팁: 개선된 검색어를 사용하면 더 많은 광고주가 입찰하여 더 높은 보상을 받을 수 있습니다!
          </p>
        </div>
      )}
    </div>
  )
} 