"""Titik awal aplikasi. Jalankan dengan: python run.py"""
import os

from app import create_app

app = create_app()  # Vercel juga mencari variabel bernama "app" ini

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
