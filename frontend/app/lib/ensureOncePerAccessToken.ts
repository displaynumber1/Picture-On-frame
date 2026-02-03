const KEY = 'ensure_registered_access_token_v1';

let inFlight: Promise<void> | null = null;

export async function ensureOncePerAccessToken(
  getAccessToken: () => Promise<string | null>,
  ensureFn: () => Promise<void>
) {
  const token = await getAccessToken();
  if (!token) return;

  const cached = sessionStorage.getItem(KEY);
  if (cached === token) return;

  if (inFlight) {
    await inFlight;
    const cachedAfter = sessionStorage.getItem(KEY);
    if (cachedAfter === token) return;
  }

  inFlight = (async () => {
    await ensureFn();
    sessionStorage.setItem(KEY, token);
  })();

  try {
    await inFlight;
  } finally {
    inFlight = null;
  }
}

export function clearEnsureCache() {
  sessionStorage.removeItem(KEY);
}
