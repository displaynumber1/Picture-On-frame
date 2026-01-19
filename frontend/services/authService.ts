// Authentication service with Google OAuth
export interface User {
  email: string;
  name?: string;
  role?: string;
  picture?: string;
}

const AUTH_KEY = 'picture_on_frame_auth';
const USER_KEY = 'picture_on_frame_user';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const authService = {
  loginWithGoogle: async (token: string): Promise<User> => {
    try {
      const response = await fetch(`${API_URL}/api/verify-google-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      const user: User = {
        email: data.email,
        name: data.name,
        role: data.role,
        picture: data.picture,
      };

      localStorage.setItem(AUTH_KEY, 'true');
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      return user;
    } catch (err: any) {
      throw new Error(err.message || 'Login failed. Please try again.');
    }
  },

  logout: (): void => {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_KEY);
  },

  isAuthenticated: (): boolean => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(AUTH_KEY) === 'true';
  },

  getCurrentUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
};

