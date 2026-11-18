"""Pembuatan aplikasi Flask Stokara."""
from flask import Flask, jsonify

from config import Config
from app.db import init_db
from app.utils.tampilan import halaman_error
from app.utils.validasi import ValidasiError


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY belum diisi di file .env")
    if not app.config["TESTING"] and not app.config["MONGO_URI"]:
        raise RuntimeError("MONGO_URI belum diisi di file .env")

    init_db(app)

    # Daftarkan kumpulan route (blueprint). Setiap fitur punya file sendiri.
    from app.routes.umum import bp as umum_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.toko import bp as toko_bp
    from app.routes.supplier import bp as supplier_bp
    from app.routes.produk import bp as produk_bp
    from app.routes.karyawan import bp as karyawan_bp
    from app.routes.stok import bp as stok_bp
    from app.routes.barang_masuk import bp as barang_masuk_bp
    from app.routes.permintaan import bp as permintaan_bp
    from app.routes.notifikasi import bp as notifikasi_bp
    app.register_blueprint(umum_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(toko_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(produk_bp)
    app.register_blueprint(karyawan_bp)
    app.register_blueprint(stok_bp)
    app.register_blueprint(barang_masuk_bp)
    app.register_blueprint(permintaan_bp)
    app.register_blueprint(notifikasi_bp)

    # Semua ValidasiError di route mana pun diubah menjadi respon 400.
    @app.errorhandler(ValidasiError)
    def validasi_gagal(error):
        return jsonify(pesan=error.pesan), 400

    # Halaman error yang rapi (API tetap mendapat JSON).
    @app.errorhandler(403)
    def dilarang(error):
        return halaman_error(403, "Akses ditolak", "Anda tidak punya akses ke fitur ini.")

    @app.errorhandler(404)
    def tidak_ditemukan(error):
        return halaman_error(404, "Halaman tidak ditemukan", "Alamat yang Anda buka tidak ada atau sudah dipindah.")

    @app.errorhandler(405)
    def metode_salah(error):
        return halaman_error(405, "Metode tidak diizinkan", "Permintaan ini tidak didukung.")

    @app.errorhandler(500)
    def kesalahan_server(error):
        return halaman_error(500, "Terjadi kesalahan", "Ada masalah di server. Silakan coba lagi.")

    return app
