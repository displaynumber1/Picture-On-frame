'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseService } from '../../services/supabaseService';
import { midtransService } from '../../services/midtransService';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type BillingStatus = {
  subscribed: boolean;
  status: 'active' | 'expired' | 'inactive';
  subscribed_until: string | null;
  expires_in_days: number | null;
  renew_window: boolean;
};

export default function BillingPage() {
  const router = useRouter();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
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
  };

  useEffect(() => {
    fetchStatus();
  }, []);

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

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Billing</h1>
            <p className="text-sm text-gray-500">Kelola status Pro dan langganan</p>
          </div>
          <button
            onClick={() => router.push('/app')}
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
            onClick={fetchStatus}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
}
