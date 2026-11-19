from flask import Blueprint, abort, g, jsonify

from app.models import user as model_user
from app.models.user import ADMIN, KEPALA_TOKO, LABEL_ROLE
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import (ValidasiError, ambil_json, id_dari_url, id_pilihan, password, pilihan,
                                teks, username, ya_tidak)

bp = Blueprint("karyawan", __name__)


@bp.get("/master/karyawan")
@wajib_login(ADMIN)
def halaman():
    daftar_role = [{"id": kode, "value": label} for kode, label in LABEL_ROLE.items()]
    return render_halaman("admin/karyawan.js", "Karyawan", "karyawan", tambahan={"role": daftar_role})


@bp.get("/api/master/karyawan")
@wajib_login(ADMIN)
def daftar():
    return jsonify([ke_json(u) for u in model_user.semua_karyawan()])


def baca_role_dan_toko(data):
    role = pilihan(data, "role", "Role", list(LABEL_ROLE))
    toko_id = None
    if role == KEPALA_TOKO:
        toko_id = id_pilihan(data, "toko_id", "Toko")
    return role, toko_id


def cari_atau_404(user_id):
    user_id = id_dari_url(user_id)
    user = model_user.cari_berdasarkan_id(user_id)
    if user is None:
        abort(404)
    return user


@bp.post("/api/master/karyawan")
@wajib_login(ADMIN)
def tambah():
    data = ambil_json(["username", "nama", "role", "toko_id", "password"])
    role, toko_id = baca_role_dan_toko(data)
    model_user.buat_user(
        username=username(data),
        password=password(data),
        nama=teks(data, "nama", "Nama"),
        role=role,
        toko_id=toko_id,
    )
    return jsonify(pesan="Akun karyawan berhasil dibuat."), 201


@bp.put("/api/master/karyawan/<user_id>")
@wajib_login(ADMIN)
def ubah(user_id):
    user = cari_atau_404(user_id)
    data = ambil_json(["nama", "role", "toko_id"])
    role, toko_id = baca_role_dan_toko(data)

    if user["_id"] == g.user["_id"] and role != ADMIN:
        raise ValidasiError("Anda tidak bisa mengubah role akun Anda sendiri.")

    model_user.ubah_karyawan(user["_id"], teks(data, "nama", "Nama"), role, toko_id)
    return jsonify(pesan="Data karyawan berhasil diubah.")


@bp.post("/api/master/karyawan/<user_id>/status")
@wajib_login(ADMIN)
def ubah_status(user_id):
    user = cari_atau_404(user_id)
    aktif = ya_tidak(ambil_json(["aktif"]), "aktif", "Status")

    if user["_id"] == g.user["_id"] and not aktif:
        raise ValidasiError("Anda tidak bisa menonaktifkan akun Anda sendiri.")

    model_user.ubah_status(user["_id"], aktif)
    return jsonify(pesan="Akun diaktifkan." if aktif else "Akun dinonaktifkan. Pengguna ini tidak bisa login lagi.")


@bp.post("/api/master/karyawan/<user_id>/password")
@wajib_login(ADMIN)
def reset_password(user_id):
    user = cari_atau_404(user_id)
    model_user.ganti_password(user["_id"], password(ambil_json(["password"])))
    return jsonify(pesan="Password berhasil diganti.")
