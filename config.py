"""Pengaturan aplikasi Stokara.

Nilai rahasia (SECRET_KEY, MONGO_URI) dibaca dari file .env,
supaya tidak tertulis di kode dan tidak ikut ke GitHub.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()  # baca file .env lalu masukkan isinya ke os.environ


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    TESTING = False

    # Keamanan cookie session
    SESSION_COOKIE_HTTPONLY = True     # cookie tidak bisa dibaca JavaScript
    SESSION_COOKIE_SAMESITE = "Lax"    # cookie tidak ikut terkirim dari situs lain
    SESSION_COOKIE_SECURE = os.getenv("FLASK_DEBUG") != "1"  # di Vercel hanya lewat HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)          # 1 shift kerja

    # Identitas gudang. Ditampilkan setelah pengguna login.
    NAMA_BRANCH = "Branch Semarang"

    # Angka untuk dashboard insight (bisa diubah tanpa menyentuh rumus)
    PERIODE_HARI = 30           # insight dihitung dari 30 hari terakhir
    HARI_PENGAMAN = 2           # safety stock = demand per hari x 2 hari
    PERIODE_CADANGAN_HARI = 7   # saran restock mencukupi lead time + 7 hari


class TestConfig(Config):
    """Dipakai saat menjalankan pytest: database palsu di memori."""
    TESTING = True
    SECRET_KEY = "kunci-khusus-test"
    SESSION_COOKIE_SECURE = False
