from flask import Blueprint, g, jsonify

from app.models import barang_masuk as model_bm
from app.models.user import KEPALA_GUDANG, STAFF_GUDANG
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ambil_json, daftar_item, id_pilihan, teks

bp = Blueprint("barang_masuk", __name__)


@bp.get("/barang-masuk")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def halaman():
    boleh_catat = g.user["role"] == STAFF_GUDANG
    return render_halaman("gudang/barang_masuk.js", "Barang Masuk", "barang-masuk",
                          tambahan={"boleh_catat": boleh_catat})


@bp.get("/api/barang-masuk")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def daftar():
    return jsonify([ke_json(b) for b in model_bm.semua()])


@bp.get("/api/barang-masuk/pilihan")
@wajib_login(STAFF_GUDANG)
def pilihan():
    return jsonify(model_bm.pilihan_form())


@bp.post("/api/barang-masuk")
@wajib_login(STAFF_GUDANG)
def simpan():
    data = ambil_json(["supplier_id", "no_surat_jalan", "catatan", "items"])
    nomor = model_bm.simpan(
        supplier_id=id_pilihan(data, "supplier_id", "Supplier"),
        no_surat_jalan=teks(data, "no_surat_jalan", "Nomor surat jalan", maks=50),
        catatan=teks(data, "catatan", "Catatan", wajib=False, maks=200),
        items=daftar_item(data),
        user=g.user,
    )
    return jsonify(pesan=f"Barang masuk {nomor} tersimpan. Stok sudah bertambah.", nomor=nomor), 201
