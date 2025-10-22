'use client'

import { authenticatedFetch } from '@/lib/auth';
import { useQuery } from '@tanstack/react-query';

export interface AnalysisStatus {
    approval_status: 'pending_analysis' | 'pending' | 'approved' | 'rejected';
    review_status: string | null;
    website_analysis: string | null;
    website_url: string | null;
    created_at: string | null;
}

const fetchAnalysisStatus = async (): Promise<AnalysisStatus> => {
    const response = await authenticatedFetch('/api/advertiser/status');
    if (!response.ok) {
        throw new Error('Failed to fetch analysis status');
    }
    return response.json();
};

export const useAnalysisStatus = () => {
    return useQuery<AnalysisStatus>({
        queryKey: ['analysisStatus'],
        queryFn: fetchAnalysisStatus,
        // 3초마다 상태를 다시 가져옴
        refetchInterval: (query) => {
            // 상태가 'pending_analysis'일 때만 폴링 계속
            const isPendingAnalysis = query.state.data?.approval_status === 'pending_analysis';
            return isPendingAnalysis ? 3000 : false;
        },
        // 백그라운드에서도 계속 폴링
        refetchIntervalInBackground: true,
        // 컴포넌트가 mount될 때 자동으로 fetch
        refetchOnMount: true,
        // 윈도우 포커스 시 refetch
        refetchOnWindowFocus: true,
        // 30초 동안 fresh 상태 유지
        staleTime: 30000,
    });
};

