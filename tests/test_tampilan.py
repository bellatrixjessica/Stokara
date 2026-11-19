from flask import abort

from app.models.user import ADMIN, KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG
from app.utils.tampilan import menu_untuk
from tests.helper import login


def id_menu(role):
    return [m["id"] for m in menu_untuk(role)]


def test_menu_admin_hanya_master_data():
    assert id_menu(ADMIN) == ["beranda", "produk", "toko", "supplier", "karyawan"]


def test_menu_kepala_gudang_ada_dashboard_dan_laporan():
    menu = id_menu(KEPALA_GUDANG)
    assert "dashboard" in menu and "laporan" in menu
    assert "produk" not in menu


def test_menu_staff_gudang_tanpa_dashboard_dan_laporan():
    menu = id_menu(STAFF_GUDANG)
    assert "dashboard" not in menu and "laporan" not in menu
    assert "barang-masuk" in menu


def test_menu_kepala_toko():
    assert id_menu(KEPALA_TOKO) == ["beranda", "permintaan-saya", "laporan"]


def test_halaman_awal_belum_login_ke_login(client):
    respon = client.get("/")
    assert respon.status_code == 302
    assert respon.headers["Location"].endswith("/login")


def test_halaman_login_bisa_dibuka(client):
    respon = client.get("/login")
    assert respon.status_code == 200
    assert b"login.js" in respon.data


def test_beranda_tanpa_login_diarahkan_ke_login(client):
    respon = client.get("/beranda")
    assert respon.status_code == 302
    assert respon.headers["Location"].endswith("/login")


def test_sudah_login_buka_login_diarahkan_ke_beranda(client):
    login(client, "admin")
    respon = client.get("/login")
    assert respon.headers["Location"].endswith("/beranda")


def test_beranda_berisi_data_pengguna_dan_menu_sesuai_role(client):
    login(client, "toko.salatiga01")
    halaman = client.get("/beranda").get_data(as_text=True)
    assert "Kepala Toko Salatiga 01" in halaman
    assert "Permintaan Barang" in halaman
    assert "Dashboard" not in halaman
    assert "password_hash" not in halaman


def test_halaman_tidak_ada_tampil_404(client):
    respon = client.get("/halaman-tidak-ada")
    assert respon.status_code == 404
    assert "Halaman tidak ditemukan" in respon.get_data(as_text=True)


def test_api_tidak_ada_dapat_json(client):
    respon = client.get("/api/tidak-ada")
    assert respon.status_code == 404
    assert "pesan" in respon.get_json()


def test_halaman_dilarang_tampil_403(app):
    @app.get("/contoh-dilarang")
    def contoh():
        abort(403)

    respon = app.test_client().get("/contoh-dilarang")
    assert respon.status_code == 403
    assert "Akses ditolak" in respon.get_data(as_text=True)
