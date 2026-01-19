'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

export default function HelpPage() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-white px-6 py-16">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-black text-gray-800 uppercase tracking-wide mb-4">Panduan Unduh Data TikTok</h1>
        <p className="text-sm text-gray-500 mb-10">
          Tutorial mengunduh data TikTok agar dapat dianalisis AI kami.
        </p>

        <div className="space-y-8 text-sm text-gray-700">
          <section id="tiktok-data">
            <h2 className="text-lg font-bold text-gray-800 mb-2">Langkah-langkah</h2>
            <ol className="list-decimal pl-5 space-y-4">
              <li>
                <span className="font-semibold">Buka aplikasi TikTok → Settings & Privacy.</span>
                <div className="mt-4">
                  <img
                    src="/help/Settings%20%26%20Privacy.jpeg"
                    alt="Settings & Privacy"
                    className="w-full max-w-sm rounded-xl border border-slate-200"
                  />
                </div>
              </li>
              <li>
                <span className="font-semibold">Masuk ke “Download your data”.</span>
                <div className="mt-4">
                  <img
                    src="/help/Download%20your%20data.jpeg"
                    alt="Download your data"
                    className="w-full max-w-sm rounded-xl border border-slate-200"
                  />
                </div>
              </li>
              <li>
                <span className="font-semibold">Pilih format data (JSON atau TXT). Centang hanya Postingan dan TikTok Shop, lalu klik Minta data.</span>
                <div className="mt-4">
                  <img
                    src="/help/Format%20data.jpeg"
                    alt="Format data"
                    className="w-full max-w-sm rounded-xl border border-slate-200"
                  />
                </div>
              </li>
              <li>
                <span className="font-semibold">Setelah data TikTok sudah ada maka klik “Unduh data”.</span>
                <div className="mt-4">
                  <img
                    src="/help/Hasil%20unduh%20data.jpeg"
                    alt="Hasil unduh data"
                    className="w-full max-w-sm rounded-xl border border-slate-200"
                  />
                </div>
              </li>
            </ol>
            <p className="mt-2 text-xs text-gray-500">
              Kami tidak memerlukan DM, dompet, atau data sensitif lainnya.
            </p>
          </section>
        </div>

        <div className="mt-10">
          <button
            onClick={() => router.replace('/app?dashboard=1')}
            className="px-6 py-3 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition"
          >
            Kembali ke Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
