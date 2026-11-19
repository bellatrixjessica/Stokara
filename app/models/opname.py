from app.db import get_db
from app.models import notifikasi
from app.models import stok as model_stok
from app.models.user import KEPALA_GUDANG, STAFF_GUDANG
from app.utils.nomor import buat_nomor
from app.utils.validasi import ValidasiError
from app.utils.waktu import sekarang

MENUNGGU = "MENUNGGU"
DISETUJUI = "DISETUJUI"
DITOLAK = "DITOLAK"


def cari(opname_id):
    return get_db().opname.find_one({"_id": opname_id})


def daftar(batas=200):
    return list(get_db().opname.find().sort("dibuat", -1).limit(batas))


def produk_untuk_dihitung():
    return [
        {"id": str(p["_id"]), "kode": p["kode"], "nama": p["nama"], "satuan": p["satuan"], "stok": p["stok"]}
        for p in get_db().master_produk.find({"aktif": True}).sort("kode", 1)
    ]


def buat(items, catatan, user):
    db = get_db()

    sedang_diperiksa = set()
    for o in db.opname.find({"status": MENUNGGU}):
        for item in o["items"]:
            sedang_diperiksa.add(item["produk_id"])

    isi_items = []
    for item in items:
        produk = db.master_produk.find_one({"_id": item["produk_id"]})
        if produk is None or not produk["aktif"]:
            raise ValidasiError("Ada produk yang tidak ditemukan atau sudah nonaktif.")
        if produk["_id"] in sedang_diperiksa:
            raise ValidasiError(f"{produk['nama']} masih ada di opname lain yang menunggu pemeriksaan.")
        isi_items.append({
            "produk_id": produk["_id"], "kode": produk["kode"], "nama": produk["nama"], "satuan": produk["satuan"],
            "stok_sistem": produk["stok"],
            "stok_hitung": item["qty"],
            "selisih": item["qty"] - produk["stok"],
        })

    opname = {
        "nomor": buat_nomor("opname", "OPN"),
        "status": MENUNGGU,
        "catatan": catatan,
        "items": isi_items,
        "dihitung_oleh": {"id": user["_id"], "nama": user["nama"]},
        "dibuat": sekarang(),
        "diperiksa_oleh": None,
        "diperiksa": None,
        "alasan_tolak": None,
    }
    db.opname.insert_one(opname)

    jumlah_selisih = sum(1 for i in isi_items if i["selisih"] != 0)
    notifikasi.kirim_ke_role(
        KEPALA_GUDANG, f"Opname {opname['nomor']} menunggu pemeriksaan",
        f"{len(isi_items)} produk dihitung, {jumlah_selisih} ada selisih.", "/opname?nomor=" + opname["nomor"],
    )
    return opname["nomor"]


def tandai_diperiksa(opname, status_baru, user, alasan=None):
    hasil = get_db().opname.update_one(
        {"_id": opname["_id"], "status": MENUNGGU},
        {"$set": {
            "status": status_baru,
            "diperiksa_oleh": {"id": user["_id"], "nama": user["nama"]},
            "diperiksa": sekarang(),
            "alasan_tolak": alasan,
        }},
    )
    if hasil.matched_count == 0:
        raise ValidasiError("Opname ini sudah diperiksa. Muat ulang halaman.")


def setujui(opname, user):
    if opname["status"] != MENUNGGU:
        raise ValidasiError("Opname ini sudah diperiksa.")

    for item in opname["items"]:
        if item["selisih"] < 0:
            produk = get_db().master_produk.find_one({"_id": item["produk_id"]})
            if produk["stok"] + item["selisih"] < 0:
                raise ValidasiError(
                    f"{item['nama']}: stok saat ini {produk['stok']}, tidak bisa dikurangi {-item['selisih']}. "
                    "Stok sudah berubah sejak dihitung; tolak opname ini lalu hitung ulang."
                )

    tandai_diperiksa(opname, DISETUJUI, user)
    for item in opname["items"]:
        if item["selisih"] != 0:
            model_stok.koreksi_stok(
                item["produk_id"], item["selisih"], opname["nomor"], "Stock opname " + opname["nomor"], user
            )

    notifikasi.kirim_ke_role(
        STAFF_GUDANG, f"Opname {opname['nomor']} disetujui", "Stok sudah dikoreksi sesuai hasil hitung.",
        "/opname?nomor=" + opname["nomor"],
    )


def tolak(opname, alasan, user):
    if opname["status"] != MENUNGGU:
        raise ValidasiError("Opname ini sudah diperiksa.")
    tandai_diperiksa(opname, DITOLAK, user, alasan)
    notifikasi.kirim_ke_role(
        STAFF_GUDANG, f"Opname {opname['nomor']} ditolak", "Alasan: " + alasan, "/opname?nomor=" + opname["nomor"],
    )
