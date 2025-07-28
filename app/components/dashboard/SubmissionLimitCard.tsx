// 제출 한도 표시 카드

'use client'

import { FileCheck2, AlertCircle, TrendingUp } from 'lucide-react'

interface Props {
  limitData: {
    level: 'Excellent' | 'Good' | 'Average' | 'Needs Improvement';
    dailyMax: number;
  };
}

const levelStyles = {
  'Excellent': 'bg-blue-500 text-white',
  'Good': 'bg-green-500 text-white',
  'Average': 'bg-yellow-500 text-black',
  'Needs Improvement': 'bg-red-500 text-white',
};

const levelDescriptions = {
  'Excellent': 'Excellent quality - 200% daily limit',
  'Good': 'Good quality - Standard daily limit',
  'Average': 'Average quality - 70% daily limit',
  'Needs Improvement': 'Needs improvement - 30% daily limit',
};

export default function SubmissionLimitCard({ limitData }: Props) {
  if (!limitData) return null;

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'Excellent':
        return <TrendingUp className="w-5 h-5" />;
      case 'Good':
        return <FileCheck2 className="w-5 h-5" />;
      case 'Average':
        return <AlertCircle className="w-5 h-5" />;
      case 'Needs Improvement':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <FileCheck2 className="w-5 h-5" />;
    }
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
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-slate-300">Today's Usage</span>
          <span className="text-sm text-slate-400">8 / {limitData.dailyMax}</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.min((8 / limitData.dailyMax) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Tips */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-slate-100 mb-3">Tips to Increase Limit</h4>
        <ul className="space-y-2 text-sm text-slate-300">
          <li className="flex items-start space-x-2">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
            <span>Include commercial keywords in your searches</span>
          </li>
          <li className="flex items-start space-x-2">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
            <span>Maintain consistent search quality</span>
          </li>
          <li className="flex items-start space-x-2">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
            <span>Complete verification processes promptly</span>
          </li>
        </ul>
      </div>
    </div>
  )
} 