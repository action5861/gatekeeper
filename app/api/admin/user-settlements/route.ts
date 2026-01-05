import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminAuth } from '@/lib/admin-auth'

const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8001'

/**
 * 사용자 정산 관련 API (GET)
 * - summary: 요약 통계
 * - users: 사용자별 적립금 목록
 * - transactions: 정산 내역
 * - withdrawals: 출금 요청 목록
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
    const endpoint = searchParams.get('endpoint') || 'summary'
    const page = searchParams.get('page') || '1'
    const pageSize = searchParams.get('pageSize') || '20'
    const sortBy = searchParams.get('sortBy') || 'earnings'
    const search = searchParams.get('search') || ''
    const userId = searchParams.get('userId') || ''
    const typeFilter = searchParams.get('typeFilter') || ''
    const statusFilter = searchParams.get('statusFilter') || ''

    let apiUrl: string

    switch (endpoint) {
      case 'summary':
        apiUrl = `${USER_SERVICE_URL}/admin/user-settlements/summary`
        break
      case 'users':
        apiUrl = `${USER_SERVICE_URL}/admin/user-settlements/users?page=${page}&page_size=${pageSize}&sort_by=${sortBy}${search ? `&search=${encodeURIComponent(search)}` : ''}`
        break
      case 'transactions':
        apiUrl = `${USER_SERVICE_URL}/admin/user-settlements/transactions?page=${page}&page_size=${pageSize}${userId ? `&user_id=${userId}` : ''}${typeFilter ? `&type_filter=${typeFilter}` : ''}`
        break
      case 'withdrawals':
        apiUrl = `${USER_SERVICE_URL}/admin/user-settlements/withdrawals?page=${page}&page_size=${pageSize}${statusFilter ? `&status_filter=${statusFilter}` : ''}`
        break
      default:
        return NextResponse.json(
          { success: false, error: '잘못된 endpoint입니다.' },
          { status: 400 }
        )
    }

    console.log(`[Admin API] Fetching user settlements: ${apiUrl}`)

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      next: { revalidate: 30 } // 30초 캐싱
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`[Admin API] User service error: ${response.status} - ${errorText}`)
      return NextResponse.json(
        { success: false, error: '사용자 서비스 오류' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ success: true, data })

  } catch (error) {
    console.error('[Admin API] User settlements error:', error)
    return NextResponse.json(
      { success: false, error: '사용자 정산 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}

/**
 * 출금 요청 승인/거절 (POST)
 */
export async function POST(request: NextRequest) {
  try {
    // 관리자 인증 확인 (JWT 검증)
    const admin = await verifyAdminAuth(request)
    if (!admin) {
      return NextResponse.json(
        { success: false, error: '관리자 인증이 필요합니다.' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { action, withdrawalId } = body

    if (!action || !withdrawalId) {
      return NextResponse.json(
        { success: false, error: 'action과 withdrawalId가 필요합니다.' },
        { status: 400 }
      )
    }

    const endpoint = action === 'approve' ? 'approve' : 'reject'
    const apiUrl = `${USER_SERVICE_URL}/admin/user-settlements/withdrawals/${withdrawalId}/${endpoint}`

    console.log(`[Admin API] Processing withdrawal: ${apiUrl}`)

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(
        { success: false, error: errorData.detail || '처리 실패' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ success: true, data })

  } catch (error) {
    console.error('[Admin API] Withdrawal action error:', error)
    return NextResponse.json(
      { success: false, error: '출금 요청 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}

