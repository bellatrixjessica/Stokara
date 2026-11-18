"""Test model stok: tambah, kurangi, sesuaikan, dan stok tersedia."""
import pytest

from app.db import get_db
from app.models import stok as model_stok
from app.utils.validasi import ValidasiError


def staff():
    return get_db().users.find_one({"username": "staff.gudang"})


def stok_fisik(produk_id):
    return get_db().master_produk.find_one({"_id": produk_id})["stok"]


def test_tambah_stok_tercatat_di_mutasi(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 40, "BM-TES-0001", "Barang masuk", staff())

        assert stok_fisik(produk["minyak"]) == 40
        mutasi = get_db().mutasi_stok.find_one({"produk_id": produk["minyak"]})
        assert mutasi["jenis"] == "MASUK"
        assert mutasi["perubahan"] == 40
        assert mutasi["stok_sebelum"] == 0
        assert mutasi["stok_sesudah"] == 40
        assert mutasi["oleh"]["nama"] == "Staff Gudang Semarang"


def test_kurangi_stok_sampai_nol_boleh(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 10, "BM-1", "-", staff())
        model_stok.kurangi_stok(produk["minyak"], 10, "PRM-1", "-", staff())
        assert stok_fisik(produk["minyak"]) == 0


def test_stok_tidak_bisa_minus(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 5, "BM-1", "-", staff())

        with pytest.raises(ValidasiError):
            model_stok.kurangi_stok(produk["minyak"], 6, "PRM-1", "-", staff())

        assert stok_fisik(produk["minyak"]) == 5                       # tidak berubah
        assert get_db().mutasi_stok.count_documents({"jenis": "KELUAR"}) == 0  # tidak tercatat


def test_koreksi_stok_mencatat_selisih(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 50, "BM-1", "-", staff())
        model_stok.koreksi_stok(produk["minyak"], -3, "OPN-1", "Hasil opname", staff())

        assert stok_fisik(produk["minyak"]) == 47
        mutasi = get_db().mutasi_stok.find_one({"jenis": "ADJUST"})
        assert mutasi["perubahan"] == -3
        assert mutasi["stok_sebelum"] == 50


def test_koreksi_stok_tidak_boleh_membuat_minus(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 2, "BM-1", "-", staff())
        with pytest.raises(ValidasiError):
            model_stok.koreksi_stok(produk["minyak"], -3, "OPN-1", "-", staff())
        assert stok_fisik(produk["minyak"]) == 2


def test_stok_tersedia_dikurangi_qty_disetujui(app, produk):
    with app.app_context():
        model_stok.tambah_stok(produk["minyak"], 100, "BM-1", "-", staff())
        # Permintaan yang sudah DISETUJUI tapi belum dikirim mengurangi stok tersedia.
        # Permintaan DIAJUKAN belum mengurangi apa-apa.
        get_db().permintaan.insert_many([
            {"status": "DISETUJUI", "items": [{"produk_id": produk["minyak"], "qty_disetujui": 30}]},
            {"status": "DISETUJUI", "items": [{"produk_id": produk["minyak"], "qty_disetujui": 20}]},
            {"status": "DIAJUKAN", "items": [{"produk_id": produk["minyak"], "qty_disetujui": None}]},
        ])

        assert model_stok.stok_tersedia(produk["minyak"]) == 50
        baris = [p for p in model_stok.daftar_stok() if p["kode"] == "P-0001"][0]
        assert (baris["fisik"], baris["dipesan"], baris["tersedia"]) == (100, 50, 50)
