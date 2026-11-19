import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    TESTING = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_DEBUG") != "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    NAMA_BRANCH = "Branch Semarang"

    PERIODE_HARI = 30
    HARI_PENGAMAN = 2
    PERIODE_CADANGAN_HARI = 7


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "kunci-khusus-test"
    SESSION_COOKIE_SECURE = False
