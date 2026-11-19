import re

from pymongo import ReturnDocument

from app.db import get_db
from app.utils.validasi import ValidasiError
from app.utils.waktu import sekarang


def catat_mutasi(produk, jenis, perubahan, stok_sesudah, referensi, keterangan, user):
    get_db().mutasi_stok.insert_one({
        "produk_id": produk["_id"],
        "kode": produk["kode"],
        "nama": produk["nama"],
        "jenis": jenis,
        "perubahan": perubahan,
        "stok_sebelum": stok_sesudah - perubahan,
        "stok_sesudah": stok_sesudah,
        "referensi": referensi,
        "keterangan": keterangan,
        "oleh": {"id": user["_id"], "nama": user["nama"]},
        "waktu": sekarang(),
    })


def tambah_stok(produk_id, qty, referensi, keterangan, user):
    produk = get_db().master_produk.find_one_and_update(
        {"_id": produk_id},
        {"$inc": {"stok": qty}},
        return_document=ReturnDocument.AFTER,
    )
    catat_mutasi(produk, "MASUK", qty, produk["stok"], referensi, keterangan, user)


def kurangi_stok(produk_id, qty, referensi, keterangan, user):
    produk = get_db().master_produk.find_one_and_update(
        {"_id": produk_id, "stok": {"$gte": qty}},
        {"$inc": {"stok": -qty}},
        return_document=ReturnDocument.AFTER,
    )
    if produk is None:
        raise ValidasiError("Stok fisik tidak cukup.")
    catat_mutasi(produk, "KELUAR", -qty, produk["stok"], referensi, keterangan, user)


def koreksi_stok(produk_id, selisih, referensi, keterangan, user):
    syarat = {"_id": produk_id}
    if selisih < 0:
        syarat["stok"] = {"$gte": -selisih}

    produk = get_db().master_produk.find_one_and_update(
        syarat, {"$inc": {"stok": selisih}}, return_document=ReturnDocument.AFTER
    )
    if produk is None:
        raise ValidasiError("Stok fisik saat ini lebih kecil dari selisih opname. Hitung ulang produk ini.")
    catat_mutasi(produk, "ADJUST", selisih, produk["stok"], referensi, keterangan, user)


def qty_dipesan():
    hasil = {}
    for permintaan in get_db().permintaan.find({"status": "DISETUJUI"}):
        for item in permintaan["items"]:
            produk_id = item["produk_id"]
            hasil[produk_id] = hasil.get(produk_id, 0) + item["qty_disetujui"]
    return hasil


def stok_tersedia(produk_id):
    produk = get_db().master_produk.find_one({"_id": produk_id})
    return produk["stok"] - qty_dipesan().get(produk_id, 0)


def filter_cari(cari):
    if any(huruf.isdigit() for huruf in cari):
        return {"kode": {"$regex": "^" + re.escape(cari.upper())}}
    return {"$text": {"$search": cari}}


def daftar_stok(cari=None):
    filter_ = {"aktif": True}
    if cari:
        filter_.update(filter_cari(cari))

    dipesan = qty_dipesan()
    hasil = []
    for p in get_db().master_produk.find(filter_).sort("kode", 1):
        jumlah_dipesan = dipesan.get(p["_id"], 0)
        hasil.append({
            "id": str(p["_id"]),
            "kode": p["kode"],
            "nama": p["nama"],
            "kategori": p["kategori"],
            "satuan": p["satuan"],
            "fisik": p["stok"],
            "dipesan": jumlah_dipesan,
            "tersedia": p["stok"] - jumlah_dipesan,
        })
    return hasil


def riwayat(produk_id, batas=100):
    return list(get_db().mutasi_stok.find({"produk_id": produk_id}).sort("waktu", -1).limit(batas))
