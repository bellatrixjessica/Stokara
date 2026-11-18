"""Model stock opname: hitung fisik barang di rak (collection opname).

ALUR
  Staff Gudang menghitung  ->  MENUNGGU  --setujui (Kepala Gudang)-->  DISETUJUI  (stok dikoreksi)
                                        --tolak (Kepala Gudang, wajib alasan)-->  DITOLAK  (stok tetap)

ATURAN BISNIS
1. Saat dihitung, stok sistem dicatat dan selisihnya dihitung: selisih = hitung fisik - stok sistem.
   Stok BELUM berubah sampai Kepala Gudang menyetujui.
2. Saat disetujui, stok dikoreksi sebesar SELISIH (koreksi_stok), dan otomatis
   tercatat sebagai mutasi ADJUST. Barang yang masuk/keluar setelah dihitung tetap terhitung.
3. Satu produk tidak boleh ada di dua opname yang sama-sama MENUNGGU,
   supaya selisihnya tidak dikoreksi dua kali.

BENTUK DOKUMEN
{
    "nomor": "OPN-261119-0001",
    "status": "MENUNGGU",
    "catatan": "Rak B, 2 dus penyok dibuang",
    "items": [{"produk_id": ObjectId, "kode": "P-0001", "nama": "Minyak Goreng 1L", "satuan": "PCS",
               "stok_sistem": 50, "stok_hitung": 47, "selisih": -3}],
    "dihitung_oleh": {"id": ObjectId, "nama": "Staff Gudang Semarang"},
    "dibuat": datetime,
    "diperiksa_oleh": None, "diperiksa": None, "alasan_tolak": None
}
"""
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
    """Produk aktif beserta stok sistemnya, untuk form opname."""
    return [
        {"id": str(p["_id"]), "kode": p["kode"], "nama": p["nama"], "satuan": p["satuan"], "stok": p["stok"]}
        for p in get_db().master_produk.find({"aktif": True}).sort("kode", 1)
    ]


def buat(items, catatan, user):
    """Staff Gudang menyimpan hasil hitung. items: [{"produk_id", "qty"}], qty = hasil hitung fisik."""
    db = get_db()

    # Produk yang masih ada di opname MENUNGGU tidak boleh dihitung lagi (aturan 3)
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
    """Ubah status HANYA jika masih MENUNGGU (mencegah diproses dua kali)."""
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
    """Kepala Gudang menyetujui: stok setiap produk dikoreksi sebesar selisihnya."""
    if opname["status"] != MENUNGGU:
        raise ValidasiError("Opname ini sudah diperiksa.")

    # 1. Periksa dulu: koreksi negatif tidak boleh membuat stok minus
    for item in opname["items"]:
        if item["selisih"] < 0:
            produk = get_db().master_produk.find_one({"_id": item["produk_id"]})
            if produk["stok"] + item["selisih"] < 0:
                raise ValidasiError(
                    f"{item['nama']}: stok saat ini {produk['stok']}, tidak bisa dikurangi {-item['selisih']}. "
                    "Stok sudah berubah sejak dihitung; tolak opname ini lalu hitung ulang."
                )

    # 2. Tandai disetujui, lalu 3. koreksi stok (tercatat sebagai mutasi ADJUST)
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
