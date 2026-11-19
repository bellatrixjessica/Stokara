from datetime import datetime

from bson import ObjectId


def ke_json(dok):
    hasil = {}
    for key, nilai in dok.items():
        if key == "password_hash":
            continue
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
