from flask import Blueprint, g, jsonify, session

from app.models import user as model_user
from app.utils.auth import wajib_login
from app.utils.validasi import ValidasiError, ambil_json, teks

bp = Blueprint("auth", __name__)


@bp.post("/api/login")
def login():
    data = ambil_json(["username", "password"])
    username = teks(data, "username", "Username", maks=50).lower()

    password = data.get("password")
    if not isinstance(password, str) or password == "":
        raise ValidasiError("Password wajib diisi.")

    user = model_user.cek_login(username, password)
    if user is None:
        return jsonify(pesan="Username atau password salah."), 401

    session.clear()
    session["user_id"] = str(user["_id"])
    session.permanent = True
    return jsonify(pesan="Login berhasil.", redirect="/beranda")


@bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify(pesan="Anda sudah keluar.")


@bp.get("/api/saya")
@wajib_login()
def saya():
    return jsonify(model_user.data_publik(g.user))
