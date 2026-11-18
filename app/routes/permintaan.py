"""Permintaan barang dari toko.

- Kepala Toko   : ajukan, batalkan, konfirmasi diterima (hanya permintaan tokonya)
- Kepala Gudang : setujui, ubah qty disetujui, tolak
- Staff Gudang  : kirim
"""
from flask import Blueprint, abort, g, jsonify, request

from app.models import permintaan as model
from app.models.user import KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG
from app.utils.auth import wajib_login
from app.utils.data import ke_json
from app.utils.tampilan import render_halaman
from app.utils.validasi import ValidasiError, ambil_json, daftar_item, id_dari_url, teks

bp = Blueprint("permintaan", __name__)

SEMUA_ROLE_PERMINTAAN = (KEPALA_GUDANG, STAFF_GUDANG, KEPALA_TOKO)


# ---------------------------------------------------------------- halaman

@bp.get("/permintaan")
@wajib_login(KEPALA_GUDANG, STAFF_GUDANG)
def halaman_gudang():
    return render_halaman(["permintaan_bersama.js", "gudang/permintaan.js"], "Permintaan Toko", "permintaan")


@bp.get("/permintaan-saya")
@wajib_login(KEPALA_TOKO)
def halaman_toko():
    return render_halaman(["permintaan_bersama.js", "toko/permintaan.js"], "Permintaan Barang", "permintaan-saya")


# ---------------------------------------------------------------- bantuan

def ambil_permintaan(permintaan_id):
    """Cari permintaan. Kepala Toko hanya boleh membuka permintaan tokonya sendiri."""
    permintaan = model.cari(id_dari_url(permintaan_id))
    if permintaan is None:
        abort(404)
    if g.user["role"] == KEPALA_TOKO and permintaan["toko_id"] != g.user["toko_id"]:
        abort(404)  # 404, bukan 403, supaya toko lain tidak tahu permintaan itu ada
    return permintaan


def baca_qty_disetujui():
    """Isi: {"items": [{"produk_id": "...", "qty": 30}, ...]} -> {ObjectId: 30, ...}"""
    items = daftar_item(ambil_json(["items"]), qty_minimal=0)
    return {item["produk_id"]: item["qty"] for item in items}


# ---------------------------------------------------------------- membaca

@bp.get("/api/permintaan")
@wajib_login(*SEMUA_ROLE_PERMINTAAN)
def daftar():
    status = request.args.get("status") or None
    if status is not None and status not in model.SEMUA_STATUS:
        raise ValidasiError("Status tidak dikenal.")

    toko_id = g.user["toko_id"] if g.user["role"] == KEPALA_TOKO else None
    return jsonify([ke_json(p) for p in model.daftar(toko_id=toko_id, status=status)])


@bp.get("/api/permintaan/<permintaan_id>")
@wajib_login(*SEMUA_ROLE_PERMINTAAN)
def detail(permintaan_id):
    permintaan = ambil_permintaan(permintaan_id)
    if g.user["role"] != KEPALA_TOKO:
        model.info_stok(permintaan)  # angka stok gudang hanya untuk layar gudang
    return jsonify(ke_json(permintaan))


@bp.get("/api/permintaan/pilihan-produk")
@wajib_login(KEPALA_TOKO)
def pilihan_produk():
    return jsonify(model.pilihan_produk())


# ---------------------------------------------------------------- aksi Kepala Toko

@bp.post("/api/permintaan")
@wajib_login(KEPALA_TOKO)
def ajukan():
    data = ambil_json(["catatan", "items"])
    nomor = model.ajukan(
        toko_id=g.user["toko_id"],
        catatan=teks(data, "catatan", "Catatan", wajib=False, maks=200),
        items=daftar_item(data),
        user=g.user,
    )
    return jsonify(pesan=f"Permintaan {nomor} berhasil diajukan.", nomor=nomor), 201


@bp.post("/api/permintaan/<permintaan_id>/batal")
@wajib_login(KEPALA_TOKO)
def batalkan(permintaan_id):
    model.batalkan(ambil_permintaan(permintaan_id), g.user)
    return jsonify(pesan="Permintaan dibatalkan.")


@bp.post("/api/permintaan/<permintaan_id>/terima")
@wajib_login(KEPALA_TOKO)
def terima(permintaan_id):
    model.terima(ambil_permintaan(permintaan_id), g.user)
    return jsonify(pesan="Terima kasih. Barang sudah dikonfirmasi diterima.")


# ---------------------------------------------------------------- aksi Kepala Gudang

@bp.post("/api/permintaan/<permintaan_id>/setujui")
@wajib_login(KEPALA_GUDANG)
def setujui(permintaan_id):
    permintaan = ambil_permintaan(permintaan_id)
    model.setujui(permintaan, baca_qty_disetujui(), g.user)
    return jsonify(pesan=f"Permintaan {permintaan['nomor']} disetujui.")


@bp.post("/api/permintaan/<permintaan_id>/ubah-qty")
@wajib_login(KEPALA_GUDANG)
def ubah_qty(permintaan_id):
    permintaan = ambil_permintaan(permintaan_id)
    model.ubah_qty(permintaan, baca_qty_disetujui(), g.user)
    return jsonify(pesan="Qty disetujui berhasil diubah.")


@bp.post("/api/permintaan/<permintaan_id>/tolak")
@wajib_login(KEPALA_GUDANG)
def tolak(permintaan_id):
    permintaan = ambil_permintaan(permintaan_id)
    alasan = teks(ambil_json(["alasan"]), "alasan", "Alasan penolakan", maks=200)
    model.tolak(permintaan, alasan, g.user)
    return jsonify(pesan=f"Permintaan {permintaan['nomor']} ditolak.")


# ---------------------------------------------------------------- aksi Staff Gudang

@bp.post("/api/permintaan/<permintaan_id>/kirim")
@wajib_login(STAFF_GUDANG)
def kirim(permintaan_id):
    permintaan = ambil_permintaan(permintaan_id)
    model.kirim(permintaan, g.user)
    return jsonify(pesan=f"Permintaan {permintaan['nomor']} dikirim. Stok sudah dikurangi.")
