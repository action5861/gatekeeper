// 가치 제안 카드 - 랜딩 하단 (개인정보 보호 강조 카드 포함)

'use client'

import { Calendar, Download, Layers, ShieldCheck } from 'lucide-react'

const cards = [
  {
    title: '검증된 성과만 거래',
    description:
      '의미없는 클릭이 아니라 실제 체류와 행동이 입증된 경우에만 보상이 발생합니다.',
    icon: Layers,
    highlight: false,
  },
  {
    title: '데이터 주권 회복',
    description:
      '몰래 추적하는 쿠키가 아닌, 사용자가 자발적으로 제공한 Zero-party Data만 거래합니다. 검색 의도의 가치를 직접 현금으로 받으세요.',
    icon: Calendar,
    highlight: false,
  },
  {
    title: '즉시 현금 인출',
    description:
      '거래가 완료되면 보상이 실시간으로 지갑에 적립됩니다. 1만원 이상 누적 시 즉시 현금 인출이 가능합니다.',
    icon: Download,
    highlight: false,
  },
  {
    title: '100% 개인정보 보호',
    description:
      '이름, 연락처, 주소 등 개인정보를 수집·저장하지 않습니다. 검색 의도만 익명으로 거래되며, 당신의 신원은 절대 노출되지 않습니다.',
    icon: ShieldCheck,
    highlight: true,
  },
]

export default function ValueCards() {
  return (
    <section className="w-full max-w-6xl mx-auto mt-12 md:mt-16">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
        {cards.map((card) => {
          const Icon = card.icon
          const isHighlight = card.highlight
          return (
            <div
              key={card.title}
              className={`rounded-xl p-6 md:p-8 border transition-all duration-300 hover:-translate-y-1 text-left ${isHighlight
                ? 'bg-emerald-500/10 border-emerald-500/50 hover:border-emerald-400/60 hover:shadow-xl hover:shadow-emerald-500/10 ring-2 ring-emerald-500/20'
                : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600 hover:shadow-xl hover:shadow-slate-900/50'
                }`}
            >
              <div
                className={`w-12 h-12 md:w-14 md:h-14 rounded-xl flex items-center justify-center mb-4 ${isHighlight
                  ? 'bg-emerald-500/30 ring-2 ring-emerald-400/40'
                  : 'bg-gradient-to-br from-[#64ffda] to-emerald-500'
                  }`}
              >
                <Icon className={`w-6 h-6 md:w-7 md:h-7 ${isHighlight ? 'text-emerald-300' : 'text-slate-900'}`} strokeWidth={2} />
              </div>
              <h3 className={`text-lg md:text-xl font-bold mb-3 break-keep ${isHighlight ? 'text-emerald-200' : 'text-white'}`}>
                {card.title}
              </h3>
              <p className="text-sm md:text-base leading-relaxed break-keep text-slate-400">
                {card.description}
              </p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
