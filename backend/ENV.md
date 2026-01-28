# Backend Environment Setup

## Local development

Create `backend/.env.local` and add the variables below:

```
FAL_KEY=
GEMINI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
GOOGLE_CLIENT_ID=
```

Then run:

```
cd backend
uvicorn app.main:app --reload
```

## Notes
- Existing OS environment variables are never overridden.
- Load order: `backend/.env.local` → `backend/config.env` → project root `.env`.
