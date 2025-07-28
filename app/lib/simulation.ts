// 데이터 수요자, 가치평가 등 백엔드 로직 시뮬레이션

import { Bid, QualityReport, DataBuyer } from './types';

// 가상 데이터 수요자 목록
const DATA_BUYERS: DataBuyer[] = [
  {
    id: 'buyer_a',
    name: 'A 광고회사',
    industry: '광고/마케팅',
    budget: 50000,
    preferences: ['구매', '가격', '리뷰', '브랜드']
  },
  {
    id: 'buyer_b',
    name: 'B 마케팅',
    industry: '디지털마케팅',
    budget: 30000,
    preferences: ['트렌드', '소셜', '인플루언서', '콘텐츠']
  },
  {
    id: 'buyer_c',
    name: 'C 데이터랩',
    industry: '데이터분석',
    budget: 40000,
    preferences: ['통계', '분석', '리서치', '시장조사']
  }
];

// 상업적 가치 키워드 가중치
const COMMERCIAL_KEYWORDS = {
  '구매': 25,
  '가격': 20,
  '리뷰': 15,
  '브랜드': 15,
  '트렌드': 10,
  '소셜': 10,
  '인플루언서': 12,
  '콘텐츠': 8,
  '통계': 5,
  '분석': 5,
  '리서치': 8,
  '시장조사': 10,
  '마케팅': 15,
  '광고': 12,
  '판매': 18,
  '홍보': 10
};

/**
 * 검색어의 구체성에 따른 포인트 계산 (10-100점)
 */
export function calculateSearchSpecificity(query: string): number {
  // 기본 포인트
  let points = 10;
  
  // 검색어 길이에 따른 포인트 증가
  if (query.length >= 15) points += 40;
  else if (query.length >= 10) points += 30;
  else if (query.length >= 7) points += 20;
  else if (query.length >= 5) points += 15;
  else if (query.length >= 3) points += 10;
  
  // 숫자가 포함된 경우 (모델명, 연도 등) 포인트 대폭 증가
  if (/\d/.test(query)) {
    points += 25;
    // 연도가 포함된 경우 추가 포인트
    if (/\b(20\d{2}|19\d{2})\b/.test(query)) points += 10;
  }
  
  // 브랜드명 + 모델명 조합 (예: 아이폰16, 갤럭시S24)
  const brandModelPatterns = [
    /아이폰\s*\d+/i,
    /iphone\s*\d+/i,
    /갤럭시\s*[a-z]?\d+/i,
    /galaxy\s*[a-z]?\d+/i,
    /맥북\s*(프로|에어|미니)?/i,
    /macbook\s*(pro|air|mini)?/i,
    /삼성\s*노트북/i,
    /samsung\s*laptop/i
  ];
  
  if (brandModelPatterns.some(pattern => pattern.test(query))) {
    points += 30;
  }
  
  // 특정 키워드 조합
  const specificCombinations = [
    '아이폰16', 'iphone16', '갤럭시s24', 'galaxys24', '맥북프로', 'macbookpro',
    '삼성노트북', 'samsunglaptop', '아이패드', 'ipad', '에어팟', 'airpods'
  ];
  
  if (specificCombinations.some(combo => query.toLowerCase().includes(combo))) {
    points += 20;
  }
  
  // 최종 포인트 범위 제한 (10-100)
  return Math.max(10, Math.min(100, points));
}

/**
 * 포인트에 따른 품질 등급 반환
 */
export function getQualityGrade(points: number): string {
  if (points >= 80) return 'Excellent';
  if (points >= 60) return 'Very Good';
  if (points >= 40) return 'Good';
  if (points >= 20) return 'Fair';
  return 'Poor';
}

/**
 * 입력된 검색어를 기반으로 상업적 가치 점수와 품질 개선 제안을 반환
 */
export function evaluateDataValue(query: string): QualityReport {
  // 구체성 포인트 계산
  const specificityPoints = calculateSearchSpecificity(query);
  
  const lowerQuery = query.toLowerCase();
  let score = specificityPoints;
  const matchedKeywords: string[] = [];
  const suggestions: string[] = [];

  // 기존 키워드 매칭 및 점수 추가
  for (const [keyword, weight] of Object.entries(COMMERCIAL_KEYWORDS)) {
    if (lowerQuery.includes(keyword.toLowerCase())) {
      score += weight * 0.5; // 기존 키워드의 가중치를 절반으로 줄임
      matchedKeywords.push(keyword);
    }
  }

  // 최종 점수 범위 제한 (10-100)
  score = Math.max(10, Math.min(100, Math.floor(score)));

  // 상업적 가치 등급 결정
  let commercialValue: 'low' | 'medium' | 'high';
  if (score >= 70) {
    commercialValue = 'high';
  } else if (score >= 40) {
    commercialValue = 'medium';
  } else {
    commercialValue = 'low';
  }

  // 구체성에 따른 품질 개선 제안 생성
  if (score < 30) {
    suggestions.push('Add specific model numbers (e.g., iPhone 16, Galaxy S24)');
    suggestions.push('Include brand names and product categories');
  } else if (score < 60) {
    suggestions.push('Add more specific product details');
    suggestions.push('Include year or generation information');
  } else {
    suggestions.push('Excellent specificity! Your search has high commercial value');
    suggestions.push('Consider adding additional specifications for even higher value');
  }

  // 구체성 수준에 따른 추가 제안
  if (specificityPoints < 40) {
    suggestions.push('More specific searches earn higher points and better rewards');
  }

  return {
    score,
    suggestions,
    keywords: matchedKeywords,
    commercialValue
  };
}

/**
 * 가치 점수에 비례하여 가상 입찰 목록을 생성
 */
export function startReverseAuction(query: string, valueScore: number): Bid[] {
  const now = new Date();

  // '아이폰16' 특별 케이스 처리
  if (query.toLowerCase().includes('아이폰16') || query.toLowerCase().includes('iphone16')) {
    return [
      {
        id: 'bid-google',
        buyerName: 'Google',
        price: Math.floor(Math.random() * 901) + 100, // 100-1000원 사이 랜덤 금액
        bonus: '가장 빠른 최신 정보',
        timestamp: now,
        landingUrl: 'https://www.google.com/search?q=아이폰16',
      },
      {
        id: 'bid-naver',
        buyerName: '네이버',
        price: Math.floor(Math.random() * 901) + 100, // 100-1000원 사이 랜덤 금액
        bonus: '네이버쇼핑 최저가 비교',
        timestamp: now,
        landingUrl: 'https://search.naver.com/search.naver?query=아이폰16',
      },
      {
        id: 'bid-coupang',
        buyerName: '쿠팡',
        price: Math.floor(Math.random() * 901) + 100, // 100-1000원 사이 랜덤 금액
        bonus: '로켓배송으로 바로 받기',
        timestamp: now,
        landingUrl: 'https://www.coupang.com/np/search?q=아이폰16',
      },
      {
        id: 'bid-amazon',
        buyerName: 'Amazon',
        price: Math.floor(Math.random() * 901) + 100, // 100-1000원 사이 랜덤 금액
        bonus: '해외 직구 & 빠른 배송',
        timestamp: now,
        landingUrl: 'https://www.amazon.com/s?k=iphone+16',
      },
    ].sort((a, b) => b.price - a.price); // 가격 높은 순으로 정렬
  }

  // 기존의 일반 검색어 처리 로직
  const bids: Bid[] = [];
  DATA_BUYERS.forEach((buyer, index) => {
    // 100-1000원 사이 랜덤 가격 설정
    const price = Math.floor(Math.random() * 901) + 100;

    // 보너스 조건 생성
    const bonusConditions = generateBonusConditions(buyer, valueScore);

    // 고유 ID 생성
    const bidId = `bid_${buyer.id}_${Date.now()}_${index}`;

    // 각 플랫폼별 검색 URL 생성
    const searchUrls = {
      google: `https://www.google.com/search?q=${encodeURIComponent(query)}`,
      naver: `https://search.naver.com/search.naver?query=${encodeURIComponent(query)}`,
      coupang: `https://www.coupang.com/np/search?q=${encodeURIComponent(query)}`,
      amazon: `https://www.amazon.com/s?k=${encodeURIComponent(query)}`,
      gmarket: `https://browse.gmarket.co.kr/search?keyword=${encodeURIComponent(query)}`,
      elevenst: `https://www.11st.co.kr/search?keyword=${encodeURIComponent(query)}`
    };

    // 플랫폼별 입찰자 생성
    const platformBuyers = [
      { name: 'Google', url: searchUrls.google, bonus: '가장 빠른 최신 정보' },
      { name: '네이버', url: searchUrls.naver, bonus: '네이버쇼핑 최저가 비교' },
      { name: '쿠팡', url: searchUrls.coupang, bonus: '로켓배송으로 바로 받기' },
      { name: 'Amazon', url: searchUrls.amazon, bonus: '해외 직구 & 빠른 배송' },
      { name: 'G마켓', url: searchUrls.gmarket, bonus: 'G마켓 특가 상품' },
      { name: '11번가', url: searchUrls.elevenst, bonus: '11번가 할인 혜택' },
      { name: query, url: `https://www.google.com/search?q=${encodeURIComponent(query)}`, bonus: '직접 검색 결과' }
    ];

    // 기존 입찰자 정보와 플랫폼 정보 결합
    const platformBuyer = platformBuyers[index % platformBuyers.length];
    
    bids.push({
      id: bidId,
      buyerName: platformBuyer.name,
      price,
      bonus: platformBuyer.bonus,
      timestamp: now,
      landingUrl: platformBuyer.url
    });
  });

  // 가격순으로 정렬 (높은 가격이 먼저)
  return bids.sort((a, b) => b.price - a.price);
}

/**
 * 보너스 조건 생성
 */
function generateBonusConditions(buyer: DataBuyer, valueScore: number): string {
  const conditions = [];

  if (valueScore >= 80) {
    conditions.push('프리미엄 데이터 우선 제공');
  }
  
  if (valueScore >= 60) {
    conditions.push('추가 분석 리포트 제공');
  }

  switch (buyer.industry) {
    case '광고/마케팅':
      conditions.push('광고 효과 분석 포함');
      break;
    case '디지털마케팅':
      conditions.push('소셜미디어 인사이트 제공');
      break;
    case '데이터분석':
      conditions.push('상세 통계 분석 포함');
      break;
  }

  if (valueScore >= 70) {
    conditions.push('전용 대시보드 제공');
  }

  return conditions.length > 0 ? conditions.join(', ') : '기본 서비스';
}

/**
 * 랜덤 지연 시간 시뮬레이션 (실시간 경매 효과)
 */
export function simulateRealTimeDelay(): Promise<void> {
  const delay = Math.random() * 2000 + 500; // 0.5~2.5초 랜덤 지연
  return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * 경매 상태 업데이트 시뮬레이션
 */
export function simulateAuctionUpdate(auctionId: string): Promise<{ status: string; participants: number }> {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        status: 'active',
        participants: Math.floor(Math.random() * 10) + 1
      });
    }, Math.random() * 1000 + 500);
  });
}

// Dynamic Submission Limit Control System
export interface SubmissionLimit {
  level: 'Excellent' | 'Good' | 'Average' | 'Needs Improvement';
  dailyMax: number;
}

export const calculateDynamicLimit = (qualityScore: number): SubmissionLimit => {
  const baseLimit = 20; // Base daily limit
  
  if (qualityScore >= 90) {
    // 'Excellent' grade: 200% of base limit
    return { level: 'Excellent', dailyMax: baseLimit * 2 };
  } else if (qualityScore >= 70) {
    // 'Good' grade: Maintain base limit (100%)
    return { level: 'Good', dailyMax: baseLimit };
  } else if (qualityScore >= 50) {
    // 'Average' grade: 70% of base limit
    return { level: 'Average', dailyMax: Math.floor(baseLimit * 0.7) };
  } else {
    // 'Needs Improvement' grade: 30% of base limit
    return { level: 'Needs Improvement', dailyMax: Math.floor(baseLimit * 0.3) };
  }
};

// 가상 거래 내역 데이터베이스
import { Transaction } from './types';

export const mockTransactions: Transaction[] = [
  {
    id: 'txn_1001',
    query: '아이폰16',
    buyerName: '쿠팡',
    primaryReward: 175,
    status: '1차 완료',
    timestamp: '2025-07-20T09:10:00Z',
  },
  {
    id: 'txn_1002',
    query: '제주도 항공권',
    buyerName: '네이버',
    primaryReward: 250,
    status: '2차 완료',
    secondaryReward: 1250,
    timestamp: '2025-07-19T14:30:00Z',
  },
  {
    id: 'txn_1003',
    query: '나이키 운동화',
    buyerName: 'Google',
    primaryReward: 90,
    status: '검증 실패',
    timestamp: '2025-07-18T18:00:00Z',
  },
]; 