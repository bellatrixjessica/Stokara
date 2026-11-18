"""Model produk (collection master_produk).

{
    "kode": "P-0001",
    "nama": "Minyak Goreng 1L",
    "kategori": "Sembako",
    "satuan": "PCS",
    "supplier_id": ObjectId,
    "lead_time_hari": 2,     <- lama barang datang setelah dipesan ke supplier
    "stok": 0,               <- stok fisik. Hanya berubah lewat barang masuk,
                                pengiriman, dan opname (tidak diubah di form produk)
    "aktif": True
}
"""
from datetime import datetime, timezone

from app.db import get_db
from app.utils.validasi import ValidasiError

SATUAN = ["PCS", "PACK", "KARTON", "BOX", "LUSIN"]


def semua():
    """Semua produk, ditambah nama supplier-nya."""
    nama_supplier = {}
    for s in get_db().master_supplier.find():
        nama_supplier[s["_id"]] = s["nama"]

    hasil = []
    for p in get_db().master_produk.find().sort("kode", 1):
        p["supplier"] = nama_supplier.get(p["supplier_id"], "-")
        hasil.append(p)
    return hasil


def cari(produk_id):
    return get_db().master_produk.find_one({"_id": produk_id})


def cek_supplier(supplier_id):
    supplier = get_db().master_supplier.find_one({"_id": supplier_id})
    if supplier is None or not supplier["aktif"]:
        raise ValidasiError("Supplier tidak ditemukan atau sudah nonaktif.")


def tambah(kode, nama, kategori, satuan, supplier_id, lead_time_hari):
    if get_db().master_produk.find_one({"kode": kode}):
        raise ValidasiError(f"Kode {kode} sudah dipakai produk lain.")
    cek_supplier(supplier_id)

    produk = {
        "kode": kode,
        "nama": nama,
        "kategori": kategori,
        "satuan": satuan,
        "supplier_id": supplier_id,
        "lead_time_hari": lead_time_hari,
        "stok": 0,  # produk baru belum punya stok
        "aktif": True,
        "dibuat": datetime.now(timezone.utc),
    }
    get_db().master_produk.insert_one(produk)
    return produk


def ubah(produk_id, nama, kategori, satuan, supplier_id, lead_time_hari):
    cek_supplier(supplier_id)
    get_db().master_produk.update_one(
        {"_id": produk_id},
        {"$set": {
            "nama": nama,
            "kategori": kategori,
            "satuan": satuan,
            "supplier_id": supplier_id,
            "lead_time_hari": lead_time_hari,
        }},
    )


def ubah_status(produk_id, aktif):
    get_db().master_produk.update_one({"_id": produk_id}, {"$set": {"aktif": aktif}})
