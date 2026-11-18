"""Model stok: perubahan stok dan riwayatnya (collection mutasi_stok).

Tiga angka stok:
- Stok fisik    : barang yang benar-benar ada di gudang (field "stok" di master_produk).
- Stok dipesan  : qty yang sudah DISETUJUI untuk toko tapi belum dikirim.
- Stok tersedia : fisik - dipesan. Inilah yang boleh disetujui untuk permintaan baru.

Stok fisik HANYA berubah lewat tiga fungsi di file ini, dan setiap perubahan
dicatat di mutasi_stok:
- tambah_stok()    -> MASUK  (barang masuk dari supplier)
- kurangi_stok()   -> KELUAR (pengiriman ke toko)
- koreksi_stok()   -> ADJUST (selisih hasil stock opname)

Bentuk dokumen mutasi_stok:
{
    "produk_id": ObjectId, "kode": "P-0001", "nama": "Minyak Goreng 1L",
    "jenis": "MASUK",            <- MASUK / KELUAR / ADJUST
    "perubahan": 40,             <- positif = bertambah, negatif = berkurang
    "stok_sebelum": 51, "stok_sesudah": 91,
    "referensi": "BM-261119-0001",
    "keterangan": "Barang masuk dari PT Sumber Pangan Jaya",
    "oleh": {"id": ObjectId, "nama": "Staff Gudang Semarang"},
    "waktu": datetime (UTC)
}
"""
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
    # $inc menambah langsung di database dalam satu langkah.
    produk = get_db().master_produk.find_one_and_update(
        {"_id": produk_id},
        {"$inc": {"stok": qty}},
        return_document=ReturnDocument.AFTER,  # kembalikan data SESUDAH ditambah
    )
    catat_mutasi(produk, "MASUK", qty, produk["stok"], referensi, keterangan, user)


def kurangi_stok(produk_id, qty, referensi, keterangan, user):
    # Syarat "stok >= qty" dan pengurangannya dikerjakan database dalam SATU langkah.
    # Kalau stok kurang, dokumen tidak cocok dengan syarat -> tidak ada yang dikurangi.
    # Jadi stok tidak akan pernah minus, walaupun dua orang mengirim bersamaan.
    produk = get_db().master_produk.find_one_and_update(
        {"_id": produk_id, "stok": {"$gte": qty}},
        {"$inc": {"stok": -qty}},
        return_document=ReturnDocument.AFTER,
    )
    if produk is None:
        raise ValidasiError("Stok fisik tidak cukup.")
    catat_mutasi(produk, "KELUAR", -qty, produk["stok"], referensi, keterangan, user)


def koreksi_stok(produk_id, selisih, referensi, keterangan, user):
    """Tambah atau kurangi stok sebesar selisih hasil opname (bisa positif atau negatif).

    Yang dikoreksi adalah SELISIHNYA, bukan menimpa stok dengan angka hitungan.
    Jadi barang yang masuk atau keluar setelah dihitung tetap terhitung.
    """
    syarat = {"_id": produk_id}
    if selisih < 0:
        syarat["stok"] = {"$gte": -selisih}  # sama seperti kurangi_stok: tidak boleh minus

    produk = get_db().master_produk.find_one_and_update(
        syarat, {"$inc": {"stok": selisih}}, return_document=ReturnDocument.AFTER
    )
    if produk is None:
        raise ValidasiError("Stok fisik saat ini lebih kecil dari selisih opname. Hitung ulang produk ini.")
    catat_mutasi(produk, "ADJUST", selisih, produk["stok"], referensi, keterangan, user)


def qty_dipesan():
    """Total qty DISETUJUI yang belum dikirim, per produk. Hasil: {produk_id: qty}"""
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
    """Filter pencarian produk.

    - Ada angkanya (contoh "P-0001", "0004") -> cari awalan kode (memakai unique index kode)
    - Kata biasa (contoh "minyak", "sembako") -> cari di nama & kategori memakai TEXT INDEX
    """
    if any(huruf.isdigit() for huruf in cari):
        return {"kode": {"$regex": "^" + re.escape(cari.upper())}}
    return {"$text": {"$search": cari}}


def daftar_stok(cari=None):
    """Produk aktif dengan stok fisik, dipesan, dan tersedia. cari = kata kunci (opsional)."""
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
    """Mutasi terbaru satu produk (paling baru di atas)."""
    return list(get_db().mutasi_stok.find({"produk_id": produk_id}).sort("waktu", -1).limit(batas))
