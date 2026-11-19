from app.db import get_db
from app.models import stok as model_stok
from app.utils.nomor import buat_nomor
from app.utils.validasi import ValidasiError
from app.utils.waktu import sekarang


def semua(batas=200):
    return list(get_db().barang_masuk.find().sort("dibuat", -1).limit(batas))


def simpan(supplier_id, no_surat_jalan, catatan, items, user):
    db = get_db()

    supplier = db.master_supplier.find_one({"_id": supplier_id})
    if supplier is None or not supplier["aktif"]:
        raise ValidasiError("Supplier tidak ditemukan atau sudah nonaktif.")

    isi_items = []
    for item in items:
        produk = db.master_produk.find_one({"_id": item["produk_id"]})
        if produk is None or not produk["aktif"]:
            raise ValidasiError("Ada produk yang tidak ditemukan atau sudah nonaktif.")
        isi_items.append({
            "produk_id": produk["_id"],
            "kode": produk["kode"],
            "nama": produk["nama"],
            "satuan": produk["satuan"],
            "qty": item["qty"],
        })

    nomor = buat_nomor("barang_masuk", "BM")
    db.barang_masuk.insert_one({
        "nomor": nomor,
        "supplier_id": supplier["_id"],
        "supplier": supplier["nama"],
        "no_surat_jalan": no_surat_jalan,
        "catatan": catatan,
        "items": isi_items,
        "oleh": {"id": user["_id"], "nama": user["nama"]},
        "dibuat": sekarang(),
    })

    for item in isi_items:
        model_stok.tambah_stok(
            item["produk_id"], item["qty"], nomor, "Barang masuk dari " + supplier["nama"], user
        )
    return nomor


def pilihan_form():
    db = get_db()
    supplier = [{"id": str(s["_id"]), "value": s["nama"]}
                for s in db.master_supplier.find({"aktif": True}).sort("nama", 1)]
    produk = [{"id": str(p["_id"]), "value": p["kode"] + " · " + p["nama"], "satuan": p["satuan"]}
              for p in db.master_produk.find({"aktif": True}).sort("kode", 1)]
    return {"supplier": supplier, "produk": produk}
