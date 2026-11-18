"""Test laporan periode: rentang tanggal WIB, isi tiap laporan, dan hak akses."""
from datetime import date, datetime, timezone

import pytest

from app.db import get_db
from app.models.laporan import rentang_waktu
from app.utils.validasi import ValidasiError, tanggal
from tests.helper import login

PERIODE = "dari=2026-11-01&sampai=2026-11-30"


def waktu_utc(tahun, bulan, hari, jam=3):
    return datetime(tahun, bulan, hari, jam, tzinfo=timezone.utc)


def tambah_permintaan(db, nomor, status, diminta, disetujui=None, dikirim=None,
                      dibuat=None, toko_id=None, toko="Toko Salatiga 01"):
    if toko_id is None:
        toko_id = db.master_toko.find_one({"kode": "TK-01"})["_id"]
    db.permintaan.insert_one({
        "nomor": nomor, "toko_id": toko_id, "toko": toko, "status": status,
        "items": [{"produk_id": None, "kode": "P-0001", "nama": "Minyak Goreng 1L", "satuan": "PCS",
                   "qty_diminta": diminta, "qty_disetujui": disetujui, "qty_dikirim": dikirim}],
        "dibuat": dibuat or waktu_utc(2026, 11, 10),
    })


@pytest.fixture
def data_permintaan(app):
    """5 permintaan Toko Salatiga + 1 permintaan toko lain, semua di bulan November 2026."""
    with app.app_context():
        db = get_db()
        tambah_permintaan(db, "PRM-1", "DITERIMA", 50, 40, 40)
        tambah_permintaan(db, "PRM-2", "DIKIRIM", 30, 30, 30)
        tambah_permintaan(db, "PRM-3", "DITOLAK", 20)               # dikirim dihitung 0
        tambah_permintaan(db, "PRM-4", "DIBATALKAN", 99)            # tidak dihitung
        tambah_permintaan(db, "PRM-5", "DIAJUKAN", 10)              # belum selesai
        lain = db.master_toko.insert_one({"kode": "TK-02", "nama": "Toko Ungaran 01", "aktif": True}).inserted_id
        tambah_permintaan(db, "PRM-6", "DITERIMA", 10, 10, 10, toko_id=lain, toko="Toko Ungaran 01")
        return {"toko_lain": str(lain)}


def ringkasan(hasil):
    return {r["label"]: r["nilai"] for r in hasil["ringkasan"]}


# ---------------------------------------------------------------- tanggal

def test_rentang_satu_hari_wib_dalam_utc():
    # 19 Nov 00.00 WIB = 18 Nov 17.00 UTC, sampai 20 Nov 00.00 WIB = 19 Nov 17.00 UTC
    waktu = rentang_waktu(date(2026, 11, 19), date(2026, 11, 19))
    assert waktu["$gte"] == datetime(2026, 11, 18, 17, tzinfo=timezone.utc)
    assert waktu["$lt"] == datetime(2026, 11, 19, 17, tzinfo=timezone.utc)


def test_rentang_tanggal_terbalik_atau_terlalu_panjang_ditolak():
    with pytest.raises(ValidasiError):
        rentang_waktu(date(2026, 11, 19), date(2026, 11, 1))
    with pytest.raises(ValidasiError):
        rentang_waktu(date(2025, 1, 1), date(2026, 11, 19))


@pytest.mark.parametrize("nilai", ["19/11/2026", "2026-02-31", "", 20261119, {"$gt": ""}])
def test_format_tanggal_salah_ditolak(nilai):
    with pytest.raises(ValidasiError):
        tanggal({"dari": nilai}, "dari", "Tanggal awal")


def test_tanggal_kosong_di_api_ditolak(client):
    login(client, "kepala.gudang")
    respon = client.get("/api/laporan/permintaan?dari=2026-11-01")
    assert respon.status_code == 400


# ---------------------------------------------------------------- laporan permintaan

def test_laporan_permintaan_fill_rate_sama_dengan_aturan_dashboard(client, data_permintaan):
    login(client, "kepala.gudang")
    hasil = client.get("/api/laporan/permintaan?" + PERIODE).get_json()

    angka = ringkasan(hasil)
    assert angka["Permintaan"] == 6
    assert angka["Qty diminta"] == 50 + 30 + 20 + 10   # hanya yang selesai: Diterima, Dikirim, Ditolak
    assert angka["Qty dikirim"] == 40 + 30 + 0 + 10
    assert angka["Fill rate"] == round(80 / 110 * 100, 1)

    baris = {b["nomor"]: b for b in hasil["baris"]}
    assert baris["PRM-3"]["dikirim"] == 0 and baris["PRM-3"]["fill_rate"] == 0
    assert baris["PRM-4"]["dikirim"] is None and baris["PRM-4"]["fill_rate"] is None
    assert baris["PRM-5"]["fill_rate"] is None
    assert baris["PRM-1"]["fill_rate"] == 80.0


def test_batas_tanggal_mengikuti_wib(client, app):
    with app.app_context():
        db = get_db()
        tambah_permintaan(db, "PRM-MALAM", "DIAJUKAN", 5, dibuat=waktu_utc(2026, 11, 19, 16))  # 19 Nov 23.00 WIB
        tambah_permintaan(db, "PRM-BESOK", "DIAJUKAN", 5, dibuat=waktu_utc(2026, 11, 19, 18))  # 20 Nov 01.00 WIB
    login(client, "kepala.gudang")
    hasil = client.get("/api/laporan/permintaan?dari=2026-11-19&sampai=2026-11-19").get_json()
    assert [b["nomor"] for b in hasil["baris"]] == ["PRM-MALAM"]


def test_filter_toko_kepala_gudang(client, data_permintaan):
    login(client, "kepala.gudang")
    hasil = client.get(f"/api/laporan/permintaan?{PERIODE}&toko={data_permintaan['toko_lain']}").get_json()
    assert [b["nomor"] for b in hasil["baris"]] == ["PRM-6"]


def test_kepala_toko_hanya_melihat_tokonya_walaupun_mengirim_toko_lain(client, data_permintaan):
    login(client, "toko.salatiga01")
    hasil = client.get(f"/api/laporan/permintaan?{PERIODE}&toko={data_permintaan['toko_lain']}").get_json()
    assert {b["toko"] for b in hasil["baris"]} == {"Toko Salatiga 01"}
    assert ringkasan(hasil)["Permintaan"] == 5


# ---------------------------------------------------------------- laporan gudang lain

def test_laporan_mutasi_menjumlahkan_per_jenis(client, app):
    with app.app_context():
        db = get_db()
        for jenis, perubahan in [("MASUK", 100), ("KELUAR", -30), ("KELUAR", -20), ("ADJUST", -2)]:
            db.mutasi_stok.insert_one({
                "kode": "P-0001", "nama": "Minyak Goreng 1L", "jenis": jenis, "perubahan": perubahan,
                "stok_sesudah": 0, "referensi": "X", "oleh": {"nama": "Staff"}, "waktu": waktu_utc(2026, 11, 5),
            })
    login(client, "kepala.gudang")
    angka = ringkasan(client.get("/api/laporan/mutasi?" + PERIODE).get_json())
    assert angka == {"Mutasi": 4, "Total masuk": 100, "Total keluar": 50, "Penyesuaian": -2}


def test_laporan_barang_masuk_satu_baris_per_produk(client, app):
    with app.app_context():
        get_db().barang_masuk.insert_one({
            "nomor": "BM-1", "supplier": "PT Sumber Pangan Jaya", "no_surat_jalan": "SJ-1",
            "items": [{"kode": "P-0001", "nama": "Minyak", "satuan": "PCS", "qty": 40},
                      {"kode": "P-0002", "nama": "Beras", "satuan": "PCS", "qty": 25}],
            "dibuat": waktu_utc(2026, 11, 3),
        })
    login(client, "kepala.gudang")
    hasil = client.get("/api/laporan/barang-masuk?" + PERIODE).get_json()
    assert [b["kode"] for b in hasil["baris"]] == ["P-0001", "P-0002"]
    assert ringkasan(hasil) == {"Dokumen": 1, "Supplier": 1, "Produk": 2, "Total qty": 65}


def test_laporan_saran_restock_tanpa_tanggal(client, produk):
    login(client, "kepala.gudang")
    hasil = client.get("/api/laporan/restock").get_json()   # keadaan saat ini, tanggal tidak perlu
    assert [b["kode"] for b in hasil["baris"]] == ["P-0001", "P-0002"]
    assert ringkasan(hasil)["Produk dipantau"] == 2


# ---------------------------------------------------------------- hak akses

def test_kepala_toko_tidak_boleh_laporan_gudang(client):
    login(client, "toko.salatiga01")
    for jenis in ["mutasi", "barang-masuk", "restock"]:
        assert client.get(f"/api/laporan/{jenis}?{PERIODE}").status_code == 403


@pytest.mark.parametrize("username", ["admin", "staff.gudang"])
def test_role_lain_tidak_boleh_membuka_laporan(client, username):
    login(client, username)
    assert client.get("/laporan").status_code == 403
    assert client.get("/api/laporan/permintaan?" + PERIODE).status_code == 403


def test_jenis_laporan_tidak_dikenal(client):
    login(client, "kepala.gudang")
    assert client.get("/api/laporan/gaji?" + PERIODE).status_code == 404


def test_halaman_laporan(client):
    login(client, "kepala.gudang")
    halaman = client.get("/laporan").get_data(as_text=True)
    assert "laporan.js" in halaman and "Toko Salatiga 01" in halaman   # pilihan toko untuk filter

    login(client, "toko.salatiga01")
    halaman = client.get("/laporan").get_data(as_text=True)
    assert '"jenis_laporan": ["permintaan"]' in halaman
