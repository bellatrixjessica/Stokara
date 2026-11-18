"""Bantuan untuk menampilkan halaman: menu per role dan halaman error."""
from flask import current_app, g, jsonify, render_template, request

from app.models import user as model_user
from app.models.user import ADMIN, KEPALA_GUDANG, KEPALA_TOKO, STAFF_GUDANG

SEMUA = [ADMIN, KEPALA_GUDANG, STAFF_GUDANG, KEPALA_TOKO]

# Daftar menu. "role" = siapa saja yang melihat menu ini.
# Ikon dari Material Design Icons: https://pictogrammers.com/library/mdi/
MENU = [
    {"id": "beranda", "judul": "Beranda", "ikon": "mdi mdi-home-outline", "url": "/beranda",
     "keterangan": "Ringkasan pekerjaan Anda", "role": SEMUA},
    {"id": "dashboard", "judul": "Dashboard", "ikon": "mdi mdi-chart-box-outline", "url": "/dashboard",
     "keterangan": "Fill rate, stok kritis, dan saran restock", "role": [KEPALA_GUDANG]},
    {"id": "permintaan", "judul": "Permintaan Toko", "ikon": "mdi mdi-clipboard-check-outline", "url": "/permintaan",
     "keterangan": "Setujui, tolak, dan kirim permintaan toko", "role": [KEPALA_GUDANG, STAFF_GUDANG]},
    {"id": "permintaan-saya", "judul": "Permintaan Barang", "ikon": "mdi mdi-cart-arrow-right", "url": "/permintaan-saya",
     "keterangan": "Ajukan permintaan ke gudang dan pantau statusnya", "role": [KEPALA_TOKO]},
    {"id": "stok", "judul": "Stok Gudang", "ikon": "mdi mdi-package-variant-closed", "url": "/stok",
     "keterangan": "Stok fisik, stok tersedia, dan riwayat mutasi", "role": [KEPALA_GUDANG, STAFF_GUDANG]},
    {"id": "barang-masuk", "judul": "Barang Masuk", "ikon": "mdi mdi-truck-delivery-outline", "url": "/barang-masuk",
     "keterangan": "Catat barang yang datang dari supplier", "role": [KEPALA_GUDANG, STAFF_GUDANG]},
    {"id": "opname", "judul": "Stock Opname", "ikon": "mdi mdi-clipboard-list-outline", "url": "/opname",
     "keterangan": "Hitung fisik dan penyesuaian stok", "role": [KEPALA_GUDANG, STAFF_GUDANG]},
    {"id": "laporan", "judul": "Laporan", "ikon": "mdi mdi-file-chart-outline", "url": "/laporan",
     "keterangan": "Rekap periode, unduh Excel atau PDF", "role": [KEPALA_GUDANG, KEPALA_TOKO]},
    {"id": "produk", "judul": "Produk", "ikon": "mdi mdi-tag-outline", "url": "/master/produk",
     "keterangan": "Data produk, satuan, dan lead time", "role": [ADMIN]},
    {"id": "toko", "judul": "Toko", "ikon": "mdi mdi-storefront-outline", "url": "/master/toko",
     "keterangan": "Data toko yang dilayani gudang", "role": [ADMIN]},
    {"id": "supplier", "judul": "Supplier", "ikon": "mdi mdi-factory", "url": "/master/supplier",
     "keterangan": "Data pemasok barang", "role": [ADMIN]},
    {"id": "karyawan", "judul": "Karyawan", "ikon": "mdi mdi-account-group-outline", "url": "/master/karyawan",
     "keterangan": "Akun login dan role karyawan", "role": [ADMIN]},
]


def menu_untuk(role):
    """Ambil menu yang boleh dilihat role tertentu (tanpa kolom "role")."""
    hasil = []
    for item in MENU:
        if role in item["role"]:
            hasil.append({k: v for k, v in item.items() if k != "role"})
    return hasil


def render_halaman(js, judul, aktif, tambahan=None):
    """Tampilkan halaman setelah login.

    js       : file JavaScript Webix halaman ini, contoh "beranda.js",
               atau daftar file, contoh ["permintaan_bersama.js", "toko/permintaan.js"]
    judul    : judul di tab browser
    aktif    : id menu yang disorot di sidebar
    tambahan : data lain untuk halaman ini, contoh {"satuan": ["PCS", "KARTON"]}
    """
    data = {
        "pengguna": model_user.data_publik(g.user),
        "menu": menu_untuk(g.user["role"]),
        "aktif": aktif,
        "branch": current_app.config["NAMA_BRANCH"],
    }
    if tambahan:
        data.update(tambahan)
    if isinstance(js, str):
        js = [js]
    return render_template("halaman.html", js=js, judul=judul, data=data)


def halaman_error(kode, judul, pesan):
    """API mendapat JSON, halaman biasa mendapat halaman error yang rapi."""
    if request.path.startswith("/api/"):
        return jsonify(pesan=pesan), kode
    return render_template("error.html", kode=kode, judul=judul, pesan=pesan), kode
