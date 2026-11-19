from flask import Blueprint, abort, jsonify

from app.models import supplier as model_supplier
from app.models.user import ADMIN
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ambil_json, id_dari_url, kode, teks, ya_tidak

bp = Blueprint("supplier", __name__)


@bp.get("/master/supplier")
@wajib_login(ADMIN)
def halaman():
    return render_halaman("admin/supplier.js", "Supplier", "supplier")


@bp.get("/api/master/supplier")
@wajib_login(ADMIN)
def daftar():
    return jsonify([ke_json(s) for s in model_supplier.semua()])


@bp.post("/api/master/supplier")
@wajib_login(ADMIN)
def tambah():
    data = ambil_json(["kode", "nama", "telepon", "alamat"])
    model_supplier.tambah(
        kode=kode(data, label="Kode supplier"),
        nama=teks(data, "nama", "Nama supplier"),
        telepon=teks(data, "telepon", "Telepon", wajib=False, maks=20),
        alamat=teks(data, "alamat", "Alamat", wajib=False, maks=200),
    )
    return jsonify(pesan="Supplier berhasil ditambahkan."), 201


@bp.put("/api/master/supplier/<supplier_id>")
@wajib_login(ADMIN)
def ubah(supplier_id):
    supplier_id = id_dari_url(supplier_id)
    if model_supplier.cari(supplier_id) is None:
        abort(404)

    data = ambil_json(["nama", "telepon", "alamat"])
    model_supplier.ubah(
        supplier_id,
        nama=teks(data, "nama", "Nama supplier"),
        telepon=teks(data, "telepon", "Telepon", wajib=False, maks=20),
        alamat=teks(data, "alamat", "Alamat", wajib=False, maks=200),
    )
    return jsonify(pesan="Data supplier berhasil diubah.")


@bp.post("/api/master/supplier/<supplier_id>/status")
@wajib_login(ADMIN)
def ubah_status(supplier_id):
    supplier_id = id_dari_url(supplier_id)
    if model_supplier.cari(supplier_id) is None:
        abort(404)

    aktif = ya_tidak(ambil_json(["aktif"]), "aktif", "Status")
    model_supplier.ubah_status(supplier_id, aktif)
    return jsonify(pesan="Supplier diaktifkan." if aktif else "Supplier dinonaktifkan.")
