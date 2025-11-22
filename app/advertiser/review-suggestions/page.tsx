'use client';

import Header from '@/components/Header';
import { authenticatedFetch } from '@/lib/auth';
import { useAnalysisStatus } from '@/lib/hooks/useAnalysisStatus';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Check, ChevronDown, ChevronUp, Loader2, Plus, Sparkles, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface Keyword {
    id: number;
    keyword: string;
    priority: number;
    match_type: string;
}

interface Category {
    id: number;
    category_path: string;
    category_level: number;
    is_primary: boolean;
}

interface AISuggestions {
    keywords: Keyword[];
    categories: Category[];
}

const fetchAISuggestions = async (): Promise<AISuggestions> => {
    const response = await authenticatedFetch('/api/advertiser/ai-suggestions');
    if (!response.ok) {
        throw new Error('Failed to fetch AI suggestions');
    }
    return response.json();
};

export default function ReviewSuggestionsPage() {
    const router = useRouter();
    const queryClient = useQueryClient();

    const [keywords, setKeywords] = useState<Keyword[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [showAnalysisSummary, setShowAnalysisSummary] = useState(false);

    // 분석 상태 확인
    const { data: analysisStatus, isLoading: isStatusLoading } = useAnalysisStatus();
    
    // 분석이 완료되었는지 확인 (pending 상태이고 website_analysis가 있으면 완료)
    const isAnalysisComplete = analysisStatus && 
        analysisStatus.approval_status === 'pending' && 
        analysisStatus.website_analysis !== null;

    // AI 제안 데이터 fetch - 분석이 완료되었을 때만 활성화하고, 완료되지 않았으면 주기적으로 재시도
    const { data, isLoading, error } = useQuery<AISuggestions>({
        queryKey: ['aiSuggestions'],
        queryFn: fetchAISuggestions,
        enabled: analysisStatus !== undefined && analysisStatus.approval_status !== 'pending_analysis', // 분석이 진행 중이 아닐 때만 활성화
        refetchInterval: (query) => {
            // 분석이 완료되지 않았거나 데이터가 없으면 3초마다 재시도
            const hasData = query.state.data && 
                (query.state.data.keywords.length > 0 || query.state.data.categories.length > 0);
            
            // 분석이 진행 중이 아니고 데이터가 없으면 재시도
            if (!isAnalysisComplete && !hasData) {
                return 3000;
            }
            // 분석이 완료되었지만 데이터가 아직 없으면 재시도
            if (isAnalysisComplete && !hasData) {
                return 3000;
            }
            return false;
        },
        refetchIntervalInBackground: true,
        refetchOnMount: true,
        refetchOnWindowFocus: true,
        retry: 3, // 최대 3번 재시도
        retryDelay: 2000, // 2초 간격으로 재시도
    });

    useEffect(() => {
        if (data) {
            setKeywords(data.keywords);
            setCategories(data.categories);
        }
    }, [data]);

    // 분석이 완료되면 AI 제안 쿼리 무효화하여 다시 가져오기
    useEffect(() => {
        if (isAnalysisComplete) {
            queryClient.invalidateQueries({ queryKey: ['aiSuggestions'] });
        }
    }, [isAnalysisComplete, queryClient]);

    // 키워드 추가
    const handleAddKeyword = () => {
        const trimmed = newKeyword.trim();
        if (!trimmed) return;

        // 중복 확인
        if (keywords.some(k => k.keyword.toLowerCase() === trimmed.toLowerCase())) {
            alert('이미 추가된 키워드입니다');
            return;
        }

        const newKw: Keyword = {
            id: Date.now(), // 임시 ID
            keyword: trimmed,
            priority: 1,
            match_type: 'broad',
        };

        setKeywords([...keywords, newKw]);
        setNewKeyword('');
    };

    // 키워드 삭제
    const handleRemoveKeyword = (id: number) => {
        setKeywords(keywords.filter(k => k.id !== id));
    };

    // 카테고리 토글
    const handleCategoryToggle = (id: number) => {
        setCategories(categories.map(cat =>
            cat.id === id ? { ...cat, is_primary: !cat.is_primary } : cat
        ));
    };

    // 최종 확정 뮤테이션
    const mutation = useMutation({
        mutationFn: async (payload: { keywords: Keyword[]; categories: Category[] }) => {
            const response = await authenticatedFetch('/api/advertiser/confirm-suggestions', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                throw new Error('Failed to confirm suggestions');
            }
            return response.json();
        },
        onSuccess: () => {
            // 상태 쿼리 무효화하여 대시보드에서 배너 업데이트
            queryClient.invalidateQueries({ queryKey: ['analysisStatus'] });
            // 대시보드로 이동
            router.push('/advertiser/dashboard');
        },
        onError: (error) => {
            console.error('Confirm error:', error);
            alert('설정 확정 중 오류가 발생했습니다');
        },
    });

    const handleSubmit = () => {
        if (keywords.length === 0) {
            alert('최소 1개의 키워드를 추가해주세요');
            return;
        }
        if (categories.length === 0) {
            alert('최소 1개의 카테고리를 선택해주세요');
            return;
        }
        mutation.mutate({ keywords, categories });
    };

    // 분석 상태 로딩 중
    if (isStatusLoading) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
                            <p className="text-slate-300">분석 상태를 확인하는 중...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    // AI 분석 진행 중인 경우 - 분석 진행 화면 표시
    if (analysisStatus && analysisStatus.approval_status === 'pending_analysis') {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 mb-4">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-4xl font-bold text-slate-100 mb-3">
                            AI 분석 진행 중
                        </h1>
                        <p className="text-xl text-slate-400">
                            웹사이트를 분석하여 최적의 광고 설정을 생성하고 있습니다
                        </p>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 mb-6">
                        <div className="flex flex-col items-center justify-center py-12">
                            <Loader2 className="w-16 h-16 animate-spin text-blue-400 mb-6" />
                            <h2 className="text-2xl font-semibold text-slate-100 mb-4">
                                🤖 AI가 분석 중입니다
                            </h2>
                            <p className="text-slate-300 mb-2 text-center max-w-md">
                                웹사이트 내용을 분석하여 추천 키워드와 카테고리를 생성하고 있습니다.
                            </p>
                            {analysisStatus.website_url && (
                                <p className="text-sm text-slate-400 mt-4">
                                    분석 중인 사이트: <span className="text-blue-400">{analysisStatus.website_url}</span>
                                </p>
                            )}
                            <div className="mt-8 flex items-center gap-2 text-slate-400 text-sm">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>잠시만 기다려주세요... 페이지가 자동으로 업데이트됩니다</span>
                            </div>
                        </div>
                    </div>

                    {/* 분석 진행 단계 표시 */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-800/30 border border-blue-500/30 rounded-xl p-4 text-center">
                            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                                <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                            </div>
                            <h3 className="text-slate-200 font-semibold mb-2">웹사이트 스크래핑</h3>
                            <p className="text-xs text-slate-400">웹사이트 내용을 수집 중...</p>
                        </div>
                        <div className="bg-slate-800/30 border border-purple-500/30 rounded-xl p-4 text-center">
                            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                                <Sparkles className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="text-slate-200 font-semibold mb-2">AI 분석</h3>
                            <p className="text-xs text-slate-400">Gemini AI가 내용을 분석 중...</p>
                        </div>
                        <div className="bg-slate-800/30 border border-slate-600 rounded-xl p-4 text-center">
                            <div className="w-12 h-12 bg-slate-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                                <Check className="w-6 h-6 text-slate-500" />
                            </div>
                            <h3 className="text-slate-400 font-semibold mb-2">결과 생성</h3>
                            <p className="text-xs text-slate-500">대기 중...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    // AI 제안 로딩 중 (분석은 완료되었지만 데이터를 가져오는 중)
    if (isLoading) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
                            <p className="text-slate-300">AI 제안을 불러오는 중...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    // 에러 처리
    if (error) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <p className="text-red-400 mb-4">AI 제안을 불러올 수 없습니다</p>
                        <button
                            onClick={() => queryClient.invalidateQueries({ queryKey: ['aiSuggestions'] })}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                            다시 시도
                        </button>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-900">
            <Header />

            <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* 헤더 */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 mb-4">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-4xl font-bold text-slate-100 mb-3">
                        AI 추천 설정 검토
                    </h1>
                    <p className="text-xl text-slate-400">
                        AI가 분석한 결과를 확인하고 필요한 경우 수정하세요
                    </p>
                </div>

                {/* AI 분석 요약 섹션 */}
                {analysisStatus && analysisStatus.website_analysis && (
                    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-6">
                        <button
                            onClick={() => setShowAnalysisSummary(!showAnalysisSummary)}
                            className="w-full flex items-center justify-between text-left"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                                    <Sparkles className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-semibold text-slate-100">
                                        AI 분석 요약
                                    </h2>
                                    <p className="text-sm text-slate-400">
                                        웹사이트 분석 결과를 확인하세요
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 text-slate-400">
                                {showAnalysisSummary ? (
                                    <>
                                        <span className="text-sm">접기</span>
                                        <ChevronUp className="w-5 h-5" />
                                    </>
                                ) : (
                                    <>
                                        <span className="text-sm">보기</span>
                                        <ChevronDown className="w-5 h-5" />
                                    </>
                                )}
                            </div>
                        </button>

                        {showAnalysisSummary && (
                            <div className="mt-4 pt-4 border-t border-slate-700">
                                <div className="bg-slate-900/60 rounded-xl p-5">
                                    <div className="flex items-start gap-3">
                                        <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                                            <Sparkles className="w-4 h-4 text-blue-400" />
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="text-slate-200 font-medium mb-2">
                                                분석된 웹사이트
                                            </h3>
                                            {analysisStatus.website_url && (
                                                <p className="text-sm text-blue-400 mb-4 break-all">
                                                    {analysisStatus.website_url}
                                                </p>
                                            )}
                                            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                                                <p className="text-slate-300 leading-relaxed whitespace-pre-line">
                                                    {analysisStatus.website_analysis}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 키워드 섹션 */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-6">
                    <h2 className="text-2xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
                        <Sparkles className="w-6 h-6 text-blue-400" />
                        AI가 추천한 키워드
                    </h2>

                    {/* 키워드 태그 */}
                    <div className="flex flex-wrap gap-2 mb-4">
                        {keywords.map((kw) => (
                            <span
                                key={kw.id}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/30"
                            >
                                {kw.keyword}
                                <button
                                    onClick={() => handleRemoveKeyword(kw.id)}
                                    className="text-blue-300/80 hover:text-blue-200 transition-colors"
                                    aria-label={`${kw.keyword} 삭제`}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </span>
                        ))}
                    </div>

                    {/* 키워드 추가 입력 */}
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newKeyword}
                            onChange={(e) => setNewKeyword(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAddKeyword()}
                            placeholder="새 키워드 추가..."
                            className="flex-1 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={handleAddKeyword}
                            disabled={!newKeyword.trim()}
                            className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            추가
                        </button>
                    </div>

                    <p className="text-sm text-slate-400 mt-3">
                        💡 {keywords.length}/20 키워드 • Enter 또는 "추가" 버튼으로 추가하세요
                    </p>
                </div>

                {/* 카테고리 섹션 */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8">
                    <h2 className="text-2xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
                        <Sparkles className="w-6 h-6 text-purple-400" />
                        AI가 추천한 카테고리
                    </h2>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {categories.map((cat) => (
                            <label
                                key={cat.id}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-all ${cat.is_primary
                                    ? 'border-purple-500 bg-purple-500/10'
                                    : 'border-slate-600 hover:border-slate-500'
                                    }`}
                            >
                                <input
                                    type="checkbox"
                                    checked={cat.is_primary}
                                    onChange={() => handleCategoryToggle(cat.id)}
                                    className="w-5 h-5 accent-purple-500"
                                />
                                <span className="text-slate-100">{cat.category_path}</span>
                            </label>
                        ))}
                    </div>

                    <p className="text-sm text-slate-400 mt-3">
                        💡 {categories.filter(c => c.is_primary).length}/{categories.length} 선택됨
                    </p>
                </div>

                {/* 확정 버튼 */}
                <div className="flex gap-4 justify-center">
                    <button
                        onClick={() => router.back()}
                        disabled={mutation.isPending}
                        className="px-8 py-4 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition-all font-semibold"
                    >
                        취소
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={mutation.isPending || keywords.length === 0}
                        className="px-10 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold text-lg disabled:opacity-50 hover:shadow-lg hover:shadow-purple-500/50 transition-all flex items-center gap-2"
                    >
                        {mutation.isPending ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                저장 중...
                            </>
                        ) : (
                            <>
                                <Check className="w-5 h-5" />
                                이 설정으로 확정하기
                            </>
                        )}
                    </button>
                </div>

                <p className="text-center text-sm text-slate-500 mt-6">
                    확정 후 대시보드에서 언제든지 설정을 수정할 수 있습니다
                </p>
            </main>
        </div>
    );
}

