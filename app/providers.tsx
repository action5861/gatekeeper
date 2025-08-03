'use client'

import { errorMonitor } from '@/lib/utils/errorMonitor'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useEffect, useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 30000, // 30초
                        gcTime: 5 * 60 * 1000, // 5분
                        retry: (failureCount, error) => {
                            // 인증 에러는 재시도하지 않음
                            if (error instanceof Error && error.message.includes('Authentication failed')) {
                                return false
                            }
                            // 네트워크 에러는 최대 3번 재시도
                            return failureCount < 3
                        },
                        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
                    },
                    mutations: {
                        retry: 1,
                        retryDelay: 1000,
                    },
                },
            })
    )

    // 에러 모니터링 초기화
    useEffect(() => {
        errorMonitor.init()
    }, [])

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            {process.env.NODE_ENV === 'development' && (
                <ReactQueryDevtools initialIsOpen={false} />
            )}
        </QueryClientProvider>
    )
} 