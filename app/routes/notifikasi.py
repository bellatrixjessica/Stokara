from flask import Blueprint, g, jsonify

from app.models import notifikasi as model_notifikasi
from app.utils.auth import wajib_login

bp = Blueprint("notifikasi", __name__)


@bp.get("/api/notifikasi")
@wajib_login()
def daftar():
    return jsonify(
        belum_dibaca=model_notifikasi.jumlah_belum_dibaca(g.user),
        daftar=model_notifikasi.untuk_user(g.user),
    )


@bp.post("/api/notifikasi/baca")
@wajib_login()
def tandai_dibaca():
    model_notifikasi.tandai_semua_dibaca(g.user)
    return jsonify(pesan="Semua notifikasi ditandai sudah dibaca.")
