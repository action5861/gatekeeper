// [LIVE] Dashboard API client
export type QualityDay = { date: string; avg: number; count: number }
export type Summary = {
    avgQualityScore: number
    successRate: number
    today: { bids: number; bidValue: number; rewards: number }
}
export type TransactionItem = {
    id: string; query: string; buyerName: string; primaryReward: number; secondaryReward?: number; status: string; timestamp?: string
}
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

const authHeaders = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function fetchSummary(): Promise<Summary> {
    console.log('🔍 [LIVE] fetchSummary called with API_BASE:', API_BASE)
    const res = await fetch(`${API_BASE}/api/dashboard/summary`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } })
    console.log('🔍 [LIVE] fetchSummary response status:', res.status)
    if (!res.ok) throw new Error(`summary ${res.status}`)
    const data = await res.json()
    console.log('🔍 [LIVE] fetchSummary data:', data)
    return data
}

export async function fetchQualityHistory(): Promise<QualityDay[]> {
    console.log('🔍 [LIVE] fetchQualityHistory called with API_BASE:', API_BASE)
    const res = await fetch(`${API_BASE}/api/dashboard/quality-history`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } })
    console.log('🔍 [LIVE] fetchQualityHistory response status:', res.status)
    if (!res.ok) throw new Error(`quality-history ${res.status}`)
    const data = await res.json()
    console.log('🔍 [LIVE] fetchQualityHistory data:', data)
    return data.series
}

export async function fetchTransactions(): Promise<TransactionItem[]> {
    const res = await fetch(`${API_BASE}/api/dashboard/transactions`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } })
    if (!res.ok) throw new Error(`transactions ${res.status}`)
    const data = await res.json()
    return data.items
}

export async function fetchRealtime(): Promise<{ recentQueries: number; recentBids: number }> {
    console.log('🔍 [LIVE] fetchRealtime called with API_BASE:', API_BASE)
    const res = await fetch(`${API_BASE}/api/dashboard/realtime`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } })
    console.log('🔍 [LIVE] fetchRealtime response status:', res.status)
    if (!res.ok) throw new Error(`realtime ${res.status}`)
    const data = await res.json()
    console.log('🔍 [LIVE] fetchRealtime data:', data)
    return data
}
