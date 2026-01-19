import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PREMIUM AI STUDIO - Picture on Frame',
  description: 'Picture on Frame by slstari',
  icons: {
    icon: '/icon.svg',
    apple: '/icon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}



