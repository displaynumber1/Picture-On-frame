'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Session } from '@supabase/supabase-js';
import { supabaseService } from '../services/supabaseService';
import LoginPage from './LoginPage';

const AuthLanding: React.FC = () => {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    let subscription: { unsubscribe: () => void } | null = null;

    try {
      if (supabaseService.supabase) {
        subscription = {
          unsubscribe: supabaseService.subscribeToAuthChanges((_event, session) => {
            setSession(session ?? null);
            if (!initializedRef.current) {
              initializedRef.current = true;
              setAuthReady(true);
            }
          })
        };

        // Speed up OAuth redirects by reading the current session immediately.
        // (onAuthStateChange can be delayed on some networks/devices.)
        (async () => {
          try {
            const { data } = await supabaseService.getSession();
            if (data?.session) {
              setSession(data.session);
            }
          } catch (error) {
            console.error('Error getting initial session:', error);
          } finally {
            if (!initializedRef.current) {
              initializedRef.current = true;
              setAuthReady(true);
            }
          }
        })();
      } else {
        setAuthReady(true);
      }
    } catch (error) {
      console.error('Error setting up auth listener:', error);
      setAuthReady(true);
    }

    return () => {
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, []);

  useEffect(() => {
    if (!authReady) return;
    if (session) {
      router.replace('/app');
    }
  }, [authReady, session, router]);

  if (!authReady) {
    return (
      <div className="min-h-screen flex items-center justify-center luxury-gradient-bg">
        <div className="text-center flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
          <div className="flex flex-col items-center gap-2">
            <div className="h-3 w-40 rounded-full bg-white/20 animate-pulse"></div>
            <div className="h-2 w-24 rounded-full bg-white/15 animate-pulse"></div>
          </div>
          <p className="text-white/70 text-sm">Menyiapkan tools AI...</p>
        </div>
      </div>
    );
  }

  if (session) {
    return null;
  }

  return <LoginPage />;
};

export default AuthLanding;
