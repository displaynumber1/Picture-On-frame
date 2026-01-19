# Panduan Admin & Role User

Dokumen ini menjelaskan cara admin melihat, mengedit, mengupload data, serta batasan akses user biasa vs admin.

## 1) Peran (Role)
Role disimpan di Supabase pada kolom `profiles.role_user`.

- `admin`
  - Bisa melihat dan mengelola data admin.
  - Bisa melihat log auto-post lintas user (panel admin).
  - Bisa upload/refresh CSV tren (RAG).
- `user`
  - Hanya bisa mengakses data miliknya sendiri.
  - Tidak bisa melihat log admin, tidak bisa upload/refresh tren.

## 2) Panduan Admin (Dashboard)

### 2.1 Melihat log Auto-Post (admin-only)
Panel: **Admin Autopost Logs** (di Dashboard).

Fungsi:
- Lihat aktivitas video terbaru lintas user.
- Lihat status, score, dan engagement (views/likes/comments/shares).
- Filter:
  - Cari user
  - Filter status (QUEUED / IN_PROGRESS / WAITING_RECHECK / POSTED / FAILED)
  - Filter tanggal (from / to)
  - Limit tampilan (25 / 50 / 100)

Catatan:
- Panel ini hanya tampil jika role `admin`.

### 2.2 Upload/Refresh Trend CSV (admin-only)
Panel: **Trend CSV** (di Dashboard).

Langkah upload:
1. Klik **Upload CSV**.
2. Pastikan format CSV: `category,hashtag,weight`.
3. Sistem akan validasi schema dan menampilkan error jika ada.
4. Jika valid, data diimport ke index tren (RAG/Qdrant).

Refresh data:
1. Klik **Refresh** untuk reload tren terbaru dari server.

Template CSV:
1. Klik **Download Template** untuk contoh format.

### 2.3 Edit Data (admin-only)
Saat ini edit data tren dilakukan dengan:
- Upload ulang CSV yang sudah diperbaiki.
- Tidak ada editor langsung di UI (masih berbasis CSV).

## 3) Panduan User Biasa

User biasa **bisa**:
- Login & akses studio/generator.
- Upload video untuk auto-post.
- Melihat status video miliknya di dashboard.
- Melihat templates, insights, dan competitor data miliknya.

User biasa **tidak bisa**:
- Mengakses panel admin log.
- Mengupload/refresh data tren CSV.
- Melihat data user lain.

## 4) Pengaturan Role Admin (SQL)
Untuk menjadikan user admin:

```sql
UPDATE public.profiles
SET role_user = 'admin'
WHERE user_id = (
  SELECT id FROM auth.users WHERE email = 'admin@email.com'
);
```

## 5) Keamanan
- Akses admin dipaksa di backend (server-side).
- User biasa tidak bisa melihat data admin walau memanipulasi UI.
