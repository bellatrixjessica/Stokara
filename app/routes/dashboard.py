"""Dashboard insight (Kepala Gudang) dan angka di kartu beranda (semua role)."""
from flask import Blueprint, g, jsonify

from app.models import beranda, insight
from app.models.user import KEPALA_GUDANG
from app.utils.auth import wajib_login
from app.utils.tampilan import render_halaman

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@wajib_login(KEPALA_GUDANG)
def halaman():
    return render_halaman("gudang/dashboard.js", "Dashboard", "dashboard")


@bp.get("/api/dashboard")
@wajib_login(KEPALA_GUDANG)
def data_dashboard():
    return jsonify(insight.dashboard())


@bp.get("/api/beranda")
@wajib_login()
def data_beranda():
    return jsonify(beranda.ringkasan(g.user))
