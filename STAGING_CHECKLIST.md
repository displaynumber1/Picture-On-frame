# Staging Checklist (pictureonframe.site)

## Pre-deploy (minimal)
- [ ] Staging env vars set (backend + frontend)
- [ ] Supabase redirect URLs include `https://pictureonframe.site/auth/callback`
- [ ] Google OAuth redirect URI includes `https://<project-ref>.supabase.co/auth/v1/callback`

## Deploy
- [ ] Deploy backend to staging
- [ ] Deploy frontend to staging

## Post-deploy verification
- [ ] `GET /health` returns 200
- [ ] `GET /ready` returns 200 or 503 with `supabase_env: ok`
- [ ] Google login redirects to `/auth/callback` then `/generator`
- [ ] No duplicate `token?grant_type=pkce` in network
- [ ] `/api/auth/ensure-access` returns 200 with Supabase JWT
- [ ] Generate flow works (image or video)

## Rollback plan
- [ ] Roll back frontend deploy (previous build)
- [ ] Roll back backend deploy (previous build)
