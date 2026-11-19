from flask import Blueprint, jsonify, redirect, render_template, session

from app.db import get_db
from app.utils.auth import wajib_login
from app.utils.tampilan import render_halaman

bp = Blueprint("umum", __name__)


@bp.get("/")
def index():
    if session.get("user_id"):
        return redirect("/beranda")
    return redirect("/login")


@bp.get("/login")
def halaman_login():
    if session.get("user_id"):
        return redirect("/beranda")
    return render_template("login.html")


@bp.get("/beranda")
@wajib_login()
def beranda():
    return render_halaman("beranda.js", "Beranda", "beranda")


@bp.get("/health")
def health():
    try:
        get_db().command("ping")
        return jsonify(status="ok", database="terhubung")
    except Exception:
        return jsonify(status="error", database="tidak terhubung"), 503
