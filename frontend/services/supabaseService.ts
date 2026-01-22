/**
 * Supabase client service
 */
import { createClient, SupabaseClient, Session } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const isValidSupabaseUrl = /^https?:\/\//i.test(supabaseUrl);

// Create a dummy client if credentials are missing to prevent runtime errors
// User should configure .env.local with actual credentials
let supabase: SupabaseClient;

if (!supabaseUrl || !supabaseAnonKey || !isValidSupabaseUrl || supabaseUrl.includes('your-project') || supabaseAnonKey.includes('your-anon')) {
  console.warn('⚠️ Supabase credentials not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local');
  // Create a dummy client with placeholder values to prevent crash
  // This will fail on actual API calls, but won't crash the app on load
  supabase = createClient('https://placeholder.supabase.co', 'placeholder-key');
} else {
  supabase = createClient(supabaseUrl, supabaseAnonKey);
}

export interface UserProfile {
  id: string;
  user_id: string;
  display_name?: string | null;
  avatar_url?: string | null;
  free_image_quota: number;
  coins_balance: number;
  trial_upload_remaining?: number | null;
  subscribed?: boolean | null;
  created_at: string;
  updated_at: string;
}

// Export supabase client directly for use in components
export { supabase };

export const supabaseService = {
  // Expose supabase client
  supabase,
  _authSubscription: null as { unsubscribe: () => void } | null,
  _authCallbacks: new Set<(event: string, session: Session | null) => void>(),

  subscribeToAuthChanges(callback: (event: string, session: Session | null) => void) {
    this._authCallbacks.add(callback);
    if (!this._authSubscription) {
      const response = supabase.auth.onAuthStateChange((event, session) => {
        this._authCallbacks.forEach((cb) => cb(event, session));
      });
      this._authSubscription = response.data.subscription;
    }
    return () => {
      this._authCallbacks.delete(callback);
      if (this._authCallbacks.size === 0 && this._authSubscription) {
        this._authSubscription.unsubscribe();
        this._authSubscription = null;
      }
    };
  },
  
  /**
   * Get current user's profile
   */
  async getProfile(): Promise<UserProfile | null> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return null;

      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (error) {
        console.error('Error fetching profile:', error);
        return null;
      }

      return data as UserProfile;
    } catch (error) {
      console.error('Error in getProfile:', error);
      return null;
    }
  },

  /**
   * Get current session
   */
  async getSession() {
    return await supabase.auth.getSession();
  },

  /**
   * Sign in with Google
   */
  async signInWithGoogle() {
    return await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/generator`,
        queryParams: {
          prompt: 'select_account'
        }
      }
    });
  },

  /**
   * Sign out
   */
  async signOut() {
    return await supabase.auth.signOut();
  },

  /**
   * Get current user
   */
  async getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  },

  /**
   * Get access token for API calls
   */
  async getAccessToken(): Promise<string | null> {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  }
};

