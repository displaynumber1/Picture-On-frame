"""
Database setup script for Premium AI Studio
Creates SQLite database and authorized_users table
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'premium_studio.db'

def setup_database():
    """Create database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create authorized_users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'user' NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Bootstrap admin users from environment (optional)
    raw_emails = os.getenv("BOOTSTRAP_ADMIN_EMAILS", "")
    if raw_emails:
        admin_emails = [email.strip().lower() for email in raw_emails.replace(";", ",").split(",") if email.strip()]
        for admin_email in admin_emails:
            try:
                cursor.execute('''
                    INSERT INTO authorized_users (email, role, created_at)
                    VALUES (?, ?, ?)
                ''', (admin_email, 'admin', datetime.now().isoformat()))
                print(f"✓ Admin user '{admin_email}' berhasil ditambahkan")
            except sqlite3.IntegrityError:
                print(f"ℹ Admin user '{admin_email}' sudah ada di database")
    else:
        print("ℹ BOOTSTRAP_ADMIN_EMAILS kosong, tidak ada admin yang di-seed")
    
    conn.commit()
    conn.close()
    print(f"✓ Database berhasil dibuat di: {DB_PATH}")

if __name__ == '__main__':
    setup_database()

