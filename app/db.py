"""Koneksi ke database MongoDB."""
from flask import current_app
from pymongo import MongoClient


def init_db(app):
    """Membuka koneksi database satu kali saat aplikasi dibuat.

    tz_aware=True: waktu dari database dibaca lengkap dengan zona waktunya (UTC),
    sehingga browser bisa mengubahnya ke WIB dengan benar.
    """
    if app.config["TESTING"]:
        # Saat testing, pakai MongoDB palsu di memori (tidak menyentuh Atlas).
        import mongomock
        client = mongomock.MongoClient(tz_aware=True)
        app.db = client["stokara_test"]
    else:
        client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000, tz_aware=True)
        # Nama database diambil dari akhir MONGO_URI, yaitu .../stokara
        app.db = client.get_default_database()


def get_db():
    """Dipanggil di route untuk mengambil database, contoh: get_db().master_produk"""
    return current_app.db
