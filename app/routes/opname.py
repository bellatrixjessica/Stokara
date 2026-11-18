"""Stock opname.

- Staff Gudang  : mencatat hasil hitung fisik
- Kepala Gudang : menyetujui (stok dikoreksi) atau menolak
"""
from flask import Blueprint, abort, g, jsonify

from app.models import opname as model
from app.models.user import KEPALA_GUDANG, STAFF_GUDANG
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ambil_json, daftar_item, id_dari_url, teks

bp = Blueprint("opname", __name__)


def ambil_opname(opname_id):
    opname = model.cari(id_dari_url(opname_id))
    if opname is None:
        abort(404)
    return opname


@bp.get("/opname")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def halaman():
    return render_halaman("gudang/opname.js", "Stock Opname", "opname")


@bp.get("/api/opname")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def daftar():
    return jsonify([ke_json(o) for o in model.daftar()])


@bp.get("/api/opname/produk")
@wajib_login(STAFF_GUDANG)
def produk_untuk_dihitung():
    return jsonify(model.produk_untuk_dihitung())


@bp.post("/api/opname")
@wajib_login(STAFF_GUDANG)
def buat():
    data = ambil_json(["catatan", "items"])
    nomor = model.buat(
        items=daftar_item(data, maks=200, qty_minimal=0),  # qty = hasil hitung, boleh 0 (habis)
        catatan=teks(data, "catatan", "Catatan", wajib=False, maks=200),
        user=g.user,
    )
    return jsonify(pesan=f"Opname {nomor} tersimpan dan menunggu pemeriksaan Kepala Gudang.", nomor=nomor), 201


@bp.post("/api/opname/<opname_id>/setujui")
@wajib_login(KEPALA_GUDANG)
def setujui(opname_id):
    opname = ambil_opname(opname_id)
    model.setujui(opname, g.user)
    return jsonify(pesan=f"Opname {opname['nomor']} disetujui. Stok sudah dikoreksi.")


@bp.post("/api/opname/<opname_id>/tolak")
@wajib_login(KEPALA_GUDANG)
def tolak(opname_id):
    opname = ambil_opname(opname_id)
    alasan = teks(ambil_json(["alasan"]), "alasan", "Alasan penolakan", maks=200)
    model.tolak(opname, alasan, g.user)
    return jsonify(pesan=f"Opname {opname['nomor']} ditolak.")
