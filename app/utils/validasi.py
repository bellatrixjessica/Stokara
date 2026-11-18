"""Validasi dan sanitasi input dari pengguna.

Prinsipnya: setiap data dari browser dianggap belum aman sampai dicek
tipenya, isinya, dan panjangnya.
"""
import re
from datetime import datetime

from bson import ObjectId
from flask import abort, request

POLA_KODE = re.compile(r"^[A-Z0-9-]{2,20}$")        # contoh: TK-01, P-0001
POLA_USERNAME = re.compile(r"^[a-z0-9._]{3,30}$")   # contoh: toko.salatiga01
POLA_TANGGAL = re.compile(r"^\d{4}-\d{2}-\d{2}$")    # contoh: 2026-11-19


class ValidasiError(Exception):
    """Dilempar saat input tidak valid.

    Ditangkap di app/__init__.py lalu dikirim ke browser sebagai respon 400
    berisi pesan, misalnya {"pesan": "Username wajib diisi."}
    """

    def __init__(self, pesan):
        super().__init__(pesan)
        self.pesan = pesan


def ambil_json(key_yang_boleh):
    """Ambil data JSON dari request dan pastikan hanya berisi key yang dikenal.

    Key lain ditolak supaya pengguna tidak bisa menyelipkan field tambahan,
    misalnya {"role": "admin"} di form yang seharusnya tidak mengubah role.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidasiError("Data harus dikirim dalam format JSON.")
    for key in data:
        if key not in key_yang_boleh:
            raise ValidasiError(f"Data '{key}' tidak dikenal.")
    return data


def teks(data, key, label, wajib=True, maks=100):
    """Ambil satu nilai teks dari data, lalu rapikan spasi di awal dan akhir.

    Harus benar-benar bertipe teks (str). Kalau pengguna mengirim objek seperti
    {"$ne": ""}, nilainya ditolak. Ini mencegah NoSQL injection.
    """
    nilai = data.get(key)
    if nilai is None:
        nilai = ""
    if not isinstance(nilai, str):
        raise ValidasiError(f"{label} harus berupa teks.")

    nilai = nilai.strip()
    if wajib and nilai == "":
        raise ValidasiError(f"{label} wajib diisi.")
    if len(nilai) > maks:
        raise ValidasiError(f"{label} maksimal {maks} karakter.")
    return nilai


def kode(data, key="kode", label="Kode"):
    """Kode data master: huruf besar, angka, dan tanda strip. Contoh: TK-01."""
    nilai = teks(data, key, label, maks=20).upper()
    if not POLA_KODE.match(nilai):
        raise ValidasiError(f"{label} hanya boleh berisi huruf, angka, dan tanda strip (2-20 karakter).")
    return nilai


def username(data, key="username"):
    nilai = teks(data, key, "Username", maks=30).lower()
    if not POLA_USERNAME.match(nilai):
        raise ValidasiError("Username hanya boleh huruf kecil, angka, titik, dan garis bawah (3-30 karakter).")
    return nilai


def password(data, key="password"):
    """Password baru: minimal 8 karakter. Spasi tidak dibuang."""
    nilai = data.get(key)
    if not isinstance(nilai, str) or len(nilai) < 8:
        raise ValidasiError("Password minimal 8 karakter.")
    if len(nilai) > 100:
        raise ValidasiError("Password maksimal 100 karakter.")
    return nilai


def angka_bulat(data, key, label, minimal=0, maksimal=1_000_000):
    """Angka bulat dalam batas tertentu. Teks seperti "5" ditolak."""
    nilai = data.get(key)
    # Di Python, True/False juga dianggap int, jadi ditolak secara khusus.
    if isinstance(nilai, bool) or not isinstance(nilai, int):
        raise ValidasiError(f"{label} harus berupa angka bulat.")
    if nilai < minimal or nilai > maksimal:
        raise ValidasiError(f"{label} harus antara {minimal} dan {maksimal}.")
    return nilai


def pilihan(data, key, label, daftar):
    """Nilai harus salah satu dari daftar, misalnya satuan PCS/PACK/KARTON."""
    nilai = data.get(key)
    if not isinstance(nilai, str) or nilai not in daftar:
        raise ValidasiError(f"{label} tidak valid.")
    return nilai


def ya_tidak(data, key, label):
    """Nilai harus true atau false."""
    nilai = data.get(key)
    if not isinstance(nilai, bool):
        raise ValidasiError(f"{label} harus bernilai true atau false.")
    return nilai


def id_pilihan(data, key, label):
    """ID data lain yang dipilih di form, misalnya supplier_id. Diubah menjadi ObjectId."""
    nilai = data.get(key)
    if not isinstance(nilai, str) or not ObjectId.is_valid(nilai):
        raise ValidasiError(f"{label} wajib dipilih.")
    return ObjectId(nilai)


def daftar_item(data, key="items", maks=50, qty_minimal=1):
    """Daftar produk + qty, contoh: [{"produk_id": "65f...", "qty": 10}, ...]

    Dipakai di barang masuk, permintaan toko, dan persetujuan (qty_minimal=0,
    karena Kepala Gudang boleh menyetujui 0 untuk produk yang stoknya habis).
    Produk yang sama tidak boleh muncul dua kali dalam satu dokumen.
    """
    items = data.get(key)
    if not isinstance(items, list) or len(items) == 0:
        raise ValidasiError("Tambahkan minimal satu produk.")
    if len(items) > maks:
        raise ValidasiError(f"Maksimal {maks} produk dalam satu dokumen.")

    hasil = []
    sudah_ada = set()
    for nomor, item in enumerate(items, start=1):
        if not isinstance(item, dict) or set(item) != {"produk_id", "qty"}:
            raise ValidasiError(f"Data produk baris {nomor} tidak valid.")
        produk_id = id_pilihan(item, "produk_id", f"Produk baris {nomor}")
        qty = angka_bulat(item, "qty", f"Qty baris {nomor}", minimal=qty_minimal, maksimal=100_000)
        if produk_id in sudah_ada:
            raise ValidasiError(f"Produk baris {nomor} sudah ada di daftar.")
        sudah_ada.add(produk_id)
        hasil.append({"produk_id": produk_id, "qty": qty})
    return hasil


def tanggal(data, key, label):
    """Tanggal dengan format tahun-bulan-hari, contoh "2026-11-19". Diubah menjadi date."""
    nilai = data.get(key)
    if not isinstance(nilai, str) or not POLA_TANGGAL.match(nilai):
        raise ValidasiError(f"{label} wajib diisi dengan format tahun-bulan-hari.")
    try:
        return datetime.strptime(nilai, "%Y-%m-%d").date()
    except ValueError:  # contoh 2026-02-31
        raise ValidasiError(f"{label} bukan tanggal yang benar.") from None


def id_dari_url(nilai):
    """ID di alamat URL, contoh /api/master/toko/<id>. ID rusak dianggap tidak ditemukan."""
    if not ObjectId.is_valid(nilai):
        abort(404)
    return ObjectId(nilai)
