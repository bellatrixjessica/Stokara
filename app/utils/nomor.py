from app.db import get_db
from app.utils.waktu import sekarang_wib


def buat_nomor(collection, awalan):
    depan = awalan + "-" + sekarang_wib().strftime("%y%m%d") + "-"
    jumlah_hari_ini = get_db()[collection].count_documents({"nomor": {"$regex": "^" + depan}})
    return depan + str(jumlah_hari_ini + 1).zfill(4)
