# Stokara

Sistem inventory gudang untuk melayani permintaan barang dari toko. Studi kasus: Warehouse Branch Semarang.

**Demo:** https://stokara-three.vercel.app

**Teknologi:** Python · Flask · MongoDB Atlas · Webix · pytest · Vercel

## Fitur

| Role | Fitur |
|---|---|
| Admin | Data master produk, toko, supplier, dan karyawan |
| Kepala Gudang | Dashboard insight, persetujuan permintaan, pemeriksaan stock opname, stok, laporan |
| Staff Gudang | Barang masuk, pengiriman, stock opname, stok |
| Kepala Toko | Pengajuan permintaan, konfirmasi penerimaan, laporan toko |

Semua role memiliki beranda dan notifikasi.

## Rumus insight

Dihitung dari permintaan 30 hari terakhir.

| Nilai | Rumus |
|---|---|
| Demand per hari | qty diminta ÷ 30 |
| Fill rate | qty dikirim ÷ qty diminta × 100% |
| Safety stock | demand per hari × 2 |
| Reorder point | demand per hari × lead time + safety stock |
| Saran restock | demand per hari × (lead time + 7) − stok tersedia |

## Menjalankan

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python scripts/seed_akun.py
python scripts/seed_data.py
python scripts/buat_index.py
python run.py
```

## Test

```powershell
python -m pytest
```

## Deploy

```powershell
npx vercel deploy --prod
```

Environment variable di Vercel: `MONGO_URI`, `SECRET_KEY`.
