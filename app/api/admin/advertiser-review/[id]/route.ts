import { requireAdminAuth } from '@/lib/admin-auth'
import { NextRequest, NextResponse } from 'next/server'

export async function DELETE(
    request: NextRequest,
    { params }: { params: { id: string } }
) {
    try {
        await requireAdminAuth(request)

        const advertiserId = parseInt(params.id)
        if (isNaN(advertiserId)) {
            return NextResponse.json(
                { error: 'Invalid advertiser ID' },
                { status: 400 }
            )
        }

        const advertiserServiceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
        const response = await fetch(`${advertiserServiceUrl}/admin/delete-advertiser/${advertiserId}`, {
            method: 'DELETE',
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to delete advertiser' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)

    } catch (error) {
        console.error('Error deleting advertiser:', error)
        if (error instanceof Error && error.message.includes('Unauthorized')) {
            return NextResponse.json(
                { error: 'Unauthorized: Admin access required' },
                { status: 401 }
            )
        }
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        )
    }
} 