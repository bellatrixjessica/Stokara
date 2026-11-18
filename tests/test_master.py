"""Test master data: toko, supplier, produk, karyawan (khusus Admin)."""
from app.db import get_db
from tests.helper import login


def id_dari_db(app, collection, kode_atau_username):
    with app.app_context():
        kunci = "username" if collection == "users" else "kode"
        return str(get_db()[collection].find_one({kunci: kode_atau_username})["_id"])


def tambah_supplier(client, kode="SUP-01"):
    return client.post("/api/master/supplier", json={
        "kode": kode, "nama": "PT Sumber Pangan", "telepon": "024-111", "alamat": "Semarang",
    })


def data_produk(sid, **ubah):
    data = {
        "kode": "P-0001", "nama": "Minyak Goreng 1L", "kategori": "Sembako",
        "satuan": "PCS", "supplier_id": sid, "lead_time_hari": 2,
    }
    data.update(ubah)
    return data


# ---------- Hak akses ----------

def test_selain_admin_tidak_bisa_membuka_master(client):
    login(client, "kepala.gudang")
    assert client.get("/api/master/toko").status_code == 403
    assert client.get("/master/produk").status_code == 403


def test_admin_bisa_membuka_semua_halaman_master(client):
    login(client, "admin")
    for url in ["/master/produk", "/master/toko", "/master/supplier", "/master/karyawan"]:
        assert client.get(url).status_code == 200


# ---------- Toko ----------

def test_tambah_toko_kode_jadi_huruf_besar(client):
    login(client, "admin")
    respon = client.post("/api/master/toko", json={"kode": "tk-02", "nama": "Toko Ungaran 01", "alamat": "Ungaran"})
    assert respon.status_code == 201
    kode = [t["kode"] for t in client.get("/api/master/toko").get_json()]
    assert "TK-02" in kode


def test_kode_toko_duplikat_ditolak(client):
    login(client, "admin")
    respon = client.post("/api/master/toko", json={"kode": "TK-01", "nama": "Toko Lain", "alamat": "X"})
    assert respon.status_code == 400
    assert "sudah dipakai" in respon.get_json()["pesan"]


def test_kode_dengan_simbol_ditolak(client):
    login(client, "admin")
    respon = client.post("/api/master/toko", json={"kode": "TK 01!", "nama": "Toko", "alamat": "X"})
    assert respon.status_code == 400


def test_ubah_dan_nonaktifkan_toko(client, app):
    login(client, "admin")
    toko_id = id_dari_db(app, "master_toko", "TK-01")

    assert client.put(f"/api/master/toko/{toko_id}", json={"nama": "Toko Salatiga Baru", "alamat": "Jl. Baru"}).status_code == 200
    assert client.post(f"/api/master/toko/{toko_id}/status", json={"aktif": False}).status_code == 200

    toko = client.get("/api/master/toko").get_json()[0]
    assert toko["nama"] == "Toko Salatiga Baru"
    assert toko["kode"] == "TK-01"   # kode tidak berubah
    assert toko["aktif"] is False


def test_id_rusak_atau_tidak_ada_404(client):
    login(client, "admin")
    assert client.put("/api/master/toko/bukan-id", json={"nama": "A", "alamat": "B"}).status_code == 404
    assert client.put("/api/master/toko/65f000000000000000000000", json={"nama": "A", "alamat": "B"}).status_code == 404


# ---------- Supplier & Produk ----------

def test_tambah_produk_stok_awal_nol(client, app):
    login(client, "admin")
    tambah_supplier(client)
    supplier_id = id_dari_db(app, "master_supplier", "SUP-01")

    assert client.post("/api/master/produk", json=data_produk(supplier_id)).status_code == 201
    produk = client.get("/api/master/produk").get_json()[0]
    assert produk["stok"] == 0
    assert produk["supplier"] == "PT Sumber Pangan"


def test_produk_dengan_supplier_nonaktif_ditolak(client, app):
    login(client, "admin")
    tambah_supplier(client)
    supplier_id = id_dari_db(app, "master_supplier", "SUP-01")
    client.post(f"/api/master/supplier/{supplier_id}/status", json={"aktif": False})

    respon = client.post("/api/master/produk", json=data_produk(supplier_id))
    assert respon.status_code == 400
    assert "Supplier" in respon.get_json()["pesan"]


def test_validasi_isian_produk(client, app):
    login(client, "admin")
    tambah_supplier(client)
    sid = id_dari_db(app, "master_supplier", "SUP-01")

    salah = [
        data_produk(sid, lead_time_hari="3"),     # angka dikirim sebagai teks
        data_produk(sid, lead_time_hari=True),    # true bukan angka
        data_produk(sid, lead_time_hari=0),       # minimal 1 hari
        data_produk(sid, satuan="KILO"),          # satuan tidak dikenal
        data_produk(sid, supplier_id="abc"),      # supplier tidak valid
        data_produk(sid, stok=999),               # stok tidak boleh diisi dari form
    ]
    for data in salah:
        assert client.post("/api/master/produk", json=data).status_code == 400, data


# ---------- Karyawan ----------

def test_daftar_karyawan_tanpa_password_hash(client):
    login(client, "admin")
    for user in client.get("/api/master/karyawan").get_json():
        assert "password_hash" not in user


def test_karyawan_baru_bisa_login(client):
    login(client, "admin")
    respon = client.post("/api/master/karyawan", json={
        "username": "staff.dua", "nama": "Staff Dua", "role": "staff_gudang",
        "toko_id": "", "password": "passwordbaru1",
    })
    assert respon.status_code == 201

    client.post("/api/logout")
    assert login(client, "staff.dua", "passwordbaru1").status_code == 200


def test_kepala_toko_tanpa_toko_ditolak(client):
    login(client, "admin")
    respon = client.post("/api/master/karyawan", json={
        "username": "toko.baru", "nama": "Kepala Toko Baru", "role": "kepala_toko",
        "toko_id": "", "password": "passwordbaru1",
    })
    assert respon.status_code == 400


def test_password_kurang_dari_8_ditolak(client):
    login(client, "admin")
    respon = client.post("/api/master/karyawan", json={
        "username": "staff.dua", "nama": "Staff Dua", "role": "staff_gudang", "toko_id": "", "password": "123",
    })
    assert respon.status_code == 400


def test_reset_password(client, app):
    login(client, "admin")
    user_id = id_dari_db(app, "users", "staff.gudang")
    assert client.post(f"/api/master/karyawan/{user_id}/password", json={"password": "passwordbaru1"}).status_code == 200

    client.post("/api/logout")
    assert login(client, "staff.gudang").status_code == 401              # password lama
    assert login(client, "staff.gudang", "passwordbaru1").status_code == 200


def test_karyawan_dinonaktifkan_tidak_bisa_login(client, app):
    login(client, "admin")
    user_id = id_dari_db(app, "users", "staff.gudang")
    client.post(f"/api/master/karyawan/{user_id}/status", json={"aktif": False})

    client.post("/api/logout")
    assert login(client, "staff.gudang").status_code == 401


def test_admin_tidak_bisa_mengunci_dirinya_sendiri(client, app):
    login(client, "admin")
    admin_id = id_dari_db(app, "users", "admin")

    nonaktif = client.post(f"/api/master/karyawan/{admin_id}/status", json={"aktif": False})
    ganti_role = client.put(f"/api/master/karyawan/{admin_id}", json={"nama": "Admin", "role": "staff_gudang", "toko_id": ""})

    assert nonaktif.status_code == 400
    assert ganti_role.status_code == 400
