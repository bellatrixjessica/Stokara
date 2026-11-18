"""Cek koneksi ke MongoDB Atlas dan izin tulis ke database Stokara.

Jalankan dari folder D:\\Stokara:
    python scripts/cek_koneksi.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
db = app.db

try:
    db.command("ping")
    print("1. Koneksi ke Atlas      : OK")
except Exception as e:
    print("1. Koneksi ke Atlas      : GAGAL ->", type(e).__name__)
    sys.exit(1)

print("2. Nama database         :", db.name)

try:
    # Tulis satu dokumen percobaan, lalu hapus lagi.
    hasil = db.cek_koneksi.insert_one({"pesan": "tes tulis"})
    db.cek_koneksi.delete_one({"_id": hasil.inserted_id})
    db.drop_collection("cek_koneksi")
    print("3. Izin tulis            : OK")
except Exception as e:
    print("3. Izin tulis            : GAGAL ->", type(e).__name__)
    print("   User database belum punya izin ke database", db.name)
    sys.exit(1)

print("4. Collection yang ada   :", db.list_collection_names() or "(belum ada, database masih kosong)")
