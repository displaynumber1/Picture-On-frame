export type IdentityStatus = {
  state: 'NO_AVATAR' | 'PENDING_ENROLL' | 'ACTIVE' | 'PENDING_REFINE' | 'LOCKED' | 'REVOKED' | string;
  avatar_ref_url?: string | null;
  avatar_version?: number | null;
  [key: string]: unknown;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const buildAuthHeaders = (token?: string): Record<string, string> =>
  token ? { Authorization: `Bearer ${token}` } : {};

const parseError = async (response: Response): Promise<Error> => {
  try {
    const data = await response.json();
    const message =
      typeof data?.message === 'string'
        ? data.message
        : typeof data?.error === 'string'
          ? data.error
          : `Request failed with status ${response.status}`;
    return new Error(message);
  } catch {
    return new Error(`Request failed with status ${response.status}`);
  }
};

export const getIdentityStatus = async (token?: string): Promise<IdentityStatus> => {
  const response = await fetch(`${API_URL}/identity/status`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...buildAuthHeaders(token)
    }
  });

  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as IdentityStatus;
};

export const enrollIdentity = async (formData: FormData, token?: string): Promise<IdentityStatus> => {
  const response = await fetch(`${API_URL}/identity/enroll`, {
    method: 'POST',
    headers: {
      ...buildAuthHeaders(token)
    },
    body: formData
  });

  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as IdentityStatus;
};
