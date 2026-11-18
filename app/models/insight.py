"""Insight dashboard: fill rate, safety stock, reorder point, dan saran restock.

Semua dihitung dari permintaan PERIODE_HARI (30) hari terakhir.

RUMUS (sama dengan README)
- Demand per hari    = total qty diminta / 30          (semua status kecuali DIBATALKAN)
- Fill rate          = total qty dikirim / total qty diminta x 100%
                       (hanya DIKIRIM, DITERIMA, dan DITOLAK; DITOLAK dihitung dikirim 0)
- Safety stock (SS)  = demand per hari x hari pengaman (2)               -> dibulatkan ke atas
- Reorder point (ROP)= demand per hari x lead time + SS                  -> dibulatkan ke atas
- Habis dalam        = stok tersedia / demand per hari (hari)
- Saran restock      = demand per hari x (lead time + cadangan 7) - stok tersedia
                                                       -> dibulatkan ke atas, minimal 0
STATUS
- KRITIS          : tersedia <= SS
- PERLU_RESTOCK   : tersedia <= ROP
- AMAN            : tersedia > ROP
- TANPA_PERMINTAAN: demand per hari = 0
"""
import math
from datetime import timedelta

from flask import current_app

from app.db import get_db
from app.models import stok as model_stok
from app.utils.waktu import WIB, sekarang

SELESAI = ["DIKIRIM", "DITERIMA", "DITOLAK"]   # permintaan yang dihitung di fill rate


def awal_periode():
    return sekarang() - timedelta(days=current_app.config["PERIODE_HARI"])


# ---------------------------------------------------------------- rumus satu produk

def rumus_produk(total_diminta, lead_time, tersedia, periode=30, hari_pengaman=2, cadangan=7):
    """Rumus insight untuk SATU produk. Fungsi murni (tanpa database), jadi mudah dites.

    Contoh README: rumus_produk(360, 3, 80) -> demand 12, SS 24, ROP 60, habis 6.7 hari, saran 40, AMAN
    """
    demand = total_diminta / periode
    if demand == 0:
        return {"demand_per_hari": 0, "safety_stock": 0, "reorder_point": 0,
                "habis_dalam": None, "saran_restock": 0, "status": "TANPA_PERMINTAAN"}

    safety_stock = math.ceil(demand * hari_pengaman)
    reorder_point = math.ceil(demand * lead_time + safety_stock)
    saran = max(0, math.ceil(demand * (lead_time + cadangan) - tersedia))

    if tersedia <= safety_stock:
        status = "KRITIS"
    elif tersedia <= reorder_point:
        status = "PERLU_RESTOCK"
    else:
        status = "AMAN"

    return {
        "demand_per_hari": round(demand, 1),
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "habis_dalam": round(max(tersedia, 0) / demand, 1),
        "saran_restock": saran,
        "status": status,
    }


# ---------------------------------------------------------------- data dari database

def demand_per_produk():
    """Total qty diminta per produk dalam periode, memakai AGGREGATION PIPELINE MongoDB.

    $match  : ambil permintaan 30 hari terakhir yang tidak dibatalkan
    $unwind : pecah array items, satu dokumen per produk
    $group  : jumlahkan qty_diminta per produk_id
    Hasil   : {produk_id: total_qty_diminta}
    """
    pipeline = [
        {"$match": {"dibuat": {"$gte": awal_periode()}, "status": {"$ne": "DIBATALKAN"}}},
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.produk_id", "total": {"$sum": "$items.qty_diminta"}}},
    ]
    return {baris["_id"]: baris["total"] for baris in get_db().permintaan.aggregate(pipeline)}


def insight_produk():
    """Insight untuk setiap produk aktif, diurutkan: Kritis, Perlu restock, Aman, Tanpa permintaan."""
    config = current_app.config
    demand = demand_per_produk()
    hasil = []
    for baris in model_stok.daftar_stok():
        produk = get_db().master_produk.find_one({"kode": baris["kode"]})
        rumus = rumus_produk(
            demand.get(produk["_id"], 0), produk["lead_time_hari"], baris["tersedia"],
            config["PERIODE_HARI"], config["HARI_PENGAMAN"], config["PERIODE_CADANGAN_HARI"],
        )
        hasil.append({**baris, **rumus, "lead_time_hari": produk["lead_time_hari"]})

    urutan = {"KRITIS": 0, "PERLU_RESTOCK": 1, "AMAN": 2, "TANPA_PERMINTAAN": 3}
    hasil.sort(key=lambda p: (urutan[p["status"]], p["kode"]))
    return hasil


def fill_rate():
    """Fill rate keseluruhan dan per toko, dari permintaan yang sudah selesai dalam periode."""
    total = {"diminta": 0, "dikirim": 0}
    per_toko = {}
    for p in get_db().permintaan.find({"dibuat": {"$gte": awal_periode()}, "status": {"$in": SELESAI}}):
        diminta = sum(i["qty_diminta"] for i in p["items"])
        dikirim = sum(i["qty_dikirim"] or 0 for i in p["items"])   # DITOLAK: qty_dikirim kosong = 0
        total["diminta"] += diminta
        total["dikirim"] += dikirim
        toko = per_toko.setdefault(p["toko"], {"toko": p["toko"], "diminta": 0, "dikirim": 0})
        toko["diminta"] += diminta
        toko["dikirim"] += dikirim

    def persen(data):
        return round(data["dikirim"] / data["diminta"] * 100, 1) if data["diminta"] else None

    daftar_toko = [{**t, "persen": persen(t)} for t in per_toko.values()]
    daftar_toko.sort(key=lambda t: t["persen"])
    return {**total, "persen": persen(total), "per_toko": daftar_toko}


def tren_harian():
    """Qty diminta dan dikirim per hari (tanggal WIB) selama periode, untuk grafik."""
    jumlah_hari = current_app.config["PERIODE_HARI"]
    hari_ini = sekarang().astimezone(WIB).date()
    tren = {}
    for i in range(jumlah_hari - 1, -1, -1):
        tanggal = hari_ini - timedelta(days=i)
        tren[tanggal] = {"tanggal": tanggal.strftime("%d/%m"), "diminta": 0, "dikirim": 0}

    for p in get_db().permintaan.find({"dibuat": {"$gte": awal_periode()}, "status": {"$ne": "DIBATALKAN"}}):
        tanggal = p["dibuat"].astimezone(WIB).date()
        if tanggal in tren:
            tren[tanggal]["diminta"] += sum(i["qty_diminta"] for i in p["items"])
            tren[tanggal]["dikirim"] += sum(i["qty_dikirim"] or 0 for i in p["items"])
    return list(tren.values())


def jumlah_status(status):
    return get_db().permintaan.count_documents({"status": status})


def dashboard():
    """Semua data untuk halaman Dashboard dalam satu paket."""
    produk = insight_produk()
    akhir = sekarang().astimezone(WIB)
    awal = akhir - timedelta(days=current_app.config["PERIODE_HARI"] - 1)
    return {
        "periode": {"dari": awal.strftime("%d/%m/%Y"), "sampai": akhir.strftime("%d/%m/%Y"),
                    "hari": current_app.config["PERIODE_HARI"]},
        "fill_rate": fill_rate(),
        "ringkasan": {
            "kritis": sum(1 for p in produk if p["status"] == "KRITIS"),
            "perlu_restock": sum(1 for p in produk if p["status"] == "PERLU_RESTOCK"),
            "menunggu_persetujuan": jumlah_status("DIAJUKAN"),
            "menunggu_kirim": jumlah_status("DISETUJUI"),
        },
        "tren": tren_harian(),
        "produk": produk,
    }
