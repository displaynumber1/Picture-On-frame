'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '../../lib/routes';
import { DebugPanel, useDebugEnabled, useDebugTimestamp } from '../../lib/debugPanel';
import { supabaseService } from '../../services/supabaseService';
import { midtransService } from '../../services/midtransService';
import { useAuthGate } from '../../lib/useAuthGate';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type BillingStatus = {
  subscribed: boolean;
  status: 'active' | 'expired' | 'inactive';
  subscribed_until: string | null;
  expires_in_days: number | null;
  renew_window: boolean;
};

type BillingHistoryItem = {
  order_id: string;
  item_type: string;
  package_id?: string | null;
  gross_amount?: number | null;
  transaction_status?: string | null;
  payment_type?: string | null;
  created_at?: string | null;
};

export default function BillingPage() {
  const router = useRouter();
  const { ready, session, user } = useAuthGate();
  const debugEnabled = useDebugEnabled();
  const timestamp = useDebugTimestamp();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<BillingHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyFilter, setHistoryFilter] = useState<'all' | 'coins' | 'subscription'>('all');

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/billing/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Gagal memuat status billing.');
      }
      const data = await response.json();
      setStatus(data);
    } catch {
      setError('Gagal memuat status billing.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      setHistoryLoading(true);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        return;
      }
      const params = new URLSearchParams({ limit: '50' });
      if (historyFilter !== 'all') {
        params.set('item_type', historyFilter);
      }
      const response = await fetch(`${API_URL}/api/billing/history?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      setHistory(Array.isArray(data?.items) ? data.items : []);
    } finally {
      setHistoryLoading(false);
    }
  }, [historyFilter]);

  useEffect(() => {
    if (!ready || !session) return;
    fetchStatus();
    fetchHistory();
  }, [ready, session, fetchStatus, fetchHistory]);

  const handlePay = async () => {
    try {
      setPaying(true);
      setError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      await midtransService.loadSnapScript();
      const snapToken = await midtransService.initializeSubscriptionSnap(token, 30);
      const snap = (window as any).snap;
      if (!snap?.pay) {
        throw new Error('Midtrans Snap tidak tersedia.');
      }
      snap.pay(snapToken, {
        onSuccess: () => fetchStatus(),
        onPending: () => fetchStatus(),
        onError: () => setError('Pembayaran gagal. Silakan coba lagi.')
      });
    } catch (err: any) {
      setError(err?.message || 'Gagal memulai pembayaran.');
    } finally {
      setPaying(false);
    }
  };

  const badge = (label: string, classes: string) => (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${classes}`}>{label}</span>
  );

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
      <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Billing</h1>
            <p className="text-sm text-gray-500">Kelola status Pro dan langganan</p>
          </div>
          <button
            onClick={() => router.push(ROUTES.afterLogin)}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Kembali ke Dashboard
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Status Subscription</h2>
        {loading && <div className="text-sm text-gray-500">Memuat status...</div>}
        {error && <div className="text-sm text-red-600">{error}</div>}
        {!loading && status && (
          <div className="space-y-3 text-sm text-gray-700">
            <div className="flex items-center gap-2">
              <span>Status:</span>
              {status.status === 'active' && badge('Active', 'bg-green-100 text-green-700')}
              {status.status === 'expired' && badge('Expired', 'bg-red-100 text-red-700')}
              {status.status === 'inactive' && badge('Inactive', 'bg-gray-100 text-gray-600')}
            </div>
            <div>
              Berlaku sampai:{' '}
              <span className="text-gray-900">
                {status.subscribed_until ? new Date(status.subscribed_until).toLocaleDateString('id-ID') : '—'}
              </span>
            </div>
            <div>
              Sisa hari: <span className="text-gray-900">{status.expires_in_days ?? '—'}</span>
            </div>
            {status.renew_window && (
              <div className="text-xs text-amber-600">
                Masa aktif hampir habis. Disarankan perpanjang sekarang.
              </div>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handlePay}
            className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm disabled:opacity-60"
            disabled={paying}
          >
            {paying ? 'Memproses...' : 'Bayar via Midtrans'}
          </button>
          <button
            onClick={() => {
              fetchStatus();
              fetchHistory();
            }}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Refresh Status
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Riwayat Pembayaran</h2>
        <div className="flex items-center gap-2">
          <select
            value={historyFilter}
            onChange={(event) => setHistoryFilter(event.target.value as any)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700"
          >
            <option value="all">Semua</option>
            <option value="coins">Coins</option>
            <option value="subscription">Subscription</option>
          </select>
          <button
            onClick={async () => {
              const token = await supabaseService.getAccessToken();
              if (!token) return;
              const params = new URLSearchParams({ limit: '100' });
              if (historyFilter !== 'all') {
                params.set('item_type', historyFilter);
              }
              window.open(`${API_URL}/api/billing/history/pdf?${params.toString()}`, '_blank');
            }}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Export PDF
          </button>
        </div>
        {historyLoading && <div className="text-sm text-gray-500">Memuat riwayat...</div>}
        {!historyLoading && history.length === 0 && (
          <div className="text-sm text-gray-500">Belum ada transaksi.</div>
        )}
        {!historyLoading && history.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-400 uppercase tracking-wide">
                <tr className="text-left">
                  <th className="py-2">Tanggal</th>
                  <th className="py-2">Tipe</th>
                  <th className="py-2">Order</th>
                  <th className="py-2">Amount</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Payment</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, idx) => (
                  <tr key={`${item.order_id}-${idx}`} className="border-t border-gray-100">
                    <td className="py-3 text-gray-600">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID') : '—'}
                    </td>
                    <td className="py-3 text-gray-700">
                      {item.item_type === 'subscription' ? 'Subscription' : 'Coins'}
                    </td>
                    <td className="py-3 text-gray-700">{item.order_id}</td>
                    <td className="py-3 text-gray-700">
                      {item.gross_amount ? `Rp ${Number(item.gross_amount).toLocaleString('id-ID')}` : '—'}
                    </td>
                    <td className="py-3 text-gray-600">{item.transaction_status || '—'}</td>
                    <td className="py-3 text-gray-600">{item.payment_type || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      </div>
      {debugPanel}
    </>
  );
}
