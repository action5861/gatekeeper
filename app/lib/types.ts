// 전역 타입 정의

// 입찰 정보를 담는 타입
export interface Bid {
  id: string;
  buyerName: string;
  price: number;
  bonus: string;
  timestamp: Date;
  landingUrl: string; // 클릭 시 이동할 외부 사이트 주소
  clickUrl: string; // 리다이렉트를 위한 서명된 URL
}

// 경매 정보를 담는 타입
export interface Auction {
  searchId: string;
  query: string;
  bids: Bid[];
  status: 'active' | 'completed' | 'cancelled';
  createdAt: Date;
  expiresAt: Date;
}

// AI가 제안한 개선된 검색어
export interface ImprovedQuery {
  query: string;
  reason: string;
  score?: number;
  commercialValue?: 'low' | 'medium' | 'high';
}

// 품질 분석 리포트 타입
export interface QualityReport {
  score: number;
  suggestions: string[];
  keywords: string[];
  commercialValue: 'low' | 'medium' | 'high';
  needsImprovement?: boolean;  // ⭐ 개선 필요 플래그
  aiSuggestions?: ImprovedQuery[];  // ⭐ AI 개선 제안
}

// 데이터 수요자 타입
export interface DataBuyer {
  id: string;
  name: string;
  industry: string;
  budget: number;
  preferences: string[];
}

// 사용자 정보 타입
export interface User {
  id: string;
  name: string;
  totalEarnings: number;
  qualityScore: number;
  completedAuctions: number;
  badges: string[];
}

// API 응답 타입
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 거래 내역 상태 타입
export type TransactionStatus = '1차 완료' | '검증 대기중' | '2차 완료' | '검증 실패';

// 거래 내역 타입
export interface Transaction {
  id: string;
  query: string;
  buyerName: string;
  primaryReward: number;
  secondaryReward?: number;
  status: TransactionStatus;
  timestamp: string;
} 