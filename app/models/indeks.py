from pymongo import ASCENDING, DESCENDING, TEXT

INDEKS = [
    ("users", [("username", ASCENDING)], {"unique": True, "name": "username_unik"}),
    ("master_produk", [("kode", ASCENDING)], {"unique": True, "name": "kode_produk_unik"}),
    ("master_toko", [("kode", ASCENDING)], {"unique": True, "name": "kode_toko_unik"}),
    ("master_supplier", [("kode", ASCENDING)], {"unique": True, "name": "kode_supplier_unik"}),
    ("permintaan", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_permintaan_unik"}),
    ("barang_masuk", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_barang_masuk_unik"}),
    ("opname", [("nomor", ASCENDING)], {"unique": True, "name": "nomor_opname_unik"}),

    ("permintaan", [("toko_id", ASCENDING), ("status", ASCENDING), ("dibuat", DESCENDING)],
     {"name": "toko_status_tanggal"}),
    ("permintaan", [("status", ASCENDING), ("dibuat", DESCENDING)], {"name": "status_tanggal"}),
    ("mutasi_stok", [("produk_id", ASCENDING), ("waktu", DESCENDING)], {"name": "produk_waktu"}),
    ("notifikasi", [("untuk_role", ASCENDING), ("waktu", DESCENDING)], {"name": "role_waktu"}),
    ("notifikasi", [("untuk_toko_id", ASCENDING), ("waktu", DESCENDING)], {"name": "toko_waktu"}),

    ("master_produk", [("nama", TEXT), ("kategori", TEXT)],
     {"name": "cari_produk", "weights": {"nama": 3, "kategori": 1}, "default_language": "none"}),
]


def buat_semua(db):
    for collection, field, opsi in INDEKS:
        db[collection].create_index(field, **opsi)
    return len(INDEKS)
