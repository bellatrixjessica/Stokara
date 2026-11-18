"""Model toko (collection master_toko).

{ "kode": "TK-01", "nama": "Toko Salatiga 01", "alamat": "...", "aktif": True, "dibuat": datetime }
"""
from datetime import datetime, timezone

from app.db import get_db
from app.utils.validasi import ValidasiError


def semua():
    return list(get_db().master_toko.find().sort("kode", 1))


def cari(toko_id):
    return get_db().master_toko.find_one({"_id": toko_id})


def tambah(kode, nama, alamat):
    if get_db().master_toko.find_one({"kode": kode}):
        raise ValidasiError(f"Kode {kode} sudah dipakai toko lain.")
    toko = {
        "kode": kode,
        "nama": nama,
        "alamat": alamat,
        "aktif": True,
        "dibuat": datetime.now(timezone.utc),
    }
    get_db().master_toko.insert_one(toko)
    return toko


def ubah(toko_id, nama, alamat):
    get_db().master_toko.update_one({"_id": toko_id}, {"$set": {"nama": nama, "alamat": alamat}})


def ubah_status(toko_id, aktif):
    get_db().master_toko.update_one({"_id": toko_id}, {"$set": {"aktif": aktif}})
