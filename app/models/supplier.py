"""Model supplier (collection master_supplier).

{ "kode": "SUP-01", "nama": "PT Sumber Pangan", "telepon": "024-...", "alamat": "...", "aktif": True }
"""
from datetime import datetime, timezone

from app.db import get_db
from app.utils.validasi import ValidasiError


def semua():
    return list(get_db().master_supplier.find().sort("kode", 1))


def cari(supplier_id):
    return get_db().master_supplier.find_one({"_id": supplier_id})


def tambah(kode, nama, telepon, alamat):
    if get_db().master_supplier.find_one({"kode": kode}):
        raise ValidasiError(f"Kode {kode} sudah dipakai supplier lain.")
    supplier = {
        "kode": kode,
        "nama": nama,
        "telepon": telepon,
        "alamat": alamat,
        "aktif": True,
        "dibuat": datetime.now(timezone.utc),
    }
    get_db().master_supplier.insert_one(supplier)
    return supplier


def ubah(supplier_id, nama, telepon, alamat):
    get_db().master_supplier.update_one(
        {"_id": supplier_id},
        {"$set": {"nama": nama, "telepon": telepon, "alamat": alamat}},
    )


def ubah_status(supplier_id, aktif):
    get_db().master_supplier.update_one({"_id": supplier_id}, {"$set": {"aktif": aktif}})
