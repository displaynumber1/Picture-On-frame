# Deploy Playbook: Staging (pictureonframe.site)

## 1) Scope (minimal staging)
- Use **one Supabase project** (Option A).
- Only add **staging redirect URLs** in Supabase.
- Do **not** touch production.

## 2) Backend environment
Set these on the staging backend host:

```
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
FAL_KEY=
GEMINI_API_KEY=
GOOGLE_CLIENT_ID=
```

Restart backend service after setting env.

## 3) Supabase configuration (same project)
In Supabase Dashboard:
- Auth → Redirect URLs:
  - `https://pictureonframe.site/auth/callback`
- Google Provider:
  - Enabled with valid Client ID/Secret
- Google Cloud OAuth redirect:
  - `https://<project-ref>.supabase.co/auth/v1/callback`

## 4) Frontend environment
Set in staging frontend:

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=https://<staging-backend-host>
```

Deploy frontend.

## 5) Verification (minimal)
- `GET https://<staging-backend-host>/health` → 200
- `GET https://<staging-backend-host>/ready` → `supabase_env: ok`
- Google login → `/auth/callback` → `/generator`
- `POST /api/auth/ensure-access` returns 200 with Supabase JWT
- Generate flow works (image or video)

## 6) Rollback
- Redeploy previous backend build
- Redeploy previous frontend build
