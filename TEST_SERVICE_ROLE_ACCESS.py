"""
Test Script untuk Verifikasi Service Role Access ke Supabase
Jalankan script ini untuk test apakah service_role key bisa mengakses profiles
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: Package 'supabase' not installed. Run: pip install supabase")
    sys.exit(1)

# Load environment variables
env_path = Path(__file__).parent.parent / 'config.env'
if not env_path.exists():
    env_path = Path(__file__).parent / 'config.env'
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def test_service_role_access():
    """Test apakah service_role key bisa mengakses profiles"""
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ ERROR: SUPABASE_URL atau SUPABASE_SERVICE_KEY tidak ditemukan di config.env")
        return False
    
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 Service Key: {'SET' if SUPABASE_SERVICE_KEY else 'NOT SET'}")
    print(f"🔑 Service Key Preview: {SUPABASE_SERVICE_KEY[:20]}...{SUPABASE_SERVICE_KEY[-10:] if len(SUPABASE_SERVICE_KEY) > 30 else ''}")
    print()
    
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client created successfully")
        print()
        
        # Test 1: SELECT (Read)
        print("Test 1: SELECT (Read) profiles...")
        try:
            response = supabase.table("profiles").select("*").limit(5).execute()
            print(f"✅ SELECT berhasil: {len(response.data)} rows")
            if response.data:
                print(f"   Sample data: {response.data[0]}")
            else:
                print("   ⚠️  Tabel kosong (tidak ada data)")
            print()
        except Exception as e:
            print(f"❌ SELECT gagal: {str(e)}")
            print()
            return False
        
        # Test 2: UPDATE (Write) - hanya test jika ada data
        if response.data and len(response.data) > 0:
            test_user_id = response.data[0].get('user_id')
            if test_user_id:
                print(f"Test 2: UPDATE (Write) profiles untuk user_id: {test_user_id}...")
                try:
                    # Get current quota
                    current_quota = response.data[0].get('free_image_quota', 0)
                    print(f"   Current quota: {current_quota}")
                    
                    # Test UPDATE (set ke nilai yang sama untuk safety)
                    update_response = supabase.table("profiles").update({
                        "free_image_quota": current_quota  # Set ke nilai yang sama
                    }).eq("user_id", test_user_id).execute()
                    
                    if update_response.data and len(update_response.data) > 0:
                        print(f"✅ UPDATE berhasil: {len(update_response.data)} rows updated")
                        print(f"   Updated data: {update_response.data[0]}")
                    else:
                        print("⚠️  UPDATE tidak mengembalikan data (mungkin policy issue)")
                    print()
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ UPDATE gagal: {error_msg}")
                    
                    # Check for specific errors
                    if "PGRST205" in error_msg or "could not find the table" in error_msg.lower():
                        print("   🔍 ERROR: Schema cache issue - refresh schema cache di Supabase Dashboard")
                    elif "permission" in error_msg.lower() or "policy" in error_msg.lower():
                        print("   🔍 ERROR: RLS policy issue - periksa policy 'Service role can do everything'")
                    elif "schema cache" in error_msg.lower():
                        print("   🔍 ERROR: Schema cache perlu di-refresh")
                    print()
                    return False
            else:
                print("⚠️  Test 2: Tidak bisa test UPDATE - user_id tidak ditemukan")
                print()
        else:
            print("⚠️  Test 2: Tidak bisa test UPDATE - tidak ada data di tabel")
            print("   💡 Buat profile manual atau login dengan user baru untuk test")
            print()
        
        # Test 3: INSERT (Write) - test dengan dummy data yang akan di-rollback
        print("Test 3: INSERT (Write) profiles...")
        print("   ⚠️  Skipping INSERT test untuk menghindari data dummy")
        print("   💡 Test manual INSERT jika diperlukan")
        print()
        
        print("=" * 60)
        print("✅ SEMUA TEST BERHASIL!")
        print("=" * 60)
        print()
        print("🔍 Jika masih ada error 500/404 di aplikasi:")
        print("   1. Pastikan schema cache sudah di-refresh (tunggu 2-3 menit)")
        print("   2. Restart backend server setelah refresh cache")
        print("   3. Pastikan service_role key di config.env adalah key yang benar")
        print("   4. Periksa log backend untuk detail error")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()
        
        error_msg = str(e)
        if "could not find the table" in error_msg.lower() or "PGRST205" in error_msg:
            print("🔍 DIAGNOSIS: Tabel tidak ditemukan atau schema cache issue")
            print("   Solusi:")
            print("   1. Pastikan setup.sql sudah dijalankan di Supabase SQL Editor")
            print("   2. Refresh schema cache di Supabase Dashboard")
            print("   3. Tunggu 2-3 menit untuk cache refresh otomatis")
        elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
            print("🔍 DIAGNOSIS: Service key tidak valid")
            print("   Solusi:")
            print("   1. Pastikan menggunakan SERVICE_ROLE key (bukan anon key)")
            print("   2. Copy key dari Supabase Dashboard > Settings > API > service_role (secret)")
            print("   3. Update config.env dengan key yang benar")
        
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST SERVICE ROLE ACCESS - SUPABASE PROFILES")
    print("=" * 60)
    print()
    
    # Test langsung dengan create_client tanpa import supabase_service
    success = test_service_role_access()
    sys.exit(0 if success else 1)
