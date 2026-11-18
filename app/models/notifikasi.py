"""Model notifikasi di dalam aplikasi (collection notifikasi).

Notifikasi dikirim ke:
- satu ROLE, contoh semua Kepala Gudang  -> {"untuk_role": "kepala_gudang"}
- satu TOKO, yaitu Kepala Toko toko itu -> {"untuk_toko_id": ObjectId}

{
    "untuk_role": "kepala_gudang", "untuk_toko_id": None,
    "judul": "Permintaan baru PRM-261119-0001",
    "pesan": "Toko Salatiga 01 meminta 3 produk.",
    "link": "/permintaan?nomor=PRM-261119-0001",
    "dibaca_oleh": [ObjectId, ...],   <- id user yang sudah membaca
    "waktu": datetime
}
"""
from app.db import get_db
from app.utils.waktu import sekarang


def simpan(untuk_role, untuk_toko_id, judul, pesan, link):
    get_db().notifikasi.insert_one({
        "untuk_role": untuk_role,
        "untuk_toko_id": untuk_toko_id,
        "judul": judul,
        "pesan": pesan,
        "link": link,
        "dibaca_oleh": [],
        "waktu": sekarang(),
    })


def kirim_ke_role(role, judul, pesan, link):
    simpan(role, None, judul, pesan, link)


def kirim_ke_toko(toko_id, judul, pesan, link):
    simpan(None, toko_id, judul, pesan, link)


def filter_untuk(user):
    """Notifikasi mana yang menjadi milik user ini."""
    if user["toko_id"]:
        return {"untuk_toko_id": user["toko_id"]}
    return {"untuk_role": user["role"]}


def untuk_user(user, batas=20):
    hasil = []
    for n in get_db().notifikasi.find(filter_untuk(user)).sort("waktu", -1).limit(batas):
        hasil.append({
            "id": str(n["_id"]),
            "judul": n["judul"],
            "pesan": n["pesan"],
            "link": n["link"],
            "waktu": n["waktu"].isoformat(),
            "dibaca": user["_id"] in n["dibaca_oleh"],
        })
    return hasil


def jumlah_belum_dibaca(user):
    filter_ = filter_untuk(user)
    filter_["dibaca_oleh"] = {"$ne": user["_id"]}
    return get_db().notifikasi.count_documents(filter_)


def tandai_semua_dibaca(user):
    # $addToSet: tambahkan id user ke daftar, tapi tidak dobel kalau sudah ada.
    get_db().notifikasi.update_many(filter_untuk(user), {"$addToSet": {"dibaca_oleh": user["_id"]}})
