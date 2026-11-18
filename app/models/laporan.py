"""Laporan periode untuk Kepala Gudang (semua laporan) dan Kepala Toko (permintaan tokonya).

Setiap laporan menghasilkan bentuk data yang SAMA, jadi satu halaman bisa
menampilkan dan mengunduh semuanya:
{
    "judul": "Laporan Permintaan Toko",
    "periode": "21/10/2026 – 19/11/2026",
    "ringkasan": [{"label": "Fill rate", "nilai": 86.8, "persen": True, "ket": "..."}, ...],
    "baris": [ {...satu baris tabel...}, ... ]
}

Tanggal yang dipilih pengguna adalah tanggal WIB. Di database waktu disimpan UTC,
jadi "19 Nov 2026" diubah menjadi rentang 19 Nov 00.00 WIB sampai 20 Nov 00.00 WIB.
"""
from datetime import datetime, time, timedelta, timezone

from app.db import get_db
from app.models import insight
from app.models.permintaan import DIBATALKAN, DIKIRIM, DISETUJUI, DITERIMA, DITOLAK
from app.utils.validasi import ValidasiError
from app.utils.waktu import WIB

MAKS_HARI = 366   # satu laporan paling panjang satu tahun

JUDUL = {
    "permintaan": "Laporan Permintaan Toko",
    "mutasi": "Laporan Mutasi Stok",
    "barang-masuk": "Laporan Barang Masuk",
    "restock": "Laporan Saran Restock",
}


def rentang_waktu(dari, sampai):
    """Dua tanggal WIB -> filter waktu MongoDB dalam UTC: {"$gte": awal, "$lt": akhir}."""
    if dari > sampai:
        raise ValidasiError("Tanggal awal tidak boleh setelah tanggal akhir.")
    if (sampai - dari).days + 1 > MAKS_HARI:
        raise ValidasiError(f"Periode laporan maksimal {MAKS_HARI} hari.")
    awal = datetime.combine(dari, time.min, tzinfo=WIB)
    akhir = datetime.combine(sampai + timedelta(days=1), time.min, tzinfo=WIB)  # sampai akhir hari
    return {"$gte": awal.astimezone(timezone.utc), "$lt": akhir.astimezone(timezone.utc)}


def teks_periode(dari, sampai):
    return dari.strftime("%d/%m/%Y") + " – " + sampai.strftime("%d/%m/%Y")


def persen(bagian, total):
    return round(bagian / total * 100, 1) if total else None


def buat(jenis, dari, sampai, toko_id=None):
    """Pintu masuk semua laporan. toko_id hanya dipakai laporan permintaan."""
    if jenis == "restock":
        # Saran restock adalah keadaan SAAT INI (dari 30 hari terakhir), bukan per periode.
        return laporan_restock()

    waktu = rentang_waktu(dari, sampai)
    if jenis == "permintaan":
        hasil = laporan_permintaan(waktu, toko_id)
    elif jenis == "mutasi":
        hasil = laporan_mutasi(waktu)
    else:
        hasil = laporan_barang_masuk(waktu)
    return {"judul": JUDUL[jenis], "periode": teks_periode(dari, sampai), **hasil}


# ---------------------------------------------------------------- permintaan toko

def laporan_permintaan(waktu, toko_id=None):
    """Satu baris per permintaan. Fill rate dihitung dengan aturan yang sama dengan dashboard:
    hanya permintaan yang sudah selesai diproses (Dikirim, Diterima, Ditolak);
    Ditolak dihitung dikirim 0; Dibatalkan tidak dihitung.
    """
    filter_ = {"dibuat": waktu}
    if toko_id is not None:
        filter_["toko_id"] = toko_id

    baris = []
    jumlah_batal = 0
    selesai = {"diminta": 0, "dikirim": 0}
    for p in get_db().permintaan.find(filter_).sort("dibuat", -1):
        diminta = sum(i["qty_diminta"] for i in p["items"])
        disetujui = dikirim = None
        if p["status"] in (DISETUJUI, DIKIRIM, DITERIMA):
            disetujui = sum(i["qty_disetujui"] for i in p["items"])
        if p["status"] in (DIKIRIM, DITERIMA):
            dikirim = sum(i["qty_dikirim"] for i in p["items"])
        elif p["status"] == DITOLAK:
            dikirim = 0

        if p["status"] in insight.SELESAI:
            selesai["diminta"] += diminta
            selesai["dikirim"] += dikirim
        if p["status"] == DIBATALKAN:
            jumlah_batal += 1

        baris.append({
            "nomor": p["nomor"],
            "toko": p["toko"],
            "dibuat": p["dibuat"],
            "status": p["status"],
            "diminta": diminta,
            "disetujui": disetujui,
            "dikirim": dikirim,
            "fill_rate": persen(dikirim, diminta) if p["status"] in insight.SELESAI else None,
        })

    return {
        "ringkasan": [
            {"label": "Permintaan", "nilai": len(baris), "ket": f"{jumlah_batal} dibatalkan"},
            {"label": "Qty diminta", "nilai": selesai["diminta"], "ket": "Dari permintaan yang sudah diproses"},
            {"label": "Qty dikirim", "nilai": selesai["dikirim"], "ket": "Ditolak dihitung 0"},
            {"label": "Fill rate", "nilai": persen(selesai["dikirim"], selesai["diminta"]), "persen": True,
             "ket": "Qty dikirim ÷ qty diminta"},
        ],
        "baris": baris,
    }


# ---------------------------------------------------------------- mutasi stok

def laporan_mutasi(waktu):
    """Semua perubahan stok fisik dalam periode (Masuk, Keluar, Penyesuaian)."""
    baris = []
    total = {"MASUK": 0, "KELUAR": 0, "ADJUST": 0}
    for m in get_db().mutasi_stok.find({"waktu": waktu}).sort("waktu", -1):
        total[m["jenis"]] += m["perubahan"]
        baris.append({
            "waktu": m["waktu"],
            "kode": m["kode"],
            "nama": m["nama"],
            "jenis": m["jenis"],
            "perubahan": m["perubahan"],
            "stok_sesudah": m["stok_sesudah"],
            "referensi": m["referensi"],
            "oleh": m["oleh"]["nama"],
        })

    return {
        "ringkasan": [
            {"label": "Mutasi", "nilai": len(baris), "ket": "Jumlah perubahan stok"},
            {"label": "Total masuk", "nilai": total["MASUK"], "ket": "Barang masuk dari supplier"},
            {"label": "Total keluar", "nilai": -total["KELUAR"], "ket": "Dikirim ke toko"},
            {"label": "Penyesuaian", "nilai": total["ADJUST"], "ket": "Selisih stock opname"},
        ],
        "baris": baris,
    }


# ---------------------------------------------------------------- barang masuk

def laporan_barang_masuk(waktu):
    """Satu baris per produk yang diterima, supaya mudah dijumlahkan di Excel."""
    baris = []
    jumlah_dokumen = 0
    supplier = set()
    produk = set()
    for bm in get_db().barang_masuk.find({"dibuat": waktu}).sort("dibuat", -1):
        jumlah_dokumen += 1
        supplier.add(bm["supplier"])
        for item in bm["items"]:
            produk.add(item["kode"])
            baris.append({
                "dibuat": bm["dibuat"],
                "nomor": bm["nomor"],
                "supplier": bm["supplier"],
                "no_surat_jalan": bm["no_surat_jalan"],
                "kode": item["kode"],
                "nama": item["nama"],
                "qty": item["qty"],
                "satuan": item["satuan"],
            })

    return {
        "ringkasan": [
            {"label": "Dokumen", "nilai": jumlah_dokumen, "ket": "Barang masuk dicatat"},
            {"label": "Supplier", "nilai": len(supplier), "ket": "Yang mengirim barang"},
            {"label": "Produk", "nilai": len(produk), "ket": "Jenis produk diterima"},
            {"label": "Total qty", "nilai": sum(b["qty"] for b in baris), "ket": "Semua satuan dijumlahkan"},
        ],
        "baris": baris,
    }


# ---------------------------------------------------------------- saran restock

def laporan_restock():
    """Isi tabel saran restock di dashboard, dalam bentuk laporan yang bisa diunduh."""
    data = insight.dashboard()
    produk = data["produk"]
    perlu = [p for p in produk if p["status"] in ("KRITIS", "PERLU_RESTOCK")]
    baris = [{
        "kode": p["kode"], "nama": p["nama"], "satuan": p["satuan"], "status": p["status"],
        "tersedia": p["tersedia"], "demand_per_hari": p["demand_per_hari"],
        "safety_stock": p["safety_stock"], "reorder_point": p["reorder_point"],
        "habis_dalam": p["habis_dalam"], "lead_time_hari": p["lead_time_hari"],
        "saran_restock": p["saran_restock"],
    } for p in produk]

    return {
        "judul": JUDUL["restock"],
        "periode": f"Keadaan saat ini, dari permintaan {data['periode']['hari']} hari terakhir "
                   f"({data['periode']['dari']} – {data['periode']['sampai']})",
        "ringkasan": [
            {"label": "Stok kritis", "nilai": data["ringkasan"]["kritis"], "ket": "Tersedia ≤ safety stock"},
            {"label": "Perlu restock", "nilai": data["ringkasan"]["perlu_restock"], "ket": "Tersedia ≤ reorder point"},
            {"label": "Produk dipantau", "nilai": len(produk), "ket": "Produk aktif"},
            {"label": "Total saran", "nilai": sum(p["saran_restock"] for p in perlu),
             "ket": "Untuk produk kritis dan perlu restock"},
        ],
        "baris": baris,
    }
