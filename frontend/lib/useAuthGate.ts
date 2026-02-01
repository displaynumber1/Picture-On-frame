import { useEffect, useState } from 'react';
import { supabaseService } from '../services/supabaseService';

export function useAuthGate() {
  const [ready, setReady] = useState(false);
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    let unsub: { unsubscribe?: () => void } | null = null;

    (async () => {
      try {
        const supabase = (supabaseService as any).getClient?.() ?? supabaseService.supabase ?? supabaseService;
        const { data } = await supabase.auth.getSession();
        setSession(data?.session ?? null);
      } catch (error) {
        console.error('[AUTH_GATE] getSession failed', error);
        setSession(null);
      } finally {
        setReady(true);
      }

      try {
        const supabase = (supabaseService as any).getClient?.() ?? supabaseService.supabase ?? supabaseService;
        const { data } = supabase.auth.onAuthStateChange((_event: any, sess: any) => {
          console.log('[AUTH_GATE] onAuthStateChange', _event, Boolean(sess));
          setSession(sess ?? null);
          setReady(true);
        });
        unsub = data?.subscription ?? null;
      } catch (error) {
        console.error('[AUTH_GATE] subscribe failed', error);
      }
    })();

    return () => {
      try {
        unsub?.unsubscribe?.();
      } catch {
        // ignore
      }
    };
  }, []);

  const user = session?.user ?? null;
  return { ready, session, user };
}
