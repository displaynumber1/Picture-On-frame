'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import App from '../../App';
import { ROUTES } from '../../lib/routes';
import { useAuthGate } from '../../lib/useAuthGate';

class AppErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error('[APP_CRASH]', error);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, color: '#b91c1c' }}>
          <div>App crashed. Please refresh or contact support.</div>
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.8 }}>{this.state.error.message}</div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function GeneratorPage() {
  const router = useRouter();
  const { ready, session, user } = useAuthGate();
  const [authStuck, setAuthStuck] = useState(false);
  const timestamp = useMemo(() => new Date().toISOString(), []);

  useEffect(() => {
    console.log('[GENERATOR] ready=', ready, 'session=', Boolean(session), 'user=', user?.email);
    if (ready && !session) {
      router.replace(ROUTES.login);
    }
  }, [ready, session, user, router]);

  useEffect(() => {
    if (ready) {
      setAuthStuck(false);
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setAuthStuck(true);
    }, 2000);
    return () => window.clearTimeout(timeoutId);
  }, [ready]);

  if (typeof window !== 'undefined') {
    console.log('[GENERATOR] render', window.location.origin, window.location.pathname);
  }

  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const hasSession = Boolean(session);
  const userEmail = user?.email || '';

  const debugPanel = (
    <div
      style={{
        position: 'fixed',
        right: 12,
        bottom: 12,
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.9)',
        color: '#e2e8f0',
        padding: '10px 12px',
        borderRadius: 8,
        fontSize: 12,
        lineHeight: 1.4,
        maxWidth: 320,
        boxShadow: '0 8px 20px rgba(0,0,0,0.25)'
      }}
    >
      <div><strong>[GENERATOR]</strong></div>
      <div>ready: {String(ready)}</div>
      <div>hasSession: {String(hasSession)}</div>
      <div>userEmail: {userEmail || '-'}</div>
      <div>currentPath: {currentPath || '-'}</div>
      <div>origin: {origin || '-'}</div>
      <div>timestamp: {timestamp}</div>
      {authStuck ? <div style={{ color: '#fca5a5' }}>Auth init stuck</div> : null}
    </div>
  );

  const routeMarker = (
    <div style={{ padding: 12, background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', fontSize: 12 }}>
      <strong>GENERATOR ROUTE ACTIVE</strong>
      <div style={{ marginTop: 4 }}>
        {origin || '-'}{currentPath || '-'}
      </div>
    </div>
  );

  if (!ready) {
    return (
      <div>
        {routeMarker}
        <div style={{ padding: 24 }}>
          {authStuck ? 'Auth init stuck' : 'Loading session…'}
        </div>
        {debugPanel}
      </div>
    );
  }

  if (!session) {
    return (
      <div>
        {routeMarker}
        <div style={{ padding: 24 }}>Redirecting to login…</div>
        {debugPanel}
      </div>
    );
  }

  return (
    <div>
      {routeMarker}
      <AppErrorBoundary>
        <App />
      </AppErrorBoundary>
      {debugPanel}
    </div>
  );
}
