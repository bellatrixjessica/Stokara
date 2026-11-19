# Tahap 12 – Deploy ke Vercel

Tujuan tahap ini: memenuhi ketentuan **deploy**. Stokara sekarang bisa dibuka siapa saja di **https://stokara-three.vercel.app**.

## Gambaran

```
Laptop (D:\Stokara) ──vercel deploy --prod──► Vercel (Flask sebagai serverless function)
                                                   │  MONGO_URI, SECRET_KEY dari Environment Variables
                                                   ▼
                                             MongoDB Atlas (database stokara)
```

Deploy dilakukan **langsung dari folder laptop** dengan Vercel CLI, bukan dari GitHub. Vercel tetap menyambungkan project ke repository GitHub, jadi kalau nanti ada push ke `main`, Vercel juga akan deploy otomatis.

## File baru

| File | Isi |
|---|---|
| `vercel.json` | Semua URL diarahkan ke `run.py`, yang berisi variabel `app` (aplikasi Flask). Vercel menjalankannya dengan runtime Python |
| `.vercelignore` | File yang **tidak** ikut di-upload: `.env`, `.env.local`, `venv/`, `tests/`, `scripts/`, `docs/` |

`vercel.json`:

```json
{
  "builds": [{ "src": "run.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "run.py" }]
}
```

Vercel memasang library dari `requirements.txt` (Flask, PyMongo, python-dotenv). Library test di `requirements-dev.txt` tidak ikut.

## Rahasia di server

| Di laptop | Di Vercel |
|---|---|
| File `.env` | **Environment Variables** di dashboard, tipe *Secret* (tidak bisa dibaca lagi setelah disimpan) |
| `MONGO_URI` | sama (database `stokara` yang sama) |
| `SECRET_KEY` | kunci **baru**, khusus server |
| `FLASK_DEBUG=1` | **tidak diisi** → `SESSION_COOKIE_SECURE` aktif, cookie login hanya dikirim lewat HTTPS |
| `DEMO_PASSWORD` | tidak perlu (hanya dipakai script seed di laptop) |

Tombol "Import .env" di Vercel sengaja tidak dipakai, supaya `FLASK_DEBUG=1` tidak ikut terbawa.

## Atlas Network Access

Server Vercel tidak punya alamat IP tetap, jadi Atlas diberi entry `0.0.0.0/0` (semua alamat). Database tetap terlindungi:
- koneksi wajib memakai username + password database di `MONGO_URI`;
- koneksi Atlas selalu terenkripsi (TLS);
- user database aplikasi hanya punya hak `readWrite` di database `stokara`.

## Pemeriksaan setelah deploy

| Cek | Hasil |
|---|---|
| `/health` | `{"database": "terhubung", "status": "ok"}` (Vercel bisa menghubungi Atlas) |
| `/` | dialihkan ke `/login` |
| `/login`, `/static/js/app.js` | 200 |
| `/.env` | **404** (rahasia tidak ikut di-upload) |

## Cara deploy ulang

Setelah mengubah kode:

```powershell
npx vercel deploy --prod
```

## Cek pemahaman

1. Kenapa `.env` tidak ikut di-upload, padahal aplikasi butuh isinya?
2. Kenapa `FLASK_DEBUG` tidak boleh diisi di Vercel?
3. Kenapa Atlas harus mengizinkan `0.0.0.0/0`, dan apa yang tetap melindungi database?
4. Apa arti hasil `"database": "terhubung"` di `/health`?
