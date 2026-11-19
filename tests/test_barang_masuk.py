import re

from app.db import get_db
from tests.helper import login


def data_bm(produk, **ubah):
    data = {
        "supplier_id": str(produk["supplier"]),
        "no_surat_jalan": "SJ-7781",
        "catatan": "",
        "items": [
            {"produk_id": str(produk["minyak"]), "qty": 40},
            {"produk_id": str(produk["beras"]), "qty": 25},
        ],
    }
    data.update(ubah)
    return data


def test_barang_masuk_menambah_stok(client, app, produk):
    login(client, "staff.gudang")
    respon = client.post("/api/barang-masuk", json=data_bm(produk))
    assert respon.status_code == 201

    stok = {p["kode"]: p["fisik"] for p in client.get("/api/stok").get_json()}
    assert stok == {"P-0001": 40, "P-0002": 25}


def test_nomor_barang_masuk_berurutan(client, produk):
    login(client, "staff.gudang")
    nomor1 = client.post("/api/barang-masuk", json=data_bm(produk)).get_json()["nomor"]
    nomor2 = client.post("/api/barang-masuk", json=data_bm(produk)).get_json()["nomor"]

    assert re.fullmatch(r"BM-\d{6}-0001", nomor1)
    assert nomor2.endswith("-0002")


def test_riwayat_mutasi_produk(client, produk):
    login(client, "staff.gudang")
    client.post("/api/barang-masuk", json=data_bm(produk))

    riwayat = client.get(f"/api/stok/{produk['minyak']}/mutasi").get_json()
    assert len(riwayat) == 1
    assert riwayat[0]["jenis"] == "MASUK"
    assert riwayat[0]["referensi"].startswith("BM-")


def test_kepala_gudang_hanya_bisa_melihat(client, produk):
    login(client, "kepala.gudang")
    assert client.get("/api/barang-masuk").status_code == 200
    assert client.get("/api/stok").status_code == 200
    assert client.post("/api/barang-masuk", json=data_bm(produk)).status_code == 403


def test_kepala_toko_tidak_bisa_melihat_stok_gudang(client):
    login(client, "toko.salatiga01")
    assert client.get("/api/stok").status_code == 403
    assert client.get("/barang-masuk").status_code == 403


def test_validasi_barang_masuk(client, app, produk):
    login(client, "staff.gudang")
    minyak = str(produk["minyak"])
    with app.app_context():
        get_db().master_produk.update_one({"_id": produk["beras"]}, {"$set": {"aktif": False}})

    salah = [
        data_bm(produk, items=[]),
        data_bm(produk, items=[{"produk_id": minyak, "qty": 0}]),
        data_bm(produk, items=[{"produk_id": minyak, "qty": "5"}]),
        data_bm(produk, items=[{"produk_id": minyak, "qty": 5}, {"produk_id": minyak, "qty": 3}]),
        data_bm(produk, items=[{"produk_id": str(produk["beras"]), "qty": 5}]),
        data_bm(produk, no_surat_jalan=""),
    ]
    for data in salah:
        assert client.post("/api/barang-masuk", json=data).status_code == 400, data

    with app.app_context():
        assert get_db().barang_masuk.count_documents({}) == 0
        assert get_db().master_produk.find_one({"_id": produk["minyak"]})["stok"] == 0
