import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db
from app.models.user import ADMIN, KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG
from config import TestConfig
from tests.helper import PASSWORD


HASH_PASSWORD = generate_password_hash(PASSWORD)


def tambah_akun(username, nama, role, toko_id=None):
    get_db().users.insert_one({
        "username": username, "password_hash": HASH_PASSWORD, "nama": nama,
        "role": role, "toko_id": toko_id, "aktif": True,
    })


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        toko_id = get_db().master_toko.insert_one(
            {"kode": "TK-01", "nama": "Toko Salatiga 01", "aktif": True}
        ).inserted_id
        tambah_akun("admin", "Admin Stokara", ADMIN)
        tambah_akun("kepala.gudang", "Kepala Gudang Semarang", KEPALA_GUDANG)
        tambah_akun("staff.gudang", "Staff Gudang Semarang", STAFF_GUDANG)
        tambah_akun("toko.salatiga01", "Kepala Toko Salatiga 01", KEPALA_TOKO, toko_id)
    return app


@pytest.fixture
def produk(app):
    with app.app_context():
        db = get_db()
        supplier_id = db.master_supplier.insert_one(
            {"kode": "SUP-01", "nama": "PT Sumber Pangan Jaya", "aktif": True}
        ).inserted_id
        minyak = db.master_produk.insert_one({
            "kode": "P-0001", "nama": "Minyak Goreng 1L", "kategori": "Sembako", "satuan": "PCS",
            "supplier_id": supplier_id, "lead_time_hari": 2, "stok": 0, "aktif": True,
        }).inserted_id
        beras = db.master_produk.insert_one({
            "kode": "P-0002", "nama": "Beras Premium 5kg", "kategori": "Sembako", "satuan": "PCS",
            "supplier_id": supplier_id, "lead_time_hari": 3, "stok": 0, "aktif": True,
        }).inserted_id
    return {"supplier": supplier_id, "minyak": minyak, "beras": beras}


@pytest.fixture
def client(app):
    return app.test_client()
