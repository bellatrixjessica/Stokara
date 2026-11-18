"""Membuat 3 toko dan 6 akun contoh di database Stokara.

Jalankan dari folder D:\\Stokara:
    python scripts/seed_akun.py

Password semua akun diambil dari DEMO_PASSWORD di file .env.
Aman dijalankan berkali-kali: data yang sudah ada dilewati.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.models import user as model_user  # noqa: E402
from app.models.user import ADMIN, KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG  # noqa: E402

TOKO = [
    {"kode": "TK-01", "nama": "Toko Salatiga 01", "alamat": "Jl. Diponegoro No. 12, Salatiga"},
    {"kode": "TK-02", "nama": "Toko Ungaran 01", "alamat": "Jl. Gatot Subroto No. 45, Ungaran"},
    {"kode": "TK-03", "nama": "Toko Semarang Tengah 01", "alamat": "Jl. Pemuda No. 88, Semarang"},
]

# (username, nama, role, kode toko)
AKUN = [
    ("admin", "Admin Stokara", ADMIN, None),
    ("kepala.gudang", "Kepala Gudang Semarang", KEPALA_GUDANG, None),
    ("staff.gudang", "Staff Gudang Semarang", STAFF_GUDANG, None),
    ("toko.salatiga01", "Kepala Toko Salatiga 01", KEPALA_TOKO, "TK-01"),
    ("toko.ungaran01", "Kepala Toko Ungaran 01", KEPALA_TOKO, "TK-02"),
    ("toko.semarang01", "Kepala Toko Semarang Tengah 01", KEPALA_TOKO, "TK-03"),
]

password = os.getenv("DEMO_PASSWORD", "")
if len(password) < 8:
    print("DEMO_PASSWORD di .env belum diisi atau kurang dari 8 karakter.")
    sys.exit(1)

app = create_app()
with app.app_context():
    db = app.db

    for toko in TOKO:
        if db.master_toko.find_one({"kode": toko["kode"]}):
            print("Toko sudah ada, dilewati :", toko["nama"])
            continue
        db.master_toko.insert_one({**toko, "aktif": True, "dibuat": datetime.now(timezone.utc)})
        print("Toko dibuat              :", toko["nama"])

    for username, nama, role, kode_toko in AKUN:
        if model_user.cari_berdasarkan_username(username):
            print("Akun sudah ada, dilewati :", username)
            continue
        toko_id = None
        if kode_toko:
            toko_id = db.master_toko.find_one({"kode": kode_toko})["_id"]
        model_user.buat_user(username, password, nama, role, toko_id)
        print("Akun dibuat              :", username, "(" + model_user.LABEL_ROLE[role] + ")")
