"""Test rumus dashboard insight. Angkanya sama dengan contoh perhitungan di README."""
from datetime import timedelta

import pytest

from app.db import get_db
from app.models import insight
from app.models.insight import rumus_produk
from app.utils.waktu import sekarang
from tests.helper import login


# ---------------------------------------------------------------- rumus (tanpa database)

def test_contoh_readme_status_aman():
    hasil = rumus_produk(total_diminta=360, lead_time=3, tersedia=80)
    assert hasil == {
        "demand_per_hari": 12.0,   # 360 / 30
        "safety_stock": 24,        # 12 x 2
        "reorder_point": 60,       # 12 x 3 + 24
        "habis_dalam": 6.7,        # 80 / 12
        "saran_restock": 40,       # 12 x (3 + 7) - 80
        "status": "AMAN",          # 80 > 60
    }


def test_contoh_readme_setelah_stok_turun_perlu_restock():
    hasil = rumus_produk(total_diminta=360, lead_time=3, tersedia=50)
    assert hasil["status"] == "PERLU_RESTOCK"   # 24 < 50 <= 60
    assert hasil["saran_restock"] == 70          # 12 x 10 - 50


def test_stok_di_bawah_safety_stock_kritis_dan_dibulatkan_ke_atas():
    hasil = rumus_produk(total_diminta=468, lead_time=2, tersedia=0)  # 15,6 per hari
    assert hasil["status"] == "KRITIS"
    assert hasil["safety_stock"] == 32     # 31,2 dibulatkan ke atas
    assert hasil["reorder_point"] == 64    # 15,6 x 2 + 32 = 63,2 -> 64
    assert hasil["saran_restock"] == 141   # 15,6 x 9 = 140,4 -> 141


def test_saran_restock_tidak_pernah_negatif():
    assert rumus_produk(total_diminta=30, lead_time=2, tersedia=500)["saran_restock"] == 0


def test_tanpa_permintaan():
    hasil = rumus_produk(total_diminta=0, lead_time=2, tersedia=10)
    assert hasil["status"] == "TANPA_PERMINTAAN"
    assert hasil["habis_dalam"] is None


# ---------------------------------------------------------------- dari database

def permintaan(produk_id, status, diminta, dikirim=None, hari_lalu=1, toko="Toko Salatiga 01", disetujui=None):
    if disetujui is None:
        disetujui = dikirim
    return {
        "nomor": f"PRM-TES-{status}-{diminta}-{hari_lalu}", "toko": toko, "status": status,
        "items": [{"produk_id": produk_id, "qty_diminta": diminta, "qty_disetujui": disetujui, "qty_dikirim": dikirim}],
        "dibuat": sekarang() - timedelta(days=hari_lalu),
    }


@pytest.fixture
def data_readme(app, produk):
    """Data contoh README untuk Minyak: diminta 360 (tanpa DIBATALKAN), selesai 300, dikirim 270."""
    m = produk["minyak"]
    with app.app_context():
        get_db().permintaan.insert_many([
            permintaan(m, "DITERIMA", 200, 200, hari_lalu=5),
            permintaan(m, "DIKIRIM", 70, 70, hari_lalu=3),
            permintaan(m, "DITOLAK", 30, None, hari_lalu=2),        # dihitung dikirim 0
            permintaan(m, "DISETUJUI", 60, None, hari_lalu=1, disetujui=60),  # demand ya, fill rate belum
            permintaan(m, "DIBATALKAN", 999, None, hari_lalu=1),    # tidak dihitung sama sekali
            permintaan(m, "DITERIMA", 500, 500, hari_lalu=40),      # di luar 30 hari
        ])
    return produk


def test_demand_tanpa_dibatalkan_dan_hanya_30_hari(app, data_readme):
    with app.app_context():
        assert insight.demand_per_produk()[data_readme["minyak"]] == 360


def test_fill_rate_ditolak_dihitung_nol_dibatalkan_tidak(app, data_readme):
    with app.app_context():
        hasil = insight.fill_rate()
    assert (hasil["dikirim"], hasil["diminta"], hasil["persen"]) == (270, 300, 90.0)


def test_dashboard_hanya_untuk_kepala_gudang(client, data_readme):
    login(client, "staff.gudang")
    assert client.get("/api/dashboard").status_code == 403

    client.post("/api/logout")
    login(client, "kepala.gudang")
    data = client.get("/api/dashboard").get_json()
    assert data["fill_rate"]["persen"] == 90.0
    assert len(data["tren"]) == 30
    assert data["ringkasan"]["menunggu_kirim"] == 1


def test_angka_beranda_sesuai_role(client, data_readme):
    login(client, "staff.gudang")
    assert client.get("/api/beranda").get_json()["permintaan"][0]["teks"] == "1 siap dikirim"

    client.post("/api/logout")
    login(client, "toko.salatiga01")
    assert "permintaan-saya" in client.get("/api/beranda").get_json()
