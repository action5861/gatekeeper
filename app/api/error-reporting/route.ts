import { NextRequest, NextResponse } from 'next/server'

interface ErrorLog {
    id: string
    message: string
    stack?: string
    componentStack?: string
    timestamp: string
    userAgent: string
    url: string
    userId?: string
    errorType: 'network' | 'runtime' | 'authentication' | 'validation' | 'unknown'
    severity: 'low' | 'medium' | 'high' | 'critical'
    context?: Record<string, any>
}

export async function POST(request: NextRequest) {
    try {
        const errorLog: ErrorLog = await request.json()

        // 에러 로그 검증
        if (!errorLog.message || !errorLog.timestamp) {
            return NextResponse.json(
                { error: 'Invalid error log format' },
                { status: 400 }
            )
        }

        // 개발 환경에서는 콘솔에 출력
        if (process.env.NODE_ENV === 'development') {
            console.error('Error reported:', {
                id: errorLog.id,
                message: errorLog.message,
                type: errorLog.errorType,
                severity: errorLog.severity,
                timestamp: errorLog.timestamp,
                userId: errorLog.userId,
                url: errorLog.url,
            })
        }

        // 프로덕션에서는 실제 에러 모니터링 서비스로 전송
        if (process.env.NODE_ENV === 'production') {
            // 실제 에러 모니터링 서비스 API 호출
            // await sendToErrorService(errorLog)

            // 현재는 로그 파일에 저장하거나 데이터베이스에 저장
            console.error('Production error logged:', errorLog)
        }

        // 에러 메트릭 업데이트 (선택사항)
        // await updateErrorMetrics(errorLog)

        return NextResponse.json({ success: true })
    } catch (error) {
        console.error('Error in error reporting endpoint:', error)
        return NextResponse.json(
            { error: 'Failed to process error report' },
            { status: 500 }
        )
    }
}

export async function GET(request: NextRequest) {
    try {
        // 에러 통계 조회 (관리자용)
        const { searchParams } = new URL(request.url)
        const userId = searchParams.get('userId')
        const timeRange = searchParams.get('timeRange') || '24h'

        // 실제로는 데이터베이스에서 에러 통계를 조회
        const errorStats = {
            totalErrors: 0,
            errorsByType: {},
            errorsBySeverity: {},
            recentErrors: [],
            timeRange,
            userId,
        }

        return NextResponse.json(errorStats)
    } catch (error) {
        console.error('Error fetching error stats:', error)
        return NextResponse.json(
            { error: 'Failed to fetch error statistics' },
            { status: 500 }
        )
    }
} 