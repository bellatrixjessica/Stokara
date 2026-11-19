import re
from datetime import datetime

from bson import ObjectId
from flask import abort, request

POLA_KODE = re.compile(r"^[A-Z0-9-]{2,20}$")
POLA_USERNAME = re.compile(r"^[a-z0-9._]{3,30}$")
POLA_TANGGAL = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidasiError(Exception):
    def __init__(self, pesan):
        super().__init__(pesan)
        self.pesan = pesan


def ambil_json(key_yang_boleh):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidasiError("Data harus dikirim dalam format JSON.")
    for key in data:
        if key not in key_yang_boleh:
            raise ValidasiError(f"Data '{key}' tidak dikenal.")
    return data


def teks(data, key, label, wajib=True, maks=100):
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
    nilai = data.get(key)
    if not isinstance(nilai, str) or len(nilai) < 8:
        raise ValidasiError("Password minimal 8 karakter.")
    if len(nilai) > 100:
        raise ValidasiError("Password maksimal 100 karakter.")
    return nilai


def angka_bulat(data, key, label, minimal=0, maksimal=1_000_000):
    nilai = data.get(key)
    if isinstance(nilai, bool) or not isinstance(nilai, int):
        raise ValidasiError(f"{label} harus berupa angka bulat.")
    if nilai < minimal or nilai > maksimal:
        raise ValidasiError(f"{label} harus antara {minimal} dan {maksimal}.")
    return nilai


def pilihan(data, key, label, daftar):
    nilai = data.get(key)
    if not isinstance(nilai, str) or nilai not in daftar:
        raise ValidasiError(f"{label} tidak valid.")
    return nilai


def ya_tidak(data, key, label):
    nilai = data.get(key)
    if not isinstance(nilai, bool):
        raise ValidasiError(f"{label} harus bernilai true atau false.")
    return nilai


def id_pilihan(data, key, label):
    nilai = data.get(key)
    if not isinstance(nilai, str) or not ObjectId.is_valid(nilai):
        raise ValidasiError(f"{label} wajib dipilih.")
    return ObjectId(nilai)


def daftar_item(data, key="items", maks=50, qty_minimal=1):
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
    nilai = data.get(key)
    if not isinstance(nilai, str) or not POLA_TANGGAL.match(nilai):
        raise ValidasiError(f"{label} wajib diisi dengan format tahun-bulan-hari.")
    try:
        return datetime.strptime(nilai, "%Y-%m-%d").date()
    except ValueError:
        raise ValidasiError(f"{label} bukan tanggal yang benar.") from None


def id_dari_url(nilai):
    if not ObjectId.is_valid(nilai):
        abort(404)
    return ObjectId(nilai)
