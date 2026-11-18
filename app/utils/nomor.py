"""Nomor dokumen, contoh: BM-261119-0001 (barang masuk ke-1 tanggal 19 Nov 2026)."""
from app.db import get_db
from app.utils.waktu import sekarang_wib


def buat_nomor(collection, awalan):
    """awalan-YYMMDD-urutan. Urutan dimulai lagi dari 0001 setiap hari.

    Contoh: buat_nomor("barang_masuk", "BM") -> "BM-261119-0003"
    """
    depan = awalan + "-" + sekarang_wib().strftime("%y%m%d") + "-"
    jumlah_hari_ini = get_db()[collection].count_documents({"nomor": {"$regex": "^" + depan}})
    return depan + str(jumlah_hari_ini + 1).zfill(4)
