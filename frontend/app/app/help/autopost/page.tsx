'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '../../../../lib/routes';
import { DebugPanel, useDebugEnabled, useDebugTimestamp } from '../../../../lib/debugPanel';
import { useAuthGate } from '../../../../lib/useAuthGate';

export default function AutopostHelpPage() {
  const router = useRouter();
  const { ready, session, user } = useAuthGate();
  const debugEnabled = useDebugEnabled();
  const timestamp = useDebugTimestamp();

  useEffect(() => {
    if (ready && !session) {
      router.replace(ROUTES.login);
    }
  }, [ready, session, router]);

  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const hasSession = Boolean(session);
  const userEmail = user?.email || '';
  const debugPanel = debugEnabled ? (
    <DebugPanel
      ready={ready}
      hasSession={hasSession}
      userEmail={userEmail}
      pathname={currentPath}
      origin={origin}
      timestamp={timestamp}
    />
  ) : null;

  if (!ready) {
    return (
      <div style={{ padding: 24 }}>
        Loading session…
        {debugPanel}
      </div>
    );
  }

  if (!session) {
    return (
      <div style={{ padding: 24 }}>
        Redirecting to login…
        {debugPanel}
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-white px-6 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-black text-gray-800 uppercase tracking-wide mb-4">Panduan AI Auto-Posting</h1>
          <p className="text-sm text-gray-500 mb-10">
            Panduan lengkap untuk menggunakan Fitur Auto-Posting dengan aman dan optimal.
          </p>

          <div className="space-y-8 text-sm text-gray-700">
            <section>
              <h2 className="text-lg font-bold text-gray-800 mb-2">Apa itu Fitur Auto-Posting?</h2>
              <p>
                Fitur Auto-Posting adalah fitur yang membantu user untuk menjalankan proses upload video langsung dari browser
                kamu, AI kami akan membantu memaksimalkan hasil postingan untuk mendapatkan engagement tinggi.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-gray-800 mb-2">Warning</h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>Pastikan Anda sudah login TikTok di browser.</li>
                <li>Jangan logout selama proses auto-post berjalan.</li>
                <li>Biarkan browser tetap aktif untuk menjaga koneksi.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-bold text-gray-800 mb-2">Keamanan</h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>AI kami tidak mengakses DM.</li>
                <li>AI kami tidak mengakses saldo/dompet.</li>
                <li>AI kami tidak menyimpan password atau data sensitif lainnya.</li>
              </ul>
            </section>
          </div>

          <div className="mt-10">
            <button
              onClick={() => router.replace(ROUTES.afterLogin)}
              className="px-6 py-3 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition"
            >
              Kembali ke Dashboard
            </button>
          </div>
        </div>
      </div>
      {debugPanel}
    </>
  );
}
