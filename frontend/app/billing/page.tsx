'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '../../lib/routes';

export default function BillingRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(ROUTES.afterLogin);
  }, [router]);

  return <div style={{ padding: 24 }}>Redirecting…</div>;
}
