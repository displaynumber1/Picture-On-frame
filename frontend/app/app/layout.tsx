'use client';

import React from 'react';
import { DebugPanel, useDebugEnabled, useDebugTimestamp } from '../../lib/debugPanel';
import AuthGate from './_components/AuthGate';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const debugEnabled = useDebugEnabled();
  const timestamp = useDebugTimestamp();

  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const debugPanel = debugEnabled ? (
    <DebugPanel
      ready={true}
      hasSession={true}
      userEmail=""
      pathname={currentPath}
      origin={origin}
      timestamp={timestamp}
    />
  ) : null;

  return (
    <AuthGate>
      {children}
      {debugPanel}
    </AuthGate>
  );
}
