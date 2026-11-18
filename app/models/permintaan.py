"""Model permintaan barang dari toko ke gudang (collection permintaan).

ALUR STATUS
                 ┌──────── tolak (Kepala Gudang, wajib alasan) ────────┐
                 │                                                       ▼
  DIAJUKAN ──setujui──► DISETUJUI ──kirim──► DIKIRIM ──terima──► DITERIMA
     │   (Kepala Gudang)   │  ▲   (Staff Gudang)    (Kepala Toko)
     │                     └──┘ ubah qty disetujui (Kepala Gudang)
     │                     │
     │                     └──tolak──► DITOLAK
     └──batal (Kepala Toko)──► DIBATALKAN

ATURAN BISNIS
1. Qty disetujui <= qty diminta, dan <= stok tersedia saat disetujui.
2. Tidak ada pengiriman sebagian: qty dikirim SELALU = qty disetujui.
   Kalau stok fisik ternyata kurang saat akan dikirim, pengiriman ditolak.
   Kepala Gudang lalu mengubah qty disetujui atau menolak permintaan.
3. Batal hanya dari DIAJUKAN (oleh toko). Tolak dari DIAJUKAN atau DISETUJUI.
4. Setiap perubahan status hanya berhasil kalau statusnya masih sesuai
   (mencegah klik dua kali atau dua orang memproses bersamaan).

BENTUK DOKUMEN
{
    "nomor": "PRM-261119-0001",
    "toko_id": ObjectId, "toko": "Toko Salatiga 01",
    "status": "DIAJUKAN",
    "catatan": "Stok akhir pekan",
    "items": [{"produk_id": ObjectId, "kode": "P-0001", "nama": "Minyak Goreng 1L",
               "satuan": "PCS", "qty_diminta": 30, "qty_disetujui": None, "qty_dikirim": None}],
    "alasan_tolak": None,
    "diajukan_oleh": {"id": ObjectId, "nama": "Kepala Toko Salatiga 01"},
    "dibuat": datetime, "diperbarui": datetime,
    "riwayat": [{"status": "DIAJUKAN", "waktu": datetime, "oleh": "...", "catatan": ""}]
}
"""
from app.db import get_db
from app.models import notifikasi
from app.models import stok as model_stok
from app.models.user import KEPALA_GUDANG, STAFF_GUDANG
from app.utils.nomor import buat_nomor
from app.utils.validasi import ValidasiError
from app.utils.waktu import sekarang

DIAJUKAN = "DIAJUKAN"
DISETUJUI = "DISETUJUI"
DIKIRIM = "DIKIRIM"
DITERIMA = "DITERIMA"
DITOLAK = "DITOLAK"
DIBATALKAN = "DIBATALKAN"
SEMUA_STATUS = [DIAJUKAN, DISETUJUI, DIKIRIM, DITERIMA, DITOLAK, DIBATALKAN]


# ---------------------------------------------------------------- membaca

def cari(permintaan_id):
    return get_db().permintaan.find_one({"_id": permintaan_id})


def daftar(toko_id=None, status=None, batas=300):
    """toko_id diisi untuk Kepala Toko (hanya tokonya sendiri)."""
    filter_ = {}
    if toko_id is not None:
        filter_["toko_id"] = toko_id
    if status:
        filter_["status"] = status
    return list(get_db().permintaan.find(filter_).sort("dibuat", -1).limit(batas))


def info_stok(permintaan):
    """Tambahkan stok fisik dan stok tersedia ke setiap item (untuk layar gudang).

    Untuk permintaan berstatus DISETUJUI, qty yang sudah dipesan untuk permintaan ini
    sendiri dihitung kembali sebagai tersedia, karena memang dipesan untuknya.
    """
    dipesan = model_stok.qty_dipesan()
    for item in permintaan["items"]:
        produk = get_db().master_produk.find_one({"_id": item["produk_id"]})
        tersedia = produk["stok"] - dipesan.get(item["produk_id"], 0)
        if permintaan["status"] == DISETUJUI:
            tersedia += item["qty_disetujui"]
        item["stok_fisik"] = produk["stok"]
        item["tersedia"] = max(tersedia, 0)
    return permintaan


# ---------------------------------------------------------------- bantuan

def link(permintaan, untuk_toko):
    halaman = "/permintaan-saya" if untuk_toko else "/permintaan"
    return halaman + "?nomor=" + permintaan["nomor"]


def ubah_status(permintaan, dari, ke, user, perubahan=None, catatan=""):
    """Ubah status HANYA jika status di database masih `dari`.

    Kalau dua orang menekan tombol bersamaan, orang kedua mendapat pesan
    karena status di database sudah berubah (matched_count = 0).
    """
    isi_baru = {"status": ke, "diperbarui": sekarang()}
    if perubahan:
        isi_baru.update(perubahan)

    hasil = get_db().permintaan.update_one(
        {"_id": permintaan["_id"], "status": dari},
        {
            "$set": isi_baru,
            "$push": {"riwayat": {"status": ke, "waktu": sekarang(), "oleh": user["nama"], "catatan": catatan}},
        },
    )
    if hasil.matched_count == 0:
        raise ValidasiError("Status permintaan sudah berubah. Muat ulang halaman.")


def cek_status(permintaan, *status_boleh):
    if permintaan["status"] not in status_boleh:
        raise ValidasiError("Aksi ini tidak bisa dilakukan untuk permintaan berstatus " + permintaan["status"] + ".")


def cek_qty_disetujui(permintaan, qty_baru):
    """qty_baru: {produk_id: qty}. Memeriksa aturan bisnis nomor 1."""
    produk_permintaan = {item["produk_id"] for item in permintaan["items"]}
    if set(qty_baru) != produk_permintaan:
        raise ValidasiError("Qty disetujui harus diisi untuk setiap produk di permintaan ini.")

    info_stok(permintaan)
    for item in permintaan["items"]:
        qty = qty_baru[item["produk_id"]]
        if qty > item["qty_diminta"]:
            raise ValidasiError(f"{item['nama']}: qty disetujui melebihi qty diminta ({item['qty_diminta']}).")
        if qty > item["tersedia"]:
            raise ValidasiError(f"{item['nama']}: stok tersedia hanya {item['tersedia']}.")

    if sum(qty_baru.values()) == 0:
        raise ValidasiError("Semua qty disetujui 0. Gunakan Tolak jika permintaan tidak bisa dipenuhi.")


def ringkasan_qty(permintaan):
    """Contoh: "55 dari 60 qty" untuk pesan notifikasi."""
    diminta = sum(i["qty_diminta"] for i in permintaan["items"])
    disetujui = sum(i["qty_disetujui"] or 0 for i in permintaan["items"])
    return disetujui, diminta


# ---------------------------------------------------------------- aksi

def ajukan(toko_id, catatan, items, user):
    """Kepala Toko mengajukan permintaan. items: [{"produk_id", "qty"}] (sudah divalidasi)."""
    db = get_db()
    toko = db.master_toko.find_one({"_id": toko_id})
    if toko is None or not toko["aktif"]:
        raise ValidasiError("Toko Anda sedang nonaktif. Hubungi Admin.")

    isi_items = []
    for item in items:
        produk = db.master_produk.find_one({"_id": item["produk_id"]})
        if produk is None or not produk["aktif"]:
            raise ValidasiError("Ada produk yang tidak ditemukan atau sudah nonaktif.")
        isi_items.append({
            "produk_id": produk["_id"], "kode": produk["kode"], "nama": produk["nama"],
            "satuan": produk["satuan"], "qty_diminta": item["qty"],
            "qty_disetujui": None, "qty_dikirim": None,
        })

    waktu = sekarang()
    permintaan = {
        "nomor": buat_nomor("permintaan", "PRM"),
        "toko_id": toko["_id"],
        "toko": toko["nama"],
        "status": DIAJUKAN,
        "catatan": catatan,
        "items": isi_items,
        "alasan_tolak": None,
        "diajukan_oleh": {"id": user["_id"], "nama": user["nama"]},
        "dibuat": waktu,
        "diperbarui": waktu,
        "riwayat": [{"status": DIAJUKAN, "waktu": waktu, "oleh": user["nama"], "catatan": catatan}],
    }
    db.permintaan.insert_one(permintaan)

    notifikasi.kirim_ke_role(
        KEPALA_GUDANG, f"Permintaan baru {permintaan['nomor']}",
        f"{toko['nama']} meminta {len(isi_items)} produk.", link(permintaan, False),
    )
    return permintaan["nomor"]


def batalkan(permintaan, user):
    """Kepala Toko membatalkan permintaannya sendiri (hanya dari DIAJUKAN)."""
    cek_status(permintaan, DIAJUKAN)
    ubah_status(permintaan, DIAJUKAN, DIBATALKAN, user)
    notifikasi.kirim_ke_role(
        KEPALA_GUDANG, f"{permintaan['nomor']} dibatalkan",
        f"{permintaan['toko']} membatalkan permintaannya.", link(permintaan, False),
    )


def setujui(permintaan, qty_baru, user):
    """Kepala Gudang menyetujui. qty_baru: {produk_id: qty}."""
    cek_status(permintaan, DIAJUKAN)
    cek_qty_disetujui(permintaan, qty_baru)

    items = [{**simpan_item(i), "qty_disetujui": qty_baru[i["produk_id"]]} for i in permintaan["items"]]
    ubah_status(permintaan, DIAJUKAN, DISETUJUI, user, {"items": items})

    permintaan["items"] = items
    disetujui, diminta = ringkasan_qty(permintaan)
    pesan = "Semua qty disetujui." if disetujui == diminta else f"Qty disesuaikan: {disetujui} dari {diminta} yang diminta."
    notifikasi.kirim_ke_toko(permintaan["toko_id"], f"{permintaan['nomor']} disetujui", pesan, link(permintaan, True))
    notifikasi.kirim_ke_role(
        STAFF_GUDANG, f"{permintaan['nomor']} siap dikirim",
        f"Disetujui untuk {permintaan['toko']}.", link(permintaan, False),
    )


def ubah_qty(permintaan, qty_baru, user):
    """Kepala Gudang mengubah qty disetujui selama status masih DISETUJUI."""
    cek_status(permintaan, DISETUJUI)
    cek_qty_disetujui(permintaan, qty_baru)

    items = [{**simpan_item(i), "qty_disetujui": qty_baru[i["produk_id"]]} for i in permintaan["items"]]
    ubah_status(permintaan, DISETUJUI, DISETUJUI, user, {"items": items}, catatan="Qty disetujui diubah")

    permintaan["items"] = items
    disetujui, diminta = ringkasan_qty(permintaan)
    notifikasi.kirim_ke_toko(
        permintaan["toko_id"], f"Qty {permintaan['nomor']} diubah",
        f"Qty disetujui sekarang {disetujui} dari {diminta} yang diminta.", link(permintaan, True),
    )


def tolak(permintaan, alasan, user):
    """Kepala Gudang menolak dari DIAJUKAN atau DISETUJUI, wajib dengan alasan."""
    cek_status(permintaan, DIAJUKAN, DISETUJUI)
    ubah_status(permintaan, permintaan["status"], DITOLAK, user, {"alasan_tolak": alasan}, catatan=alasan)
    # Stok yang dipesan otomatis kembali tersedia, karena qty_dipesan()
    # hanya menghitung permintaan berstatus DISETUJUI.
    notifikasi.kirim_ke_toko(
        permintaan["toko_id"], f"{permintaan['nomor']} ditolak", "Alasan: " + alasan, link(permintaan, True),
    )


def kirim(permintaan, user):
    """Staff Gudang mengirim. Tidak ada pengiriman sebagian (aturan bisnis nomor 2)."""
    cek_status(permintaan, DISETUJUI)

    # 1. Periksa stok fisik SEMUA produk dulu.
    kurang = []
    for item in permintaan["items"]:
        produk = get_db().master_produk.find_one({"_id": item["produk_id"]})
        if item["qty_disetujui"] > produk["stok"]:
            kurang.append(f"{item['nama']} (perlu {item['qty_disetujui']}, stok fisik {produk['stok']})")
    if kurang:
        raise ValidasiError(
            "Stok fisik tidak cukup untuk: " + ", ".join(kurang) + ". "
            "Kepala Gudang perlu mengubah qty disetujui atau menolak permintaan ini."
        )

    # 2. Ubah status dulu (mencegah pengiriman ganda), qty dikirim = qty disetujui.
    items = [{**simpan_item(i), "qty_dikirim": i["qty_disetujui"]} for i in permintaan["items"]]
    ubah_status(permintaan, DISETUJUI, DIKIRIM, user, {"items": items})

    # 3. Kurangi stok fisik, tercatat sebagai mutasi KELUAR.
    for item in items:
        if item["qty_dikirim"] > 0:
            model_stok.kurangi_stok(
                item["produk_id"], item["qty_dikirim"], permintaan["nomor"],
                "Dikirim ke " + permintaan["toko"], user,
            )

    notifikasi.kirim_ke_toko(
        permintaan["toko_id"], f"{permintaan['nomor']} sudah dikirim",
        "Barang dalam perjalanan. Konfirmasi setelah barang diterima.", link(permintaan, True),
    )


def terima(permintaan, user):
    """Kepala Toko mengonfirmasi barang sudah diterima."""
    cek_status(permintaan, DIKIRIM)
    ubah_status(permintaan, DIKIRIM, DITERIMA, user)


def simpan_item(item):
    """Item tanpa field tambahan dari info_stok() (stok_fisik, tersedia)."""
    return {k: v for k, v in item.items() if k not in ("stok_fisik", "tersedia")}


def pilihan_produk():
    """Produk aktif untuk form pengajuan Kepala Toko (tanpa angka stok gudang)."""
    return [{"id": str(p["_id"]), "value": p["kode"] + " · " + p["nama"], "satuan": p["satuan"]}
            for p in get_db().master_produk.find({"aktif": True}).sort("kode", 1)]
