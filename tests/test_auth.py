"""Test login, logout, dan pembatasan akses per role."""
from app.db import get_db
from app.models.user import ADMIN
from app.utils.auth import wajib_login
from tests.helper import login


# ---------- Login ----------

def test_login_berhasil(client):
    respon = login(client, "kepala.gudang")
    assert respon.status_code == 200
    assert respon.get_json()["redirect"] == "/beranda"


def test_username_huruf_besar_tetap_bisa_login(client):
    assert login(client, "  Kepala.Gudang ").status_code == 200


def test_password_salah_ditolak(client):
    respon = login(client, "kepala.gudang", "password-salah")
    assert respon.status_code == 401
    assert respon.get_json()["pesan"] == "Username atau password salah."


def test_username_tidak_terdaftar_pesannya_sama(client):
    respon = login(client, "tidak.ada")
    assert respon.status_code == 401
    assert respon.get_json()["pesan"] == "Username atau password salah."


def test_user_nonaktif_tidak_bisa_login(client, app):
    with app.app_context():
        get_db().users.update_one({"username": "staff.gudang"}, {"$set": {"aktif": False}})
    assert login(client, "staff.gudang").status_code == 401


def test_password_disimpan_dalam_bentuk_hash(app):
    with app.app_context():
        user = get_db().users.find_one({"username": "admin"})
    assert "password" not in user
    assert user["password_hash"] != "rahasia123"
    assert user["password_hash"].startswith("scrypt:")


# ---------- Validasi & sanitasi ----------

def test_injeksi_nosql_ditolak(client):
    respon = client.post("/api/login", json={"username": {"$ne": ""}, "password": {"$ne": ""}})
    assert respon.status_code == 400
    assert respon.get_json()["pesan"] == "Username harus berupa teks."


def test_key_tidak_dikenal_ditolak(client):
    respon = client.post("/api/login", json={"username": "admin", "password": "x", "role": "admin"})
    assert respon.status_code == 400


def test_data_bukan_json_ditolak(client):
    respon = client.post("/api/login", data="username=admin")
    assert respon.status_code == 400


def test_password_kosong_ditolak(client):
    respon = client.post("/api/login", json={"username": "admin", "password": ""})
    assert respon.status_code == 400


# ---------- Session ----------

def test_data_saya_tanpa_login_ditolak(client):
    assert client.get("/api/saya").status_code == 401


def test_data_saya_kepala_toko_berisi_nama_toko(client):
    login(client, "toko.salatiga01")
    data = client.get("/api/saya").get_json()
    assert data["role"] == "kepala_toko"
    assert data["label_role"] == "Kepala Toko"
    assert data["toko"] == "Toko Salatiga 01"
    assert "password_hash" not in data


def test_logout_menghapus_session(client):
    login(client, "admin")
    client.post("/api/logout")
    assert client.get("/api/saya").status_code == 401


def test_user_dinonaktifkan_saat_masih_login_langsung_keluar(client, app):
    login(client, "staff.gudang")
    with app.app_context():
        get_db().users.update_one({"username": "staff.gudang"}, {"$set": {"aktif": False}})
    assert client.get("/api/saya").status_code == 401


# ---------- Hak akses per role ----------

def test_hanya_role_yang_diizinkan_bisa_akses(app):
    # Route contoh khusus Admin, dibuat hanya untuk test ini.
    @app.get("/api/contoh-khusus-admin")
    @wajib_login(ADMIN)
    def contoh():
        return {"pesan": "halo admin"}

    client = app.test_client()

    login(client, "toko.salatiga01")
    assert client.get("/api/contoh-khusus-admin").status_code == 403

    client.post("/api/logout")
    login(client, "admin")
    assert client.get("/api/contoh-khusus-admin").status_code == 200
