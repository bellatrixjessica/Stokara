# Stokara

Sistem inventory gudang: stok, permintaan toko, stock opname, dashboard restock, laporan, dan notifikasi.
Studi kasus: Warehouse Branch Semarang.

**Teknologi:** Flask · MongoDB Atlas · Webix · Vercel

> README lengkap (fitur, rumus insight, akun contoh, deploy) ditulis di tahap 11.

## Menjalankan di laptop

```powershell
cd D:\Stokara
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env      # lalu isi nilainya
python run.py
```

Buka http://127.0.0.1:5000/health.

## Test

```powershell
python -m pytest
```

## Dokumentasi

- Mockup tampilan: [`docs/mockup/index.html`](docs/mockup/index.html)
- Catatan belajar per tahap: [`docs/belajar/`](docs/belajar/)
