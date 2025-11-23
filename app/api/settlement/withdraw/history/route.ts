import { NextRequest, NextResponse } from 'next/server'

const SETTLEMENT_SERVICE_URL = process.env.SETTLEMENT_SERVICE_URL || 'http://localhost:8008'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')

    if (!authHeader) {
      console.error('[Withdrawal History API] No authorization header')
      return NextResponse.json(
        { message: 'Authorization header required' },
        { status: 401 }
      )
    }

    console.log(`[Withdrawal History API] Fetching withdrawal history`)

    const response = await fetch(`${SETTLEMENT_SERVICE_URL}/api/settlement/withdraw/history`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
    })

    console.log(`[Withdrawal History API] Response status: ${response.status}`)

    if (!response.ok) {
      let errorMessage = 'Failed to fetch withdrawal history'
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        console.error(`[Withdrawal History API] Error response:`, errorData)
      } catch (parseError) {
        const errorText = await response.text()
        errorMessage = errorText || `Server error (${response.status})`
        console.error(`[Withdrawal History API] Failed to parse error:`, errorText)
      }
      return NextResponse.json(
        { message: errorMessage },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log(`[Withdrawal History API] Success: found ${data.total} withdrawals`)
    return NextResponse.json(data)

  } catch (error) {
    console.error('[Withdrawal History API] Exception:', error)
    const errorMessage = error instanceof Error ? error.message : 'Internal server error'
    return NextResponse.json(
      { message: errorMessage },
      { status: 500 }
    )
  }
}

