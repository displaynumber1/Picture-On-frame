'use client';

// Usage: import IdentitySelector from `frontend/components/IdentitySelector`
// and render it in the generate form area.

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getIdentityStatus, type IdentityStatus } from '../lib/identityApi';
import { supabaseService } from '../services/supabaseService';

export type IdentityMode = 'none' | 'avatar';

type IdentitySelectorProps = {
  accessToken?: string;
  onChange?: (mode: IdentityMode) => void;
};

export default function IdentitySelector({ accessToken, onChange }: IdentitySelectorProps) {
  const [status, setStatus] = useState<IdentityStatus | null>(null);
  const [mode, setMode] = useState<IdentityMode>('none');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  useEffect(() => {
    onChange?.(mode);
  }, [mode, onChange]);

  const state = status?.state ?? 'NO_AVATAR';
  const canUseAvatar = state === 'ACTIVE';

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Gunakan Avatar</h4>
        {canUseAvatar && (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
            Avatar aktif
          </span>
        )}
      </div>

      <p className="mt-1 text-[11px] text-gray-500">
        Avatar hanya diperlukan untuk wajah konsisten.
      </p>

      {isLoading && (
        <p className="mt-3 text-xs text-gray-500">Memuat status avatar…</p>
      )}

      {!isLoading && error && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          {error} · Default ke tanpa avatar.
        </p>
      )}

      {!isLoading && (
        <div className="mt-3 space-y-2 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="identity-mode"
              checked={mode === 'none'}
              onChange={() => setMode('none')}
            />
            <span>Tanpa Avatar</span>
          </label>

          {canUseAvatar && (
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="identity-mode"
                checked={mode === 'avatar'}
                onChange={() => setMode('avatar')}
              />
              <span>Gunakan Avatar Saya</span>
            </label>
          )}
        </div>
      )}

      {!isLoading && !canUseAvatar && (
        <div className="mt-3 text-xs text-gray-600">
          <Link href="/app/avatar/enroll" className="font-semibold underline hover:text-gray-900">
            Buat Avatar untuk wajah konsisten
          </Link>
        </div>
      )}
    </div>
  );
}
