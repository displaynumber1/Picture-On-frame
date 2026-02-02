'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getIdentityStatus, type IdentityStatus } from '../lib/identityApi';
import { supabaseService } from '../services/supabaseService';

type CreateAvatarProps = {
  accessToken?: string;
};

export default function CreateAvatar({ accessToken }: CreateAvatarProps) {
  const [status, setStatus] = useState<IdentityStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadStatus = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const token = accessToken || (await supabaseService.getAccessToken());
        const data = await getIdentityStatus(token || undefined);
        if (isMounted) setStatus(data);
      } catch (err: any) {
        if (!isMounted) return;
        setError(typeof err?.message === 'string' ? err.message : 'Gagal memuat status avatar.');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadStatus();
    return () => {
      isMounted = false;
    };
  }, [accessToken]);

  const state = status?.state ?? 'NO_AVATAR';
  const avatarRefUrl = typeof status?.avatar_ref_url === 'string' ? status.avatar_ref_url : null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Avatar Konsisten</h3>
          <p className="text-xs text-gray-500">Gunakan avatar untuk wajah konsisten.</p>
        </div>
        {state === 'ACTIVE' && (
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            Avatar aktif
          </span>
        )}
      </div>

      {avatarRefUrl && !isLoading && !error && (
        <div className="mt-4 overflow-hidden rounded-xl border border-gray-100">
          <img src={avatarRefUrl} alt="Avatar preview" className="h-40 w-full object-cover" />
        </div>
      )}

      <div className="mt-4 text-sm text-gray-700">
        {isLoading && <p>Memuat status avatar…</p>}
        {!isLoading && error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>
        )}
        {!isLoading && !error && (
          <p>Status: <span className="font-semibold">{state}</span></p>
        )}
      </div>

      {state === 'NO_AVATAR' && !isLoading && (
        <div className="mt-4">
          <Link
            href="/app/avatar/enroll"
            className="inline-flex items-center justify-center rounded-xl bg-black px-4 py-2 text-sm font-semibold text-white transition hover:bg-gray-800"
          >
            Buat Avatar
          </Link>
        </div>
      )}

      {state === 'ACTIVE' && (
        <div className="mt-4">
          <Link
            href="/app/avatar/enroll"
            className="text-xs font-semibold text-gray-600 underline hover:text-gray-900"
          >
            Kelola / Perbarui Avatar
          </Link>
        </div>
      )}
    </div>
  );
}
