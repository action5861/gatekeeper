'use client'

import { CheckCircle, Clock, DollarSign, Target, XCircle } from 'lucide-react'

interface Bid {
    id: string
    auctionId: string
    amount: number
    timestamp: string
    status: 'active' | 'won' | 'lost' | 'pending'
    highestBid?: number
    myBid: number
}

interface MyBidsProps {
    recentBids?: Bid[]
}

export default function MyBids({ recentBids }: MyBidsProps) {
    if (!recentBids) {
        return (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                </div>
            </div>
        )
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'won':
                return <CheckCircle className="w-4 h-4 text-green-400" />
            case 'lost':
                return <XCircle className="w-4 h-4 text-red-400" />
            case 'active':
                return <Clock className="w-4 h-4 text-blue-400" />
            default:
                return <Clock className="w-4 h-4 text-yellow-400" />
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'won':
                return 'text-green-400'
            case 'lost':
                return 'text-red-400'
            case 'active':
                return 'text-blue-400'
            default:
                return 'text-yellow-400'
        }
    }

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-100">My Bids</h2>
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-white" />
                </div>
            </div>

            {recentBids.length === 0 ? (
                <div className="text-center py-8">
                    <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No bids yet</p>
                    <p className="text-sm text-slate-500">Start bidding to see your activity here</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {recentBids.slice(0, 5).map((bid) => (
                        <div
                            key={bid.id}
                            className="bg-slate-700/30 rounded-xl p-4 border border-slate-600 hover:border-slate-500 transition-all duration-200"
                        >
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                    {getStatusIcon(bid.status)}
                                    <span className={`text-sm font-medium ${getStatusColor(bid.status)}`}>
                                        {bid.status.charAt(0).toUpperCase() + bid.status.slice(1)}
                                    </span>
                                </div>
                                <span className="text-xs text-slate-400">
                                    {new Date(bid.timestamp).toLocaleDateString()}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs text-slate-400">Auction ID</p>
                                    <p className="text-sm font-medium text-slate-200">{bid.auctionId}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-400">My Bid</p>
                                    <p className="text-sm font-bold text-slate-100">₩{bid.myBid.toLocaleString()}</p>
                                </div>
                                {bid.highestBid && (
                                    <div>
                                        <p className="text-xs text-slate-400">Highest Bid</p>
                                        <p className="text-sm font-medium text-slate-200">₩{bid.highestBid.toLocaleString()}</p>
                                    </div>
                                )}
                                <div>
                                    <p className="text-xs text-slate-400">Amount</p>
                                    <p className="text-sm font-medium text-slate-200">₩{bid.amount.toLocaleString()}</p>
                                </div>
                            </div>

                            {/* Bid Status Indicator */}
                            <div className="mt-3 pt-3 border-t border-slate-600">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs text-slate-400">Bid Status</span>
                                    <div className="flex items-center space-x-2">
                                        <DollarSign className="w-3 h-3 text-slate-400" />
                                        <span className="text-xs text-slate-300">
                                            {bid.status === 'active' && 'Active'}
                                            {bid.status === 'won' && 'Won'}
                                            {bid.status === 'lost' && 'Outbid'}
                                            {bid.status === 'pending' && 'Pending'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* View All Bids Button */}
            {recentBids.length > 5 && (
                <div className="mt-6 text-center">
                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors duration-200">
                        View All Bids ({recentBids.length})
                    </button>
                </div>
            )}
        </div>
    )
} 