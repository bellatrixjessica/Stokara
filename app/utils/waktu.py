"""Waktu di Stokara.

Waktu SIMPAN di database selalu UTC (standar internasional).
Waktu TAMPIL ke pengguna selalu WIB (UTC+7), diubah oleh browser.
"""
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7), "WIB")


def sekarang():
    """Waktu saat ini dalam UTC, untuk disimpan ke database."""
    return datetime.now(timezone.utc)


def sekarang_wib():
    """Waktu saat ini di Semarang (WIB), misalnya untuk tanggal di nomor dokumen."""
    return datetime.now(WIB)
