"""Mengubah dokumen MongoDB menjadi data yang bisa dikirim sebagai JSON."""
from datetime import datetime

from bson import ObjectId


def ke_json(dok):
    """Contoh: {"_id": ObjectId("65f..."), "dibuat": datetime(...)}
           -> {"id": "65f...", "dibuat": "2026-11-19T02:10:00+00:00"}

    "_id" diganti nama menjadi "id" karena tabel Webix memakai "id" sebagai kunci baris.
    """
    hasil = {}
    for key, nilai in dok.items():
        if key == "password_hash":
            continue  # tidak pernah dikirim ke browser
        if key == "_id":
            key = "id"
        hasil[key] = ubah_nilai(nilai)
    return hasil


def ubah_nilai(nilai):
    if isinstance(nilai, ObjectId):
        return str(nilai)
    if isinstance(nilai, datetime):
        return nilai.isoformat()
    if isinstance(nilai, dict):
        return ke_json(nilai)
    if isinstance(nilai, list):
        return [ubah_nilai(x) for x in nilai]
    return nilai
