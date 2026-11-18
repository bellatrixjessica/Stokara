"""Test data contoh (seed) dan index MongoDB."""
import pytest
from pymongo.errors import DuplicateKeyError

from app.db import get_db
from app.models import indeks, insight
from app.models.user import KEPALA_TOKO
from scripts import seed_data
from tests.conftest import tambah_akun
from tests.helper import login


@pytest.fixture
def db_contoh(app):
    """Database berisi 3 toko (dengan Kepala Toko) dan data contoh 30 hari."""
    with app.app_context():
        db = get_db()
        for kode, nama in [("TK-02", "Toko Ungaran 01"), ("TK-03", "Toko Semarang Tengah 01")]:
            toko_id = db.master_toko.insert_one({"kode": kode, "nama": nama, "aktif": True}).inserted_id
            tambah_akun("toko." + kode.lower(), "Kepala " + nama, KEPALA_TOKO, toko_id)
        seed_data.buat_data_contoh(db)
        yield db


# ---------------------------------------------------------------- data contoh

def test_stok_produk_sama_dengan_jumlah_mutasi(db_contoh):
    for produk in db_contoh.master_produk.find():
        total = sum(m["perubahan"] for m in db_contoh.mutasi_stok.find({"produk_id": produk["_id"]}))
        assert produk["stok"] == total, produk["kode"]
        assert produk["stok"] >= 0


def test_tidak_ada_pengiriman_sebagian(db_contoh):
    for p in db_contoh.permintaan.find({"status": {"$in": ["DIKIRIM", "DITERIMA"]}}):
        for item in p["items"]:
            assert item["qty_dikirim"] == item["qty_disetujui"] <= item["qty_diminta"]


def test_ada_pekerjaan_menunggu_untuk_demo(db_contoh):
    assert db_contoh.permintaan.count_documents({"status": "DIAJUKAN"}) == 1
    assert db_contoh.permintaan.count_documents({"status": "DISETUJUI"}) == 1


def test_hasil_dashboard_data_contoh(app, db_contoh):
    data = insight.dashboard()
    assert 80 <= data["fill_rate"]["persen"] <= 92
    assert data["ringkasan"]["kritis"] == 1
    assert data["ringkasan"]["perlu_restock"] == 1


def test_nomor_dokumen_tidak_ganda(db_contoh):
    nomor = [p["nomor"] for p in db_contoh.permintaan.find()]
    assert len(nomor) == len(set(nomor))


# ---------------------------------------------------------------- index

def test_index_unique_menolak_kode_ganda(app):
    with app.app_context():
        db = get_db()
        indeks.buat_semua(db)
        db.master_supplier.insert_one({"kode": "SUP-99", "nama": "A"})
        with pytest.raises(DuplicateKeyError):
            db.master_supplier.insert_one({"kode": "SUP-99", "nama": "B"})


def test_semua_index_terdaftar(app):
    with app.app_context():
        db = get_db()
        indeks.buat_semua(db)
        nama = {i["name"] for i in db.permintaan.list_indexes()}
        assert {"nomor_permintaan_unik", "toko_status_tanggal", "status_tanggal"} <= nama


def test_cari_stok_berdasarkan_kode(client, produk):
    # Pencarian kata memakai $text (text index) yang hanya ada di MongoDB asli,
    # jadi dicek dengan scripts/buat_index.py --cek di Atlas. Di sini yang dites cari kode.
    login(client, "staff.gudang")
    hasil = client.get("/api/stok?cari=p-0002").get_json()
    assert [p["kode"] for p in hasil] == ["P-0002"]
