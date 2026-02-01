'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseService } from '../../../services/supabaseService';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [message, setMessage] = useState('Signing you in...');
  const [showRetry, setShowRetry] = useState(false);
  const didRun = useRef(false);

  useEffect(() => {
    if (didRun.current) {
      return;
    }
    didRun.current = true;
    let mounted = true;
    const redirectToGenerator = () => {
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('auth_redirected', Date.now().toString());
        window.location.href = '/generator';
        // Fallbacks in case navigation is blocked or interrupted.
        setTimeout(() => {
          window.location.assign('/generator');
        }, 100);
        setTimeout(() => {
          if (window.location.pathname === '/auth/callback') {
            window.location.assign('/generator');
          }
        }, 600);
        return;
      }
      router.replace('/generator');
    };
    const timeoutId = setTimeout(() => {
      if (mounted) {
        setMessage('Login terlalu lama. Silakan coba lagi.');
        setShowRetry(true);
      }
    }, 8000);
    const waitForSession = async () => {
      for (let i = 0; i < 6; i += 1) {
        const { data } = await supabaseService.supabase.auth.getSession();
        if (data?.session) {
          return true;
        }
        await new Promise((resolve) => setTimeout(resolve, 200));
      }
      return false;
    };
    const handleCallback = async () => {
      try {
        if (typeof window === 'undefined') {
          return;
        }
        console.log('[AUTH] origin=', window.location.origin, 'path=', window.location.pathname);
        const params = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash.replace('#', ''));
        const code = params.get('code');
        const errorParam = params.get('error');
        const errorDescription = params.get('error_description');
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');

        if (errorParam) {
          if (errorParam === 'server_error' && errorDescription?.includes('flow_state_not_found')) {
            console.warn('[AuthCallback] flow_state_not_found, redirecting to login');
            if (mounted) {
              clearTimeout(timeoutId);
              setMessage('Login state hilang. Silakan login ulang.');
              setShowRetry(true);
              setTimeout(() => {
                router.replace('/login');
              }, 800);
            }
            return;
          }
          throw new Error(errorDescription || errorParam);
        }

        if (code) {
          console.info('[AuthCallback] Detected code flow');
          const guardKey = `pkce_exchanged_${code}`;
          if (sessionStorage.getItem(guardKey)) {
            if (mounted) {
              clearTimeout(timeoutId);
              redirectToGenerator();
            }
            return;
          }
          sessionStorage.setItem(guardKey, '1');
          const { error } = await supabaseService.supabase.auth.exchangeCodeForSession(code);
          console.info('[AuthCallback] exchangeCodeForSession', error ? 'error' : 'ok');
          if (error) {
            throw error;
          }
          const ready = await waitForSession();
          console.info('[AuthCallback] waitForSession', ready ? 'ok' : 'timeout');
          if (mounted) {
            clearTimeout(timeoutId);
            if (!ready) {
              throw new Error('Session not ready');
            }
            window.history.replaceState(null, '', '/auth/callback');
            redirectToGenerator();
          }
          return;
        }

        if (accessToken && refreshToken) {
          console.info('[AuthCallback] Detected implicit hash flow');
          const guardKey = `implicit_session_${accessToken.slice(0, 12)}`;
          if (!sessionStorage.getItem(guardKey)) {
            sessionStorage.setItem(guardKey, '1');
            const { error } = await supabaseService.supabase.auth.setSession({
              access_token: accessToken,
              refresh_token: refreshToken
            });
            console.info('[AuthCallback] setSession', error ? 'error' : 'ok');
            if (error) {
              throw error;
            }
            const ready = await waitForSession();
            console.info('[AuthCallback] waitForSession', ready ? 'ok' : 'timeout');
            if (!ready) {
              throw new Error('Session not ready');
            }
          }
        }

        const { data } = await supabaseService.supabase.auth.getSession();
        console.info('[AuthCallback] getSession', data?.session ? 'ok' : 'empty');
        if (data?.session && mounted) {
          clearTimeout(timeoutId);
            window.history.replaceState(null, '', '/auth/callback');
            redirectToGenerator();
          window.history.replaceState(null, '', '/auth/callback');
          redirectToGenerator();
          return;
        }

        throw new Error('Missing auth code');
      } catch (error: any) {
        if (mounted) {
          const message = typeof error?.message === 'string' ? error.message : '';
          const display = message
            ? `Login gagal: ${message}. Pastikan redirect URL benar dan tidak ada exchange ganda.`
            : 'Login gagal. Mengarahkan ke halaman login...';
          setMessage(display);
          setShowRetry(true);
          console.error('OAuth callback error:', error);
          setTimeout(() => {
            router.replace('/login');
          }, 1200);
        }
      }
    };
    handleCallback();
    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-gray-600">
      <div>{message}</div>
      {showRetry ? (
        <button
          type="button"
          onClick={() => router.replace('/login')}
          className="px-4 py-2 rounded-md bg-purple-600 text-white hover:bg-purple-700"
        >
          Retry
        </button>
      ) : null}
      {showRetry ? (
        <button
          type="button"
          onClick={() => {
            if (typeof window !== 'undefined') {
              window.location.href = '/generator';
            } else {
              router.replace('/generator');
            }
          }}
          className="px-4 py-2 rounded-md border border-purple-600 text-purple-700 hover:bg-purple-50"
        >
          Go to Generator
        </button>
      ) : null}
    </div>
  );
}
