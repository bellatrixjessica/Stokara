"""Decorator untuk membatasi siapa yang boleh membuka halaman atau API.

Contoh pemakaian di route:

    @bp.get("/api/saya")
    @wajib_login()                      # semua role yang sudah login
    def saya(): ...

    @bp.post("/api/permintaan/<id>/setujui")
    @wajib_login(KEPALA_GUDANG)         # hanya Kepala Gudang
    def setujui(id): ...
"""
from functools import wraps

from flask import abort, g, jsonify, redirect, request, session

from app.models import user as model_user


def wajib_login(*role_boleh):
    def decorator(fungsi_route):
        @wraps(fungsi_route)
        def pembungkus(*args, **kwargs):
            # 1. Authentication: siapa pengguna ini? Ambil dari session.
            user = model_user.cari_berdasarkan_id(session.get("user_id"))
            if user is None or not user["aktif"]:
                session.clear()
                if request.path.startswith("/api/"):
                    return jsonify(pesan="Silakan login terlebih dahulu."), 401
                return redirect("/login")

            # 2. Authorization: apakah role-nya boleh?
            if role_boleh and user["role"] not in role_boleh:
                abort(403)  # ditangani halaman error 403 (app/__init__.py)

            g.user = user  # bisa dipakai di dalam route: g.user["nama"]
            return fungsi_route(*args, **kwargs)
        return pembungkus
    return decorator
