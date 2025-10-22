'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { useAnalysisStatus } from '@/lib/hooks/useAnalysisStatus';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';

export function AnalysisStatusBanner() {
    const { data, isLoading, error } = useAnalysisStatus();

    // 로딩 중이거나 에러가 있으면 배너를 표시하지 않음
    if (isLoading) return null;
    if (error || !data) return null;

    // AI 분석 진행 중
    if (data.approval_status === 'pending_analysis') {
        return (
            <div className="mb-6 animate-pulse">
                <Alert variant="default" className="border-blue-300 bg-blue-50">
                    <div className="flex items-start gap-3">
                        <Loader2 className="h-5 w-5 animate-spin text-blue-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                            <AlertTitle className="text-blue-900 font-semibold">
                                🤖 AI 분석 진행 중
                            </AlertTitle>
                            <AlertDescription className="text-blue-800 mt-1">
                                웹사이트를 분석하여 최적의 광고 설정을 생성하고 있습니다.
                                잠시 후 페이지가 자동으로 업데이트됩니다.
                            </AlertDescription>
                            {data.website_url && (
                                <p className="text-xs text-blue-600 mt-2">
                                    분석 중인 사이트: {data.website_url}
                                </p>
                            )}
                        </div>
                    </div>
                </Alert>
            </div>
        );
    }

    // AI 분석 완료 (심사 대기)
    if (data.approval_status === 'pending' && data.website_analysis) {
        return (
            <div className="mb-6">
                <Alert variant="success" className="border-green-300 bg-green-50">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                            <AlertTitle className="text-green-900 font-semibold">
                                ✨ AI 분석 완료!
                            </AlertTitle>
                            <AlertDescription className="text-green-800 mt-1">
                                AI가 추천하는 광고 설정을 확인하고 비즈니스를 시작하세요.
                                <Link
                                    href="/advertiser/review-suggestions"
                                    className="font-bold underline ml-2 hover:text-green-900 transition-colors"
                                >
                                    지금 확인하기 →
                                </Link>
                            </AlertDescription>
                            {data.website_analysis && (
                                <div className="mt-3 p-3 bg-white/50 rounded-lg border border-green-200">
                                    <p className="text-sm text-green-900">
                                        <strong>AI 분석 요약:</strong> {data.website_analysis}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </Alert>
            </div>
        );
    }

    // 승인됨
    if (data.approval_status === 'approved') {
        return null; // 승인된 경우 배너 표시 안 함
    }

    // 거절됨
    if (data.approval_status === 'rejected') {
        return (
            <div className="mb-6">
                <Alert variant="destructive" className="border-red-300 bg-red-50">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                            <AlertTitle className="text-red-900 font-semibold">
                                심사 거절
                            </AlertTitle>
                            <AlertDescription className="text-red-800 mt-1">
                                광고주 신청이 거절되었습니다. 자세한 내용은 고객 지원팀에 문의하세요.
                            </AlertDescription>
                        </div>
                    </div>
                </Alert>
            </div>
        );
    }

    return null;
}

