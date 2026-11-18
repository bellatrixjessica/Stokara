"""Master Produk (khusus Admin)."""
from flask import Blueprint, abort, jsonify

from app.models import produk as model_produk
from app.models.produk import SATUAN
from app.models.user import ADMIN
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import (ambil_json, angka_bulat, id_dari_url, id_pilihan, kode, pilihan, teks,
                                ya_tidak)

bp = Blueprint("produk", __name__)

KOLOM_FORM = ["nama", "kategori", "satuan", "supplier_id", "lead_time_hari"]


@bp.get("/master/produk")
@wajib_login(ADMIN)
def halaman():
    return render_halaman("admin/produk.js", "Produk", "produk", tambahan={"satuan": SATUAN})


@bp.get("/api/master/produk")
@wajib_login(ADMIN)
def daftar():
    return jsonify([ke_json(p) for p in model_produk.semua()])


def baca_form(data):
    """Validasi isian form produk (dipakai saat tambah dan ubah)."""
    return {
        "nama": teks(data, "nama", "Nama produk"),
        "kategori": teks(data, "kategori", "Kategori", maks=50),
        "satuan": pilihan(data, "satuan", "Satuan", SATUAN),
        "supplier_id": id_pilihan(data, "supplier_id", "Supplier"),
        "lead_time_hari": angka_bulat(data, "lead_time_hari", "Lead time", minimal=1, maksimal=60),
    }


@bp.post("/api/master/produk")
@wajib_login(ADMIN)
def tambah():
    data = ambil_json(["kode"] + KOLOM_FORM)
    model_produk.tambah(kode=kode(data, label="Kode produk"), **baca_form(data))
    return jsonify(pesan="Produk berhasil ditambahkan."), 201


@bp.put("/api/master/produk/<produk_id>")
@wajib_login(ADMIN)
def ubah(produk_id):
    produk_id = id_dari_url(produk_id)
    if model_produk.cari(produk_id) is None:
        abort(404)

    data = ambil_json(KOLOM_FORM)  # kode dan stok tidak bisa diubah dari sini
    model_produk.ubah(produk_id, **baca_form(data))
    return jsonify(pesan="Data produk berhasil diubah.")


@bp.post("/api/master/produk/<produk_id>/status")
@wajib_login(ADMIN)
def ubah_status(produk_id):
    produk_id = id_dari_url(produk_id)
    if model_produk.cari(produk_id) is None:
        abort(404)

    aktif = ya_tidak(ambil_json(["aktif"]), "aktif", "Status")
    model_produk.ubah_status(produk_id, aktif)
    return jsonify(pesan="Produk diaktifkan." if aktif else "Produk dinonaktifkan.")
