from app.db import get_db
from app.models import insight
from app.models.user import KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG


def label(jumlah, teks, warna):
    return [{"teks": f"{jumlah} {teks}", "warna": warna}] if jumlah else []


def ringkasan(user):
    db = get_db()
    hasil = {}

    if user["role"] == KEPALA_GUDANG:
        produk = insight.insight_produk()
        kritis = sum(1 for p in produk if p["status"] == "KRITIS")
        restock = sum(1 for p in produk if p["status"] == "PERLU_RESTOCK")
        hasil["permintaan"] = label(db.permintaan.count_documents({"status": "DIAJUKAN"}), "menunggu persetujuan", "b-biru")
        hasil["dashboard"] = label(kritis, "kritis", "b-merah") + label(restock, "perlu restock", "b-oranye")
        hasil["opname"] = label(db.opname.count_documents({"status": "MENUNGGU"}), "menunggu pemeriksaan", "b-ungu")

    elif user["role"] == STAFF_GUDANG:
        hasil["permintaan"] = label(db.permintaan.count_documents({"status": "DISETUJUI"}), "siap dikirim", "b-ungu")
        hasil["opname"] = label(db.opname.count_documents({"status": "DITOLAK"}), "ditolak", "b-merah")

    elif user["role"] == KEPALA_TOKO:
        toko = {"toko_id": user["toko_id"]}
        hasil["permintaan-saya"] = (
            label(db.permintaan.count_documents({**toko, "status": "DIKIRIM"}), "perlu dikonfirmasi", "b-oranye")
            + label(db.permintaan.count_documents({**toko, "status": "DIAJUKAN"}), "diajukan", "b-biru")
        )
    return hasil
