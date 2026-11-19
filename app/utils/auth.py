from functools import wraps

from flask import abort, g, jsonify, redirect, request, session

from app.models import user as model_user


def wajib_login(*role_boleh):
    def decorator(fungsi_route):
        @wraps(fungsi_route)
        def pembungkus(*args, **kwargs):
            user = model_user.cari_berdasarkan_id(session.get("user_id"))
            if user is None or not user["aktif"]:
                session.clear()
                if request.path.startswith("/api/"):
                    return jsonify(pesan="Silakan login terlebih dahulu."), 401
                return redirect("/login")

            if role_boleh and user["role"] not in role_boleh:
                abort(403)

            g.user = user
            return fungsi_route(*args, **kwargs)
        return pembungkus
    return decorator
