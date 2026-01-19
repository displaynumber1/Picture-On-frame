# Skema & Teknologi Halaman Auto-Posting

Dokumen ini merangkum skema/teknologi yang saat ini dipakai di halaman Auto-Posting tanpa mengubah apa pun pada kode.

## 1) Frontend (UI & State)
- Stack: React + Next.js (client component).
- State utama: dashboard items, upload state, admin CSV state (preview, pagination, filter).
- Komponen utama: `frontend/App.tsx` (dashboard + studio + admin panel).

## 2) Autentikasi
- Provider: Supabase Auth.
- Mekanisme: `supabase.auth.onAuthStateChange` untuk mendeteksi sesi.
- Guard akses: routing ke `/app` hanya setelah auth siap dan sesi valid.

## 3) Realtime Update
- Transport: WebSocket.
- Endpoint: `/ws/autopost` (token dari Supabase access token).
- Tujuan: refresh status dashboard tanpa polling berat.

## 4) Autopost Dashboard API
- REST endpoints (backend):
  - `/api/autopost/dashboard` untuk list status.
  - `/api/autopost/templates` untuk hooks/CTA/caption.
  - `/api/autopost/insights` untuk insight & rekomendasi.
  - `/api/autopost/competitors` untuk data competitor.

## 5) Trend RAG (CSV + Vector DB)
- Sumber data: `backend/trends.csv` (format `category,hashtag,weight`).
- Embedding + vector search: Qdrant (vector DB).
- Admin panel:
  - Upload/refresh CSV.
  - Preview + pagination + search.
  - Filter by kategori.
  - Validasi schema (regex hashtag + whitelist kategori).

## 6) Keamanan & Error Handling
- Error detail dari API disanitasi di frontend.
- Detail troubleshooting/logging hanya muncul di backend log.
- Login hanya untuk user yang terdaftar di Supabase.

## 7) File/Folder Referensi
- `frontend/App.tsx` (UI & client logic).
- `frontend/components/LoginPage.tsx` (login UI).
- `frontend/services/supabaseService.ts` (auth & profile).
- `backend/main.py` (API, RAG, scoring, WebSocket).
- `backend/trends.csv` (data tren).
