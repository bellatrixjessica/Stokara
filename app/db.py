from flask import current_app
from pymongo import MongoClient


def init_db(app):
    if app.config["TESTING"]:
        import mongomock
        client = mongomock.MongoClient(tz_aware=True)
        app.db = client["stokara_test"]
    else:
        client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000, tz_aware=True)
        app.db = client.get_default_database()


def get_db():
    return current_app.db
