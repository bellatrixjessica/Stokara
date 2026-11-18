"""Daftar index MongoDB Stokara.

Index = "daftar isi" untuk collection. Tanpa index, MongoDB membaca SEMUA dokumen
(COLLSCAN). Dengan index, MongoDB langsung melompat ke dokumen yang dicari (IXSCAN).

Tiga jenis index yang dipakai:
- UNIQUE    : satu nilai tidak boleh dipakai dua dokumen (kode, username, nomor dokumen)
- COMPOSITE : gabungan beberapa field, sesuai urutan filter + urutan sort di query
- TEXT      : pencarian kata di nama dan kategori produk
"""
from pymongo import ASCENDING, DESCENDING, TEXT

INDEKS = [
    # (collection, field, opsi)
    # ---- UNIQUE: mencegah data ganda, walaupun dua orang menyimpan bersamaan
    ("users", [("username", ASCENDING)], {"unique": True, "name": "username_unik"}),
    ("master_produk", [("kode", ASCENDING)], {"unique": True, "name": "kode_produk_unik"}),
    ("master_toko", [("kode", ASCENDING)], {"unique": True, "name": "kode_toko_unik"}),
    ("master_supplier", [("kode", ASCENDING)], {"unique": True, "name": "kode_supplier_unik"}),
    ("permintaan", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_permintaan_unik"}),
    ("barang_masuk", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_barang_masuk_unik"}),
    ("opname", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_opname_unik"}),

    # ---- COMPOSITE: dipakai query yang sering dijalankan
    # Halaman Kepala Toko: permintaan toko X, status Y, terbaru dulu
    ("permintaan", [("toko_id", ASCENDING), ("status", ASCENDING), ("dibuat", DESCENDING)],
     {"name": "toko_status_tanggal"}),
    # Halaman gudang & dashboard: permintaan status Y, terbaru dulu
    ("permintaan", [("status", ASCENDING), ("dibuat", DESCENDING)], {"name": "status_tanggal"}),
    # Riwayat stok satu produk, terbaru dulu
    ("mutasi_stok", [("produk_id", ASCENDING), ("waktu", DESCENDING)], {"name": "produk_waktu"}),
    # Lonceng: notifikasi untuk role / toko, terbaru dulu
    ("notifikasi", [("untuk_role", ASCENDING), ("waktu", DESCENDING)], {"name": "role_waktu"}),
    ("notifikasi", [("untuk_toko_id", ASCENDING), ("waktu", DESCENDING)], {"name": "toko_waktu"}),

    # ---- TEXT: pencarian produk berdasarkan kata di nama (bobot 3) dan kategori (bobot 1)
    ("master_produk", [("nama", TEXT), ("kategori", TEXT)],
     {"name": "cari_produk", "weights": {"nama": 3, "kategori": 1}, "default_language": "none"}),
]


def buat_semua(db):
    """Buat semua index. Aman dijalankan berkali-kali (index yang sudah ada dilewati)."""
    for collection, field, opsi in INDEKS:
        db[collection].create_index(field, **opsi)
    return len(INDEKS)
