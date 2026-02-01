'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { COIN_PACKAGES, midtransService } from '../../../services/midtransService';
import { supabaseService } from '../../../services/supabaseService';
import { ROUTES } from '../../../lib/routes';
import { DebugPanel, useDebugEnabled, useDebugTimestamp } from '../../../lib/debugPanel';
import { useAuthGate } from '../../../lib/useAuthGate';

declare global {
  interface Window {
    snap?: {
      pay: (
        token: string,
        options: {
          onSuccess?: () => void;
          onPending?: () => void;
          onError?: () => void;
          onClose?: () => void;
        }
      ) => void;
    };
  }
}

export default function TopUpPage() {
  const router = useRouter();
  const { ready, session, user } = useAuthGate();
  const debugEnabled = useDebugEnabled();
  const timestamp = useDebugTimestamp();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toSafeErrorMessage = (err: any, fallback: string) => {
    const message = typeof err?.message === 'string' ? err.message : '';
    const safeMessages = new Set([
      'Sesi Anda telah berakhir. Silakan login ulang.',
      'Pembayaran gagal. Silakan coba lagi.'
    ]);
    return safeMessages.has(message) ? message : fallback;
  };

  const handlePay = async (packageId: string) => {
    try {
      setError(null);
      setLoadingId(packageId);

      const user = await supabaseService.getCurrentUser();
      const token = await supabaseService.getAccessToken();
      if (!user || !token) {
        throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
      }

      await midtransService.loadSnapScript();
      const snapToken = await midtransService.initializeSnap(packageId, user.id, token);

      if (!window.snap) {
        throw new Error('Midtrans Snap tidak tersedia.');
      }

      window.snap.pay(snapToken, {
        onSuccess: () => {
          router.replace(ROUTES.afterLogin);
        },
        onPending: () => {
          router.replace(ROUTES.afterLogin);
        },
        onError: () => {
          setError('Pembayaran gagal. Silakan coba lagi.');
        },
        onClose: () => {
          setLoadingId(null);
        }
      });
    } catch (err: any) {
      setError(toSafeErrorMessage(err, 'Gagal memulai pembayaran. Silakan coba lagi.'));
      setLoadingId(null);
    }
  };

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
      <div className="min-h-screen bg-gradient-to-b from-white via-white to-slate-50 px-6 py-16">
        <div className="max-w-5xl mx-auto relative">
          <button
            onClick={() => router.replace(ROUTES.afterLogin)}
            className="absolute right-0 top-0 h-10 w-10 rounded-full border border-slate-200 bg-white text-slate-500 text-lg font-semibold hover:text-slate-800 hover:border-slate-300 transition"
            aria-label="Kembali ke Dashboard"
            title="Kembali"
          >
            ×
          </button>
          <div className="text-center mb-12">
            <p className="text-xs font-semibold tracking-[0.3em] uppercase text-slate-400 mb-3">Top Up</p>
            <h1 className="text-3xl md:text-4xl font-black text-slate-900 mb-3">Top Up Coins</h1>
            <p className="text-sm text-slate-500">Pilih paket coin favorit kamu, proses cepat & aman.</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm text-center">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {COIN_PACKAGES.map((pkg) => (
              <div
                key={pkg.id}
                className="rounded-3xl border border-slate-200 bg-white/80 backdrop-blur px-6 py-7 shadow-[0_12px_30px_rgba(15,23,42,0.08)]"
              >
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900">
                    Rp {pkg.price.toLocaleString('id-ID')}
                  </span>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-[0.25em]">IDR</span>
                </div>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-3xl font-black text-amber-500">{pkg.coins}</span>
                  <span className="text-sm text-slate-500">Coins</span>
                </div>
                <p className="mt-3 text-xs text-slate-400">{pkg.description}</p>
                <button
                  onClick={() => handlePay(pkg.id)}
                  disabled={loadingId === pkg.id}
                  className="mt-6 w-full py-3 rounded-full bg-slate-900 text-white text-sm font-semibold tracking-wide hover:bg-slate-800 transition disabled:opacity-60"
                >
                  {loadingId === pkg.id ? 'Memproses...' : 'Tambah Coins'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
      {debugPanel}
    </>
  );
}
