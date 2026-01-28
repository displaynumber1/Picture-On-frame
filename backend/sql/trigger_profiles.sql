-- Ensure profiles.user_id is unique for safe upserts.
ALTER TABLE public.profiles
ADD CONSTRAINT IF NOT EXISTS profiles_user_id_unique UNIQUE (user_id);

-- Create profile row when a new auth user is created.
CREATE OR REPLACE FUNCTION public.handle_new_user_profile()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (user_id, role_user, coins_balance, trial_upload_remaining, display_name)
  VALUES (NEW.id, 'user', 0, 3, NEW.raw_user_meta_data->>'full_name')
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_profile();
