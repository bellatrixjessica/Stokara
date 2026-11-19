import pytest
from bson import ObjectId

from app.db import get_db
from app.models.user import KEPALA_TOKO
from tests.conftest import tambah_akun
from tests.helper import login


@pytest.fixture
def stok_awal(app, produk):
    with app.app_context():
        get_db().master_produk.update_one({"_id": produk["minyak"]}, {"$set": {"stok": 100}})
        get_db().master_produk.update_one({"_id": produk["beras"]}, {"$set": {"stok": 10}})
    return produk


def sebagai(client, username):
    client.post("/api/logout")
    login(client, username)


def ajukan(client, produk, minyak=30, beras=5):
    sebagai(client, "toko.salatiga01")
    items = [{"produk_id": str(produk["minyak"]), "qty": minyak}]
    if beras:
        items.append({"produk_id": str(produk["beras"]), "qty": beras})
    respon = client.post("/api/permintaan", json={"catatan": "", "items": items})
    assert respon.status_code == 201, respon.get_json()
    nomor = respon.get_json()["nomor"]
    return [p for p in client.get("/api/permintaan").get_json() if p["nomor"] == nomor][0]["id"]


def qty(produk, minyak, beras=None):
    items = [{"produk_id": str(produk["minyak"]), "qty": minyak}]
    if beras is not None:
        items.append({"produk_id": str(produk["beras"]), "qty": beras})
    return {"items": items}


def setujui(client, pid, isi):
    sebagai(client, "kepala.gudang")
    return client.post(f"/api/permintaan/{pid}/setujui", json=isi)


def kirim(client, pid):
    sebagai(client, "staff.gudang")
    return client.post(f"/api/permintaan/{pid}/kirim")


def status(app, pid):
    with app.app_context():
        return get_db().permintaan.find_one({"_id": ObjectId(pid)})["status"]


def stok_fisik(app, produk_id):
    with app.app_context():
        return get_db().master_produk.find_one({"_id": produk_id})["stok"]


def stok_tersedia(client, kode):
    sebagai(client, "staff.gudang")
    return [p for p in client.get("/api/stok").get_json() if p["kode"] == kode][0]["tersedia"]


def test_ajukan_berstatus_diajukan_dan_kepala_gudang_dapat_notifikasi(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    assert status(app, pid) == "DIAJUKAN"

    sebagai(client, "kepala.gudang")
    notif = client.get("/api/notifikasi").get_json()
    assert notif["belum_dibaca"] == 1
    assert notif["daftar"][0]["judul"].startswith("Permintaan baru PRM-")


def test_diajukan_belum_mengurangi_stok_tersedia(client, stok_awal):
    ajukan(client, stok_awal, minyak=30)
    assert stok_tersedia(client, "P-0001") == 100


def test_setujui_mengurangi_stok_tersedia_bukan_stok_fisik(client, app, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    assert setujui(client, pid, qty(stok_awal, 30, 5)).status_code == 200

    assert status(app, pid) == "DISETUJUI"
    assert stok_tersedia(client, "P-0001") == 70
    assert stok_fisik(app, stok_awal["minyak"]) == 100


def test_qty_disetujui_tidak_boleh_melebihi_diminta(client, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    respon = setujui(client, pid, qty(stok_awal, 31, 5))
    assert respon.status_code == 400
    assert "melebihi qty diminta" in respon.get_json()["pesan"]


def test_qty_disetujui_tidak_boleh_melebihi_stok_tersedia(client, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=20)
    respon = setujui(client, pid, qty(stok_awal, 30, 15))
    assert respon.status_code == 400
    assert "stok tersedia hanya 10" in respon.get_json()["pesan"]

    assert setujui(client, pid, qty(stok_awal, 30, 10)).status_code == 200


def test_stok_yang_sudah_dipesan_tidak_bisa_disetujui_lagi(client, stok_awal):
    pertama = ajukan(client, stok_awal, minyak=80, beras=0)
    setujui(client, pertama, qty(stok_awal, 80))
    kedua = ajukan(client, stok_awal, minyak=30, beras=0)

    respon = setujui(client, kedua, qty(stok_awal, 30))
    assert respon.status_code == 400
    assert "stok tersedia hanya 20" in respon.get_json()["pesan"]


def test_semua_qty_nol_harus_pakai_tolak(client, stok_awal):
    pid = ajukan(client, stok_awal)
    respon = setujui(client, pid, qty(stok_awal, 0, 0))
    assert respon.status_code == 400
    assert "Gunakan Tolak" in respon.get_json()["pesan"]


def test_qty_harus_diisi_untuk_semua_produk(client, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    assert setujui(client, pid, qty(stok_awal, 30)).status_code == 400


def test_toko_diberi_tahu_jika_qty_disesuaikan(client, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=20)
    setujui(client, pid, qty(stok_awal, 30, 10))

    sebagai(client, "toko.salatiga01")
    notif = client.get("/api/notifikasi").get_json()
    assert "Qty disesuaikan: 40 dari 50" in notif["daftar"][0]["pesan"]

    client.post("/api/notifikasi/baca")
    assert client.get("/api/notifikasi").get_json()["belum_dibaca"] == 0


def test_tolak_wajib_dengan_alasan(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/permintaan/{pid}/tolak", json={"alasan": "  "}).status_code == 400
    assert client.post(f"/api/permintaan/{pid}/tolak", json={"alasan": "Stok kosong"}).status_code == 200
    assert status(app, pid) == "DITOLAK"


def test_tolak_dari_disetujui_mengembalikan_stok_tersedia(client, app, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=0)
    setujui(client, pid, qty(stok_awal, 30))
    assert stok_tersedia(client, "P-0001") == 70

    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/permintaan/{pid}/tolak", json={"alasan": "Truk rusak"}).status_code == 200
    assert status(app, pid) == "DITOLAK"
    assert stok_tersedia(client, "P-0001") == 100


def test_batal_hanya_dari_diajukan(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    setujui(client, pid, qty(stok_awal, 30, 5))

    sebagai(client, "toko.salatiga01")
    assert client.post(f"/api/permintaan/{pid}/batal").status_code == 400
    assert status(app, pid) == "DISETUJUI"


def test_toko_bisa_membatalkan_yang_masih_diajukan(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    assert client.post(f"/api/permintaan/{pid}/batal").status_code == 200
    assert status(app, pid) == "DIBATALKAN"


def test_kirim_qty_dikirim_sama_dengan_disetujui_dan_stok_berkurang(client, app, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    setujui(client, pid, qty(stok_awal, 25, 5))
    assert kirim(client, pid).status_code == 200

    assert status(app, pid) == "DIKIRIM"
    assert stok_fisik(app, stok_awal["minyak"]) == 75
    assert stok_fisik(app, stok_awal["beras"]) == 5
    with app.app_context():
        p = get_db().permintaan.find_one({"_id": ObjectId(pid)})
        assert [i["qty_dikirim"] for i in p["items"]] == [25, 5]
        assert get_db().mutasi_stok.count_documents({"jenis": "KELUAR", "referensi": p["nomor"]}) == 2


def test_tidak_ada_pengiriman_sebagian(client, app, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    setujui(client, pid, qty(stok_awal, 30, 5))
    with app.app_context():
        get_db().master_produk.update_one({"_id": stok_awal["beras"]}, {"$set": {"stok": 3}})

    respon = kirim(client, pid)
    assert respon.status_code == 400
    assert "Beras Premium 5kg (perlu 5, stok fisik 3)" in respon.get_json()["pesan"]
    assert status(app, pid) == "DISETUJUI"
    assert stok_fisik(app, stok_awal["minyak"]) == 100


def test_setelah_qty_diubah_pengiriman_berhasil(client, app, stok_awal):
    pid = ajukan(client, stok_awal, minyak=30, beras=5)
    setujui(client, pid, qty(stok_awal, 30, 5))
    with app.app_context():
        get_db().master_produk.update_one({"_id": stok_awal["beras"]}, {"$set": {"stok": 3}})

    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/permintaan/{pid}/ubah-qty", json=qty(stok_awal, 30, 3)).status_code == 200
    assert kirim(client, pid).status_code == 200
    assert stok_fisik(app, stok_awal["beras"]) == 0


def test_tidak_bisa_dikirim_dua_kali(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    setujui(client, pid, qty(stok_awal, 30, 5))
    assert kirim(client, pid).status_code == 200
    assert kirim(client, pid).status_code == 400
    assert stok_fisik(app, stok_awal["minyak"]) == 70


def test_toko_konfirmasi_diterima_setelah_dikirim(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    assert client.post(f"/api/permintaan/{pid}/terima").status_code == 400

    setujui(client, pid, qty(stok_awal, 30, 5))
    kirim(client, pid)
    sebagai(client, "toko.salatiga01")
    assert client.post(f"/api/permintaan/{pid}/terima").status_code == 200
    assert status(app, pid) == "DITERIMA"


def test_hak_akses_aksi_per_role(client, stok_awal):
    pid = ajukan(client, stok_awal)

    sebagai(client, "staff.gudang")
    assert client.post(f"/api/permintaan/{pid}/setujui", json=qty(stok_awal, 30, 5)).status_code == 403
    sebagai(client, "toko.salatiga01")
    assert client.post(f"/api/permintaan/{pid}/setujui", json=qty(stok_awal, 30, 5)).status_code == 403

    setujui(client, pid, qty(stok_awal, 30, 5))
    sebagai(client, "kepala.gudang")
    assert client.post(f"/api/permintaan/{pid}/kirim").status_code == 403


def test_kepala_toko_hanya_melihat_permintaan_tokonya(client, app, stok_awal):
    pid = ajukan(client, stok_awal)
    with app.app_context():
        toko_lain = get_db().master_toko.insert_one({"kode": "TK-02", "nama": "Toko Ungaran 01", "aktif": True}).inserted_id
        tambah_akun("toko.ungaran01", "Kepala Toko Ungaran 01", KEPALA_TOKO, toko_lain)

    sebagai(client, "toko.ungaran01")
    assert client.get("/api/permintaan").get_json() == []
    assert client.get(f"/api/permintaan/{pid}").status_code == 404
    assert client.post(f"/api/permintaan/{pid}/batal").status_code == 404


def test_toko_tidak_melihat_angka_stok_gudang(client, stok_awal):
    pid = ajukan(client, stok_awal)
    item = client.get(f"/api/permintaan/{pid}").get_json()["items"][0]
    assert "stok_fisik" not in item and "tersedia" not in item
