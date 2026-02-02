import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PREMIUM AI STUDIO - Picture on Frame',
  description: 'Exclusive AI Renderings - Picture on Frame',
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
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  )
}



