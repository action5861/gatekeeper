import { sql } from '@vercel/postgres'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
    try {
        // Get all business categories ordered by level and sort_order
        const result = await sql`
            SELECT id, parent_id, name, path, level, is_active, sort_order, created_at
            FROM business_categories 
            WHERE is_active = true 
            ORDER BY level, sort_order, name
        `

        return NextResponse.json(result.rows)
    } catch (error) {
        console.error('Error fetching business categories:', error)
        return NextResponse.json(
            { error: 'Failed to fetch business categories' },
            { status: 500 }
        )
    }
} 