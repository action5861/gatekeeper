'use client'


interface SkeletonProps {
    className?: string
    width?: string | number
    height?: string | number
}

// 기본 Skeleton 컴포넌트
export function Skeleton({ className = '', width, height }: SkeletonProps) {
    return (
        <div
            className={`animate-pulse bg-slate-700 rounded ${className}`}
            style={{
                width: width,
                height: height,
            }}
        />
    )
}

// 카드 형태의 Skeleton
export function CardSkeleton() {
    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="space-y-4">
                {/* 헤더 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-6 h-6 rounded" />
                    <Skeleton className="w-32 h-6 rounded" />
                </div>

                {/* 메인 콘텐츠 */}
                <div className="space-y-3">
                    <Skeleton className="w-full h-20 rounded-lg" />
                    <div className="grid grid-cols-2 gap-3">
                        <Skeleton className="w-full h-16 rounded" />
                        <Skeleton className="w-full h-16 rounded" />
                    </div>
                </div>
            </div>
        </div>
    )
}

// 수익 요약 Skeleton
export function EarningsSummarySkeleton() {
    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="space-y-6">
                {/* 헤더 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-6 h-6 rounded" />
                    <Skeleton className="w-40 h-7 rounded" />
                </div>

                {/* 총 수익 */}
                <div className="bg-gradient-to-r from-green-600/20 to-blue-600/20 rounded-lg p-4 border border-green-500/30">
                    <div className="flex items-center justify-between">
                        <div className="space-y-2">
                            <Skeleton className="w-24 h-4 rounded" />
                            <Skeleton className="w-32 h-8 rounded" />
                        </div>
                        <Skeleton className="w-12 h-12 rounded-full" />
                    </div>
                </div>

                {/* 세부 수익 */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Skeleton className="w-16 h-4 rounded" />
                        <Skeleton className="w-20 h-6 rounded" />
                    </div>
                    <div className="space-y-2">
                        <Skeleton className="w-16 h-4 rounded" />
                        <Skeleton className="w-20 h-6 rounded" />
                    </div>
                </div>

                {/* 성장률 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-4 h-4 rounded" />
                    <Skeleton className="w-20 h-4 rounded" />
                </div>
            </div>
        </div>
    )
}

// 품질 이력 Skeleton
export function QualityHistorySkeleton() {
    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="space-y-6">
                {/* 헤더 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-6 h-6 rounded" />
                    <Skeleton className="w-36 h-7 rounded" />
                </div>

                {/* 차트 영역 */}
                <div className="space-y-4">
                    <Skeleton className="w-full h-32 rounded-lg" />
                    <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Skeleton className="w-12 h-4 rounded" />
                            <Skeleton className="w-16 h-6 rounded" />
                        </div>
                        <div className="space-y-2">
                            <Skeleton className="w-12 h-4 rounded" />
                            <Skeleton className="w-16 h-6 rounded" />
                        </div>
                        <div className="space-y-2">
                            <Skeleton className="w-12 h-4 rounded" />
                            <Skeleton className="w-16 h-6 rounded" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

// 제출 한도 카드 Skeleton
export function SubmissionLimitSkeleton() {
    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="space-y-6">
                {/* 헤더 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-6 h-6 rounded" />
                    <Skeleton className="w-32 h-7 rounded" />
                </div>

                {/* 진행률 바 */}
                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <Skeleton className="w-20 h-4 rounded" />
                        <Skeleton className="w-16 h-4 rounded" />
                    </div>
                    <Skeleton className="w-full h-3 rounded-full" />
                </div>

                {/* 통계 */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Skeleton className="w-16 h-4 rounded" />
                        <Skeleton className="w-20 h-6 rounded" />
                    </div>
                    <div className="space-y-2">
                        <Skeleton className="w-16 h-4 rounded" />
                        <Skeleton className="w-20 h-6 rounded" />
                    </div>
                </div>

                {/* 팁 */}
                <div className="space-y-2">
                    <Skeleton className="w-16 h-4 rounded" />
                    <Skeleton className="w-full h-12 rounded" />
                </div>
            </div>
        </div>
    )
}

// 실시간 통계 Skeleton
export function RealtimeStatsSkeleton() {
    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 mt-8">
            <div className="space-y-6">
                {/* 헤더 */}
                <div className="flex items-center space-x-2">
                    <Skeleton className="w-6 h-6 rounded" />
                    <Skeleton className="w-32 h-7 rounded" />
                </div>

                {/* 통계 카드들 */}
                <div className="grid md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="space-y-3">
                            <div className="flex items-center space-x-2">
                                <Skeleton className="w-5 h-5 rounded" />
                                <Skeleton className="w-20 h-5 rounded" />
                            </div>
                            <Skeleton className="w-16 h-8 rounded" />
                            <Skeleton className="w-24 h-4 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

// 대시보드 전체 Skeleton
export function DashboardSkeleton() {
    return (
        <div className="min-h-screen bg-slate-900">
            {/* Header Skeleton */}
            <div className="bg-slate-800 border-b border-slate-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <Skeleton className="w-32 h-8 rounded" />
                        <div className="flex items-center space-x-4">
                            <Skeleton className="w-20 h-8 rounded" />
                            <Skeleton className="w-20 h-8 rounded" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Page Title */}
                <div className="mb-8 space-y-2">
                    <Skeleton className="w-48 h-8 rounded" />
                    <Skeleton className="w-64 h-5 rounded" />
                </div>

                {/* Dashboard Grid */}
                <div className="grid lg:grid-cols-3 gap-8">
                    <EarningsSummarySkeleton />
                    <QualityHistorySkeleton />
                    <SubmissionLimitSkeleton />
                </div>

                <RealtimeStatsSkeleton />
            </main>
        </div>
    )
} 