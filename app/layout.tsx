// 전역 레이아웃

import type { Metadata, Viewport } from 'next'
import ReturnTracker from './components/ReturnTracker'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'Intendex – Real-time Intent Exchange',
  description: 'A platform for real-time search data trading and auction',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-900 text-slate-100 min-h-screen">
        <Providers>
          <ReturnTracker />
          {children}
        </Providers>
      </body>
    </html>
  )
}
