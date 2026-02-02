'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '../../lib/routes';
import { DebugPanel, useDebugEnabled, useDebugTimestamp } from '../../lib/debugPanel';
import { useAuthGate } from '../../lib/useAuthGate';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { ready, session, user } = useAuthGate();
  const debugEnabled = useDebugEnabled();
  const timestamp = useDebugTimestamp();

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
      {children}
      {debugPanel}
    </>
  );
}
