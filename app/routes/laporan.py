from bson import ObjectId
from flask import Blueprint, abort, g, jsonify, request

from app.db import get_db
from app.models import laporan as model
from app.models.user import KEPALA_GUDANG, KEPALA_TOKO
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ValidasiError, tanggal

bp = Blueprint("laporan", __name__)


@bp.get("/laporan")
@wajib_login(KEPALA_GUDANG, KEPALA_TOKO)
def halaman():
    if g.user["role"] == KEPALA_GUDANG:
        toko = [{"id": str(t["_id"]), "value": t["nama"]}
                for t in get_db().master_toko.find().sort("nama", 1)]
        tambahan = {"jenis_laporan": list(model.JUDUL), "toko": toko}
    else:
        tambahan = {"jenis_laporan": ["permintaan"], "toko": None}
    return render_halaman(["permintaan_bersama.js", "laporan.js"], "Laporan", "laporan", tambahan)


@bp.get("/api/laporan/<jenis>")
@wajib_login(KEPALA_GUDANG, KEPALA_TOKO)
def data(jenis):
    if jenis not in model.JUDUL:
        abort(404)

    if g.user["role"] == KEPALA_TOKO:
        if jenis != "permintaan":
            abort(403)
        toko_id = g.user["toko_id"]
    else:
        toko_id = None
        toko = request.args.get("toko", "")
        if toko:
            if not ObjectId.is_valid(toko):
                raise ValidasiError("Toko tidak valid.")
            toko_id = ObjectId(toko)

    dari = sampai = None
    if jenis != "restock":
        dari = tanggal(request.args, "dari", "Tanggal awal")
        sampai = tanggal(request.args, "sampai", "Tanggal akhir")

    hasil = model.buat(jenis, dari, sampai, toko_id)
    hasil["baris"] = [ke_json(b) for b in hasil["baris"]]
    return jsonify(hasil)
