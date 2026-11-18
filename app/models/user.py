"""Model user: akun login, password, dan role.

Bentuk dokumen di collection "users":
{
    "username": "kepala.gudang",
    "password_hash": "scrypt:32768:8:1$...",   <- bukan password asli
    "nama": "Kepala Gudang Semarang",
    "role": "kepala_gudang",
    "toko_id": None,          <- hanya diisi untuk Kepala Toko
    "aktif": True,
    "dibuat": datetime
}
"""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.utils.validasi import ValidasiError

# Empat role di Stokara
ADMIN = "admin"
KEPALA_GUDANG = "kepala_gudang"
STAFF_GUDANG = "staff_gudang"
KEPALA_TOKO = "kepala_toko"

LABEL_ROLE = {
    ADMIN: "Admin",
    KEPALA_GUDANG: "Kepala Gudang",
    STAFF_GUDANG: "Staff Gudang",
    KEPALA_TOKO: "Kepala Toko",
}


def cari_berdasarkan_username(username):
    return get_db().users.find_one({"username": username})


def cari_berdasarkan_id(user_id):
    try:
        return get_db().users.find_one({"_id": ObjectId(user_id)})
    except (InvalidId, TypeError):
        return None  # id rusak atau kosong dianggap tidak ditemukan


def cek_role_dan_toko(role, toko_id):
    """Kepala Toko wajib punya toko yang aktif. Role lain tidak punya toko."""
    if role not in LABEL_ROLE:
        raise ValidasiError("Role tidak dikenal.")
    if role != KEPALA_TOKO:
        return None
    toko = get_db().master_toko.find_one({"_id": toko_id}) if toko_id else None
    if toko is None or not toko["aktif"]:
        raise ValidasiError("Kepala Toko wajib dihubungkan ke satu toko yang aktif.")
    return toko_id


def buat_user(username, password, nama, role, toko_id=None):
    """Menyimpan user baru. Password di-hash dulu, yang asli tidak disimpan."""
    toko_id = cek_role_dan_toko(role, toko_id)
    if cari_berdasarkan_username(username):
        raise ValidasiError(f"Username '{username}' sudah dipakai.")

    user = {
        "username": username,
        "password_hash": generate_password_hash(password),
        "nama": nama,
        "role": role,
        "toko_id": toko_id,
        "aktif": True,
        "dibuat": datetime.now(timezone.utc),
    }
    get_db().users.insert_one(user)
    return user


def cek_login(username, password):
    """Kembalikan data user jika username dan password benar, selain itu None."""
    user = cari_berdasarkan_username(username)
    if user is None or not user["aktif"]:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def semua_karyawan():
    """Daftar semua akun untuk halaman Karyawan, ditambah nama toko dan label role."""
    nama_toko = {}
    for t in get_db().master_toko.find():
        nama_toko[t["_id"]] = t["nama"]

    hasil = []
    for u in get_db().users.find().sort("username", 1):
        u["label_role"] = LABEL_ROLE[u["role"]]
        u["toko"] = nama_toko.get(u["toko_id"], "")
        hasil.append(u)
    return hasil


def ubah_karyawan(user_id, nama, role, toko_id):
    toko_id = cek_role_dan_toko(role, toko_id)
    get_db().users.update_one(
        {"_id": user_id},
        {"$set": {"nama": nama, "role": role, "toko_id": toko_id}},
    )


def ubah_status(user_id, aktif):
    get_db().users.update_one({"_id": user_id}, {"$set": {"aktif": aktif}})


def ganti_password(user_id, password_baru):
    get_db().users.update_one(
        {"_id": user_id},
        {"$set": {"password_hash": generate_password_hash(password_baru)}},
    )


def data_publik(user):
    """Data user yang aman dikirim ke browser (tanpa password_hash)."""
    nama_toko = None
    if user["toko_id"]:
        toko = get_db().master_toko.find_one({"_id": user["toko_id"]})
        nama_toko = toko["nama"] if toko else None

    return {
        "username": user["username"],
        "nama": user["nama"],
        "role": user["role"],
        "label_role": LABEL_ROLE[user["role"]],
        "toko": nama_toko,
    }
