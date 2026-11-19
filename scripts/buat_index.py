import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import indeks


def cari_tahap(rencana, hasil=None):
    if hasil is None:
        hasil = []
    if isinstance(rencana, dict):
        if "stage" in rencana:
            hasil.append(rencana["stage"] + (f" ({rencana['indexName']})" if "indexName" in rencana else ""))
        for nilai in rencana.values():
            cari_tahap(nilai, hasil)
    elif isinstance(rencana, list):
        for nilai in rencana:
            cari_tahap(nilai, hasil)
    return hasil


app = create_app()
with app.app_context():
    db = app.db
    jumlah = indeks.buat_semua(db)
    print(f"{jumlah} index siap.\n")

    for nama in ["users", "master_produk", "master_toko", "master_supplier", "permintaan",
                 "barang_masuk", "opname", "mutasi_stok", "notifikasi"]:
        daftar = [i["name"] for i in db[nama].list_indexes() if i["name"] != "_id_"]
        print(f"  {nama:16} : {', '.join(daftar)}")

    if "--cek" in sys.argv:
        print("\nBukti index dipakai (explain):")
        toko = db.master_toko.find_one()
        contoh = [
            ("Permintaan satu toko, status DIKIRIM, terbaru dulu",
             db.permintaan.find({"toko_id": toko["_id"] if toko else None, "status": "DIKIRIM"}).sort("dibuat", -1)),
            ("Cari produk dengan kata 'minyak' (text index)",
             db.master_produk.find({"$text": {"$search": "minyak"}})),
            ("Produk berkode P-0001 (unique index)",
             db.master_produk.find({"kode": "P-0001"})),
        ]
        for judul, kursor in contoh:
            rencana = kursor.explain()["queryPlanner"]["winningPlan"]
            print(f"  - {judul}\n      {' -> '.join(cari_tahap(rencana))}")
