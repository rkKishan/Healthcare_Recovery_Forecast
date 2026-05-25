import type { Metadata } from 'next'
import { ReactNode } from 'react'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Healthcare Recovery Forecast',
  description: 'Clinical Modernist Dashboard for Patient Recovery Predictions',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
