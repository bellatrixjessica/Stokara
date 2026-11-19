import pytest
from bson import ObjectId

from app.db import get_db
from tests.helper import login


@pytest.fixture
def stok_awal(app, produk):
    with app.app_context():
        get_db().master_produk.update_one({"_id": produk["minyak"]}, {"$set": {"stok": 50}})
        get_db().master_produk.update_one({"_id": produk["beras"]}, {"$set": {"stok": 10}})
    return produk


def sebagai(client, username):
    client.post("/api/logout")
    login(client, username)


def hitung(client, produk, minyak=47, beras=10):
    sebagai(client, "staff.gudang")
    items = [{"produk_id": str(produk["minyak"]), "qty": minyak}]
    if beras is not None:
        items.append({"produk_id": str(produk["beras"]), "qty": beras})
    respon = client.post("/api/opname", json={"catatan": "Rak A", "items": items})
    assert respon.status_code == 201, respon.get_json()
    return client.get("/api/opname").get_json()[0]["id"]


def stok(app, produk_id):
    with app.app_context():
        return get_db().master_produk.find_one({"_id": produk_id})["stok"]


def test_hasil_hitung_mencatat_selisih_tanpa_mengubah_stok(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47, beras=12)

    opname = client.get("/api/opname").get_json()[0]
    assert opname["status"] == "MENUNGGU"
    assert [(i["stok_sistem"], i["stok_hitung"], i["selisih"]) for i in opname["items"]] == [(50, 47, -3), (10, 12, 2)]
    assert stok(app, stok_awal["minyak"]) == 50
    assert oid


def test_kepala_gudang_dapat_notifikasi(client, stok_awal):
    hitung(client, stok_awal)
    sebagai(client, "kepala.gudang")
    notif = client.get("/api/notifikasi").get_json()
    assert notif["daftar"][0]["judul"].endswith("menunggu pemeriksaan")


def test_disetujui_stok_dikoreksi_dan_tercatat_adjust(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47, beras=12)
    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/opname/{oid}/setujui").status_code == 200

    assert stok(app, stok_awal["minyak"]) == 47
    assert stok(app, stok_awal["beras"]) == 12
    with app.app_context():
        mutasi = list(get_db().mutasi_stok.find({"jenis": "ADJUST"}))
        assert sorted(m["perubahan"] for m in mutasi) == [-3, 2]
        assert get_db().opname.find_one({"_id": ObjectId(oid)})["status"] == "DISETUJUI"


def test_produk_tanpa_selisih_tidak_membuat_mutasi(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=50, beras=None)
    sebagai(client, "kepala.gudang")
    client.post(f"/api/opname/{oid}/setujui")
    with app.app_context():
        assert get_db().mutasi_stok.count_documents({"jenis": "ADJUST"}) == 0


def test_yang_dikoreksi_selisihnya_bukan_angka_hitungan(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47, beras=None)
    with app.app_context():
        get_db().master_produk.update_one({"_id": stok_awal["minyak"]}, {"$inc": {"stok": 20}})

    sebagai(client, "kepala.gudang")
    client.post(f"/api/opname/{oid}/setujui")
    assert stok(app, stok_awal["minyak"]) == 67


def test_koreksi_yang_membuat_minus_ditolak(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47, beras=None)
    with app.app_context():
        get_db().master_produk.update_one({"_id": stok_awal["minyak"]}, {"$set": {"stok": 2}})

    sebagai(client, "kepala.gudang")
    respon = client.post(f"/api/opname/{oid}/setujui")
    assert respon.status_code == 400
    assert "hitung ulang" in respon.get_json()["pesan"]
    assert stok(app, stok_awal["minyak"]) == 2


def test_ditolak_wajib_alasan_dan_stok_tetap(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47)
    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/opname/{oid}/tolak", json={"alasan": ""}).status_code == 400
    assert client.post(f"/api/opname/{oid}/tolak", json={"alasan": "Hitung ulang rak A"}).status_code == 200
    assert stok(app, stok_awal["minyak"]) == 50


def test_tidak_bisa_disetujui_dua_kali(client, app, stok_awal):
    oid = hitung(client, stok_awal, minyak=47, beras=None)
    sebagai(client, "kepala.gudang")
    client.post(f"/api/opname/{oid}/setujui")
    assert client.post(f"/api/opname/{oid}/setujui").status_code == 400
    assert stok(app, stok_awal["minyak"]) == 47


def test_produk_yang_masih_menunggu_tidak_bisa_dihitung_lagi(client, stok_awal):
    hitung(client, stok_awal, minyak=47, beras=None)
    respon = client.post("/api/opname", json={"catatan": "", "items": [{"produk_id": str(stok_awal["minyak"]), "qty": 48}]})
    assert respon.status_code == 400
    assert "masih ada di opname lain" in respon.get_json()["pesan"]


def test_hak_akses_opname(client, stok_awal):
    oid = hitung(client, stok_awal)
    assert client.post(f"/api/opname/{oid}/setujui").status_code == 403

    sebagai(client, "kepala.gudang")
    data = {"catatan": "", "items": [{"produk_id": str(stok_awal["beras"]), "qty": 1}]}
    assert client.post("/api/opname", json=data).status_code == 403

    sebagai(client, "toko.salatiga01")
    assert client.get("/api/opname").status_code == 403


def test_validasi_hasil_hitung(client, stok_awal):
    sebagai(client, "staff.gudang")
    minyak = str(stok_awal["minyak"])
    for items in ([], [{"produk_id": minyak, "qty": -1}], [{"produk_id": minyak, "qty": "5"}]):
        assert client.post("/api/opname", json={"catatan": "", "items": items}).status_code == 400
