import { NextRequest, NextResponse } from 'next/server'

const SETTLEMENT_SERVICE_URL = process.env.SETTLEMENT_SERVICE_URL || 'http://localhost:8008'

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')

    if (!authHeader) {
      console.error('[Withdrawal API] No authorization header')
      return NextResponse.json(
        { message: 'Authorization header required' },
        { status: 401 }
      )
    }

    const body = await request.json()
    console.log(`[Withdrawal API] Withdrawal request:`, { 
      request_amount: body.request_amount,
      bank_name: body.bank_name ? '***' : undefined
    })

    const response = await fetch(`${SETTLEMENT_SERVICE_URL}/api/settlement/withdraw`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    console.log(`[Withdrawal API] Response status: ${response.status}`)

    if (!response.ok) {
      let errorMessage = 'Failed to process withdrawal request'
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        console.error(`[Withdrawal API] Error response:`, errorData)
      } catch (parseError) {
        const errorText = await response.text()
        errorMessage = errorText || `Server error (${response.status})`
        console.error(`[Withdrawal API] Failed to parse error:`, errorText)
      }
      return NextResponse.json(
        { message: errorMessage },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log(`[Withdrawal API] Success: withdrawal_id=${data.withdrawal_id}`)
    return NextResponse.json(data)

  } catch (error) {
    console.error('[Withdrawal API] Exception:', error)
    const errorMessage = error instanceof Error ? error.message : 'Internal server error'
    return NextResponse.json(
      { message: errorMessage },
      { status: 500 }
    )
  }
}

