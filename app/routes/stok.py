"""Stok gudang dan riwayat mutasi (Kepala Gudang dan Staff Gudang)."""
from flask import Blueprint, abort, jsonify, request

from app.db import get_db
from app.models import stok as model_stok
from app.models.user import KEPALA_GUDANG, STAFF_GUDANG
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import id_dari_url, teks

bp = Blueprint("stok", __name__)


@bp.get("/stok")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def halaman():
    return render_halaman("gudang/stok.js", "Stok Gudang", "stok")


@bp.get("/api/stok")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def daftar():
    # /api/stok?cari=minyak  -> hanya produk yang cocok (lihat filter_cari di model)
    cari = teks(request.args, "cari", "Kata kunci", wajib=False, maks=50)
    return jsonify(model_stok.daftar_stok(cari or None))


@bp.get("/api/stok/<produk_id>/mutasi")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def mutasi(produk_id):
    produk_id = id_dari_url(produk_id)
    if get_db().master_produk.find_one({"_id": produk_id}) is None:
        abort(404)
    return jsonify([ke_json(m) for m in model_stok.riwayat(produk_id)])
