'use client';

import Header from '@/components/Header';
import { authenticatedFetch } from '@/lib/auth';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Check, Loader2, Plus, Sparkles, X } from 'lucide-react';
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

    // AI 제안 데이터 fetch
    const { data, isLoading, error } = useQuery<AISuggestions>({
        queryKey: ['aiSuggestions'],
        queryFn: fetchAISuggestions,
    });

    useEffect(() => {
        if (data) {
            setKeywords(data.keywords);
            setCategories(data.categories);
        }
    }, [data]);

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

    if (error) {
        return (
            <div className="min-h-screen bg-slate-900">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <p className="text-red-400">AI 제안을 불러올 수 없습니다</p>
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

