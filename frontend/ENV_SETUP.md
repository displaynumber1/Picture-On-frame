# Setup Environment Variables

## File yang Perlu Dibuat

Buat file `.env.local` di folder `frontend/` dengan isi berikut:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
# Get these from your Supabase project settings: https://app.supabase.com/project/_/settings/api
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Google OAuth Client ID (for Google login)
# Get this from Google Cloud Console: https://console.cloud.google.com/apis/credentials
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
```

**Catatan:**
- File `.env.local` digunakan oleh Next.js untuk environment variables
- File ini akan di-ignore oleh git (tidak akan ter-commit)
- Setelah membuat file, **restart development server** agar perubahan terdeteksi

## Cara Membuat File

### Windows (PowerShell):
```powershell
cd frontend
New-Item -Path .env.local -ItemType File -Force
Add-Content -Path .env.local -Value "NEXT_PUBLIC_API_URL=http://localhost:8000"
Add-Content -Path .env.local -Value "NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co"
Add-Content -Path .env.local -Value "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here"
Add-Content -Path .env.local -Value "NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here"
```

### Windows (Command Prompt):
```cmd
cd frontend
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
echo NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co >> .env.local
echo NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here >> .env.local
echo NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here >> .env.local
```

### Mac/Linux:
```bash
cd frontend
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
EOF
```

## Cara Mendapatkan Kredensial

### 1. Supabase Configuration

1. Buka https://app.supabase.com dan login
2. Pilih project Anda (atau buat project baru)
3. Buka **Settings** → **API**
4. Salin nilai berikut:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon/public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Catatan:** Gunakan **anon/public key** (bukan service_role key) untuk frontend karena key ini aman untuk diekspos di client-side.

### 2. Google OAuth Client ID

1. Buka https://console.cloud.google.com
2. Pilih project Anda (atau buat project baru)
3. Buka **APIs & Services** → **Credentials**
4. Klik **Create Credentials** → **OAuth client ID**
5. Pilih **Web application**
6. Tambahkan **Authorized redirect URIs**: `http://localhost:3000` (untuk development)
7. Salin **Client ID** → `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

### 3. Setup File .env.local

1. Buka file `.env.local` di folder `frontend/`
2. Ganti placeholder dengan nilai yang sebenarnya:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
   ```
3. **Restart development server** agar perubahan terdeteksi:
   ```bash
   npm run dev
   ```

## Verifikasi

Pastikan semua variabel environment sudah terkonfigurasi:
- ✅ `NEXT_PUBLIC_SUPABASE_URL` - URL project Supabase
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Anon key dari Supabase
- ✅ `NEXT_PUBLIC_GOOGLE_CLIENT_ID` - Client ID dari Google Cloud Console
- ✅ `NEXT_PUBLIC_API_URL` - URL backend API (default: http://localhost:8000)

**Catatan Penting:**
- File `.env.local` akan di-ignore oleh git (tidak akan ter-commit)
- Jangan commit file `.env.local` ke repository
- Untuk production, set environment variables di hosting platform (Vercel, Netlify, dll)

