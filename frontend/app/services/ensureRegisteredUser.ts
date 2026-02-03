const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function ensureRegisteredUser(accessToken: string): Promise<void> {
  if (!accessToken) return;
  await fetch(`${API_URL}/api/auth/ensure-access`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` }
  });
}
