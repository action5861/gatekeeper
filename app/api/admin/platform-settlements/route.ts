import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminAuth } from '@/lib/admin-auth'

const SETTLEMENT_SERVICE_URL = process.env.SETTLEMENT_SERVICE_URL || 'http://settlement-service:8003'

/**
 * 플랫폼 정산 통계 조회 API
 * 시스템 부하 최소화를 위해 백엔드에서 집계된 데이터만 전달
 */
export async function GET(request: NextRequest) {
  try {
    // 관리자 인증 확인 (JWT 검증)
    const admin = await verifyAdminAuth(request)
    if (!admin) {
      return NextResponse.json(
        { success: false, error: '관리자 인증이 필요합니다.' },
        { status: 401 }
      )
    }

    const { searchParams } = new URL(request.url)
    const period = searchParams.get('period') || 'week'
    const endpoint = searchParams.get('endpoint') || 'stats'
    const page = searchParams.get('page') || '1'
    const pageSize = searchParams.get('pageSize') || '20'

    let apiUrl: string
    if (endpoint === 'users') {
      apiUrl = `${SETTLEMENT_SERVICE_URL}/admin/platform-settlements/users?period=${period}&page=${page}&page_size=${pageSize}`
    } else {
      apiUrl = `${SETTLEMENT_SERVICE_URL}/admin/platform-settlements/stats?period=${period}`
    }

    console.log(`[Admin API] Fetching platform settlements: ${apiUrl}`)

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // 캐싱 설정 (1분)
      next: { revalidate: 60 }
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`[Admin API] Settlement service error: ${response.status} - ${errorText}`)
      return NextResponse.json(
        { success: false, error: '정산 서비스 오류' },
        { status: response.status }
      )
    }

    const data = await response.json()
    
    return NextResponse.json({
      success: true,
      data
    })

  } catch (error) {
    console.error('[Admin API] Platform settlements error:', error)
    return NextResponse.json(
      { success: false, error: '플랫폼 정산 통계 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}

