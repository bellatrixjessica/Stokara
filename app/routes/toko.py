from flask import Blueprint, abort, jsonify

from app.models import toko as model_toko
from app.models.user import ADMIN
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ambil_json, id_dari_url, kode, teks, ya_tidak

bp = Blueprint("toko", __name__)


@bp.get("/master/toko")
@wajib_login(ADMIN)
def halaman():
    return render_halaman("admin/toko.js", "Toko", "toko")


@bp.get("/api/master/toko")
@wajib_login(ADMIN)
def daftar():
    return jsonify([ke_json(t) for t in model_toko.semua()])


@bp.post("/api/master/toko")
@wajib_login(ADMIN)
def tambah():
    data = ambil_json(["kode", "nama", "alamat"])
    model_toko.tambah(
        kode=kode(data, label="Kode toko"),
        nama=teks(data, "nama", "Nama toko"),
        alamat=teks(data, "alamat", "Alamat", maks=200),
    )
    return jsonify(pesan="Toko berhasil ditambahkan."), 201


@bp.put("/api/master/toko/<toko_id>")
@wajib_login(ADMIN)
def ubah(toko_id):
    toko_id = id_dari_url(toko_id)
    if model_toko.cari(toko_id) is None:
        abort(404)

    data = ambil_json(["nama", "alamat"])
    model_toko.ubah(
        toko_id,
        nama=teks(data, "nama", "Nama toko"),
        alamat=teks(data, "alamat", "Alamat", maks=200),
    )
    return jsonify(pesan="Data toko berhasil diubah.")


@bp.post("/api/master/toko/<toko_id>/status")
@wajib_login(ADMIN)
def ubah_status(toko_id):
    toko_id = id_dari_url(toko_id)
    if model_toko.cari(toko_id) is None:
        abort(404)

    aktif = ya_tidak(ambil_json(["aktif"]), "aktif", "Status")
    model_toko.ubah_status(toko_id, aktif)
    return jsonify(pesan="Toko diaktifkan." if aktif else "Toko dinonaktifkan.")
