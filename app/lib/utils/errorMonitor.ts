'use client'

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

interface ErrorMetrics {
    totalErrors: number
    errorsByType: Record<string, number>
    errorsBySeverity: Record<string, number>
    recentErrors: ErrorLog[]
    lastErrorTime?: string
}

class ErrorMonitor {
    private static instance: ErrorMonitor
    private errorHistory: ErrorLog[] = []
    private maxHistorySize = 100
    private isInitialized = false

    private constructor() { }

    static getInstance(): ErrorMonitor {
        if (!ErrorMonitor.instance) {
            ErrorMonitor.instance = new ErrorMonitor()
        }
        return ErrorMonitor.instance
    }

    init() {
        if (this.isInitialized) return

        // 전역 에러 핸들러 등록
        window.addEventListener('error', this.handleGlobalError.bind(this))
        window.addEventListener('unhandledrejection', this.handleUnhandledRejection.bind(this))

        // 기존 에러 히스토리 로드
        this.loadErrorHistory()

        this.isInitialized = true
        console.log('ErrorMonitor initialized')
    }

    private handleGlobalError(event: ErrorEvent) {
        const errorLog: ErrorLog = {
            id: this.generateErrorId(),
            message: event.message,
            stack: event.error?.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: this.getUserId(),
            errorType: this.categorizeError(event.error),
            severity: this.assessSeverity(event.error),
            context: {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
            },
        }

        this.logError(errorLog)
    }

    private handleUnhandledRejection(event: PromiseRejectionEvent) {
        const errorLog: ErrorLog = {
            id: this.generateErrorId(),
            message: event.reason?.message || 'Unhandled Promise Rejection',
            stack: event.reason?.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: this.getUserId(),
            errorType: 'runtime',
            severity: 'high',
            context: {
                reason: event.reason,
            },
        }

        this.logError(errorLog)
    }

    logError(error: Error | string, context?: Record<string, any>) {
        const errorLog: ErrorLog = {
            id: this.generateErrorId(),
            message: error instanceof Error ? error.message : error,
            stack: error instanceof Error ? error.stack : undefined,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: this.getUserId(),
            errorType: error instanceof Error ? this.categorizeError(error) : 'unknown',
            severity: error instanceof Error ? this.assessSeverity(error) : 'medium',
            context,
        }

        this.addToHistory(errorLog)
        this.saveErrorHistory()
        this.reportError(errorLog)
    }

    logComponentError(
        error: Error,
        componentName: string,
        componentStack?: string,
        context?: Record<string, any>
    ) {
        const errorLog: ErrorLog = {
            id: this.generateErrorId(),
            message: error.message,
            stack: error.stack,
            componentStack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: this.getUserId(),
            errorType: this.categorizeError(error),
            severity: this.assessSeverity(error),
            context: {
                componentName,
                ...context,
            },
        }

        this.addToHistory(errorLog)
        this.saveErrorHistory()
        this.reportError(errorLog)
    }

    logNetworkError(
        url: string,
        status: number,
        statusText: string,
        context?: Record<string, any>
    ) {
        const errorLog: ErrorLog = {
            id: this.generateErrorId(),
            message: `Network Error: ${status} ${statusText}`,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: this.getUserId(),
            errorType: 'network',
            severity: status >= 500 ? 'high' : status >= 400 ? 'medium' : 'low',
            context: {
                requestUrl: url,
                status,
                statusText,
                ...context,
            },
        }

        this.addToHistory(errorLog)
        this.saveErrorHistory()
        this.reportError(errorLog)
    }

    private categorizeError(error: Error): ErrorLog['errorType'] {
        const message = error.message.toLowerCase()
        const stack = error.stack?.toLowerCase() || ''

        if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
            return 'network'
        }
        if (message.includes('authentication') || message.includes('unauthorized') || message.includes('token')) {
            return 'authentication'
        }
        if (message.includes('validation') || message.includes('invalid')) {
            return 'validation'
        }
        if (stack.includes('react') || stack.includes('component')) {
            return 'runtime'
        }
        return 'unknown'
    }

    private assessSeverity(error: Error): ErrorLog['severity'] {
        const message = error.message.toLowerCase()

        if (message.includes('critical') || message.includes('fatal')) {
            return 'critical'
        }
        if (message.includes('authentication') || message.includes('unauthorized')) {
            return 'high'
        }
        if (message.includes('network') || message.includes('fetch')) {
            return 'medium'
        }
        return 'low'
    }

    private generateErrorId(): string {
        return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private getUserId(): string | undefined {
        try {
            const token = localStorage.getItem('token')
            if (token) {
                // JWT 토큰에서 사용자 ID 추출 (실제로는 디코딩 필요)
                return 'user_' + token.split('.')[1]?.substr(0, 8) || 'unknown'
            }
        } catch (e) {
            console.warn('Failed to get user ID from token')
        }
        return undefined
    }

    private addToHistory(errorLog: ErrorLog) {
        this.errorHistory.unshift(errorLog)
        if (this.errorHistory.length > this.maxHistorySize) {
            this.errorHistory.pop()
        }
    }

    private saveErrorHistory() {
        try {
            localStorage.setItem('errorHistory', JSON.stringify(this.errorHistory))
        } catch (e) {
            console.warn('Failed to save error history to localStorage')
        }
    }

    private loadErrorHistory() {
        try {
            const saved = localStorage.getItem('errorHistory')
            if (saved) {
                this.errorHistory = JSON.parse(saved)
            }
        } catch (e) {
            console.warn('Failed to load error history from localStorage')
        }
    }

    private reportError(errorLog: ErrorLog) {
        // 개발 환경에서는 콘솔에 출력
        if (process.env.NODE_ENV === 'development') {
            console.error('Error logged:', errorLog)
        }

        // 프로덕션에서는 에러 모니터링 서비스로 전송
        if (process.env.NODE_ENV === 'production') {
            this.sendToErrorService(errorLog)
        }
    }

    private async sendToErrorService(errorLog: ErrorLog) {
        try {
            // 실제 에러 모니터링 서비스 API 호출
            const response = await fetch('/api/error-reporting', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(errorLog),
            })

            if (!response.ok) {
                throw new Error(`Failed to send error report: ${response.status}`)
            }

            console.log('Error reported to service successfully')
        } catch (e) {
            console.warn('Failed to send error to monitoring service:', e)
        }
    }

    getErrorMetrics(): ErrorMetrics {
        const errorsByType: Record<string, number> = {}
        const errorsBySeverity: Record<string, number> = {}

        this.errorHistory.forEach(error => {
            errorsByType[error.errorType] = (errorsByType[error.errorType] || 0) + 1
            errorsBySeverity[error.severity] = (errorsBySeverity[error.severity] || 0) + 1
        })

        return {
            totalErrors: this.errorHistory.length,
            errorsByType,
            errorsBySeverity,
            recentErrors: this.errorHistory.slice(0, 10),
            lastErrorTime: this.errorHistory[0]?.timestamp,
        }
    }

    clearErrorHistory() {
        this.errorHistory = []
        localStorage.removeItem('errorHistory')
    }

    getErrorHistory(): ErrorLog[] {
        return [...this.errorHistory]
    }
}

// 싱글톤 인스턴스
export const errorMonitor = ErrorMonitor.getInstance()

// 편의 함수들
export const logError = (error: Error | string, context?: Record<string, any>) => {
    errorMonitor.logError(error, context)
}

export const logComponentError = (
    error: Error,
    componentName: string,
    componentStack?: string,
    context?: Record<string, any>
) => {
    errorMonitor.logComponentError(error, componentName, componentStack, context)
}

export const logNetworkError = (
    url: string,
    status: number,
    statusText: string,
    context?: Record<string, any>
) => {
    errorMonitor.logNetworkError(url, status, statusText, context)
}

export const getErrorMetrics = () => errorMonitor.getErrorMetrics()

export const getErrorHistory = () => errorMonitor.getErrorHistory()

export const clearErrorHistory = () => errorMonitor.clearErrorHistory()

// 초기화
if (typeof window !== 'undefined') {
    errorMonitor.init()
} 