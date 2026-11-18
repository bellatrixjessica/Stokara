import pytest

from app import create_app
from config import TestConfig


def test_health_database_terhubung(client):
    respon = client.get("/health")
    assert respon.status_code == 200
    assert respon.get_json() == {"status": "ok", "database": "terhubung"}


def test_aplikasi_menolak_jalan_tanpa_secret_key():
    class TanpaKunci(TestConfig):
        SECRET_KEY = None

    with pytest.raises(RuntimeError):
        create_app(TanpaKunci)
