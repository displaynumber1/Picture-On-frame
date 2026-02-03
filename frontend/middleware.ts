import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_COOKIE = 'aistudio_session';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith('/app')) {
    // UX-only marker cookie; not a security boundary.
    // Real auth is enforced in AuthGate (client-side).
    const hasSessionMarker = request.cookies.get(AUTH_COOKIE)?.value === '1';
    if (!hasSessionMarker) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = '/login';
      loginUrl.search = '';
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/app/:path*']
};
