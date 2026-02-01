import { useEffect, useMemo, useState } from 'react';

type DebugPanelProps = {
  ready: boolean;
  hasSession: boolean;
  userEmail?: string;
  pathname: string;
  origin: string;
  timestamp: string;
  authStuck?: boolean;
};

export function useDebugEnabled() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    try {
      const isQA = window.location.hostname.includes('pictureonframe.space');
      const hasDebug = new URLSearchParams(window.location.search).has('debug');
      setEnabled(isQA || hasDebug);
    } catch {
      setEnabled(false);
    }
  }, []);

  return enabled;
}

export function useDebugTimestamp() {
  return useMemo(() => new Date().toISOString(), []);
}

export function DebugPanel({
  ready,
  hasSession,
  userEmail,
  pathname,
  origin,
  timestamp,
  authStuck
}: DebugPanelProps) {
  return (
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
      <div><strong>[DEBUG]</strong></div>
      <div>ready: {String(ready)}</div>
      <div>hasSession: {String(hasSession)}</div>
      <div>userEmail: {userEmail || '-'}</div>
      <div>pathname: {pathname || '-'}</div>
      <div>origin: {origin || '-'}</div>
      <div>timestamp: {timestamp}</div>
      {authStuck ? <div style={{ color: '#fca5a5' }}>Auth init stuck</div> : null}
    </div>
  );
}
