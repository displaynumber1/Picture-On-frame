'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { supabaseService } from '../../../services/supabaseService';
import { ensureOncePerAccessToken, clearEnsureCache } from '../../lib/ensureOncePerAccessToken';
import { ensureRegisteredUser } from '../../services/ensureRegisteredUser';

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const setSessionCookie = () => {
    if (typeof document === 'undefined') return;
    document.cookie = 'aistudio_session=1; path=/; SameSite=Lax';
  };
  const clearSessionCookie = () => {
    if (typeof document === 'undefined') return;
    document.cookie = 'aistudio_session=; Max-Age=0; path=/; SameSite=Lax';
  };

  useEffect(() => {
    let sub: { unsubscribe?: () => void } | null = null;
    let cancelled = false;

    const run = async () => {
      const supabase = (supabaseService as any).getClient?.() ?? supabaseService.supabase ?? supabaseService;
      const { data } = await supabase.auth.getSession();
      const token = data?.session?.access_token ?? null;

      if (!token) {
        clearEnsureCache();
        clearSessionCookie();
        if (!cancelled) {
          setReady(false);
          router.replace('/login');
        }
        return;
      }

      await ensureOncePerAccessToken(async () => token, async () => {
        await ensureRegisteredUser(token);
      });

      if (!cancelled) {
        setSessionCookie();
        setReady(true);
      }

      const { data: listener } = supabase.auth.onAuthStateChange(async (_event: any, session: any) => {
        const nextToken = session?.access_token ?? null;
        if (!nextToken) {
          clearEnsureCache();
          clearSessionCookie();
          setReady(false);
          router.replace('/login');
          return;
        }

        await ensureOncePerAccessToken(async () => nextToken, async () => {
          await ensureRegisteredUser(nextToken);
        });

        setSessionCookie();
        setReady(true);
      });

      sub = listener?.subscription ?? null;
    };

    run();

    return () => {
      cancelled = true;
      sub?.unsubscribe?.();
    };
  }, [router, pathname]);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-sm opacity-70">Loading…</div>
      </div>
    );
  }

  return <>{children}</>;
}
