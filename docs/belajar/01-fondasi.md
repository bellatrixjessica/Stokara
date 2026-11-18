# Tahap 1 – Fondasi

Tujuan tahap ini: aplikasi Flask bisa jalan dan tersambung ke database `stokara` di MongoDB Atlas.

## Struktur folder Stokara

Pola yang dipakai mirip **MVC** (Model – View – Controller):

```
Stokara/
├── run.py              ← titik awal: python run.py
├── config.py           ← pengaturan (membaca .env)
├── requirements.txt    ← daftar library untuk dijalankan (dipakai Vercel)
├── requirements-dev.txt← + library untuk testing
├── .env                ← RAHASIA: password database, secret key (tidak di-upload)
├── .env.example        ← contoh isi .env (boleh di-upload)
├── app/
│   ├── __init__.py     ← create_app(): merakit aplikasi
│   ├── db.py           ← koneksi MongoDB
│   ├── routes/         ← CONTROLLER: menerima URL, cek login, panggil model
│   ├── models/         ← MODEL: aturan bisnis + query MongoDB      (tahap 2 dst.)
│   ├── templates/      ← VIEW: halaman HTML (Jinja)                (tahap 3)
│   └── static/         ← VIEW: CSS, JavaScript Webix, logo         (tahap 3)
├── scripts/            ← script sekali jalan: cek koneksi, seed data, index
├── tests/              ← unit test (pytest)
└── docs/               ← mockup, catatan belajar, SRS, System Design
```

| Lapisan | Folder | Contoh nanti |
|---|---|---|
| Model | `app/models/` | `permintaan.py` berisi fungsi `setujui()` yang memeriksa stok tersedia |
| View | `app/templates/`, `app/static/` | halaman Permintaan dengan tabel Webix |
| Controller | `app/routes/` | URL `POST /api/permintaan/<id>/setujui` yang mengecek role lalu memanggil `setujui()` |

## File yang dibuat di tahap ini

| File | Isi singkat |
|---|---|
| `config.py` | Kelas `Config` membaca `SECRET_KEY` dan `MONGO_URI` dari `.env`. `TestConfig` dipakai saat testing. |
| `app/db.py` | `init_db(app)` membuka koneksi sekali. `get_db()` dipakai di mana saja untuk mengambil database. |
| `app/__init__.py` | `create_app()` membaca config, mengecek `SECRET_KEY`, membuka database, mendaftarkan route. |
| `app/routes/umum.py` | Route `/` (sementara) dan `/health` untuk cek koneksi database. |
| `run.py` | Membuat aplikasi dan menjalankannya. |
| `scripts/cek_koneksi.py` | Cek koneksi Atlas dan izin tulis ke database `stokara`. |
| `tests/` | 3 test pertama. |

## Alur saat membuka `/health`

```
Browser → run.py (app) → routes/umum.py: health() → db.py: get_db() → MongoDB Atlas: ping
                                                   ← {"status": "ok", "database": "terhubung"}
```

## Kenapa ada `create_app()`?

Supaya aplikasi bisa dibuat dengan **pengaturan berbeda**:
- `create_app()` → pengaturan asli, database Atlas (dipakai `run.py` dan Vercel).
- `create_app(TestConfig)` → database palsu di memori (dipakai pytest), jadi test tidak mengotori data asli.

## Kenapa `.env`?

Password database tidak boleh tertulis di kode, karena kode akan di-upload ke GitHub (publik). `.env` sudah masuk `.gitignore`, jadi tidak ikut ter-upload. Di Vercel, isinya dimasukkan lewat menu **Environment Variables**.

## Database `stokara` di Atlas

Di MongoDB, database **tidak perlu dibuat dulu**. Database dan collection muncul sendiri saat data pertama disimpan.

Yang perlu disiapkan adalah **izin user database**. User `warehouse_inventory` awalnya hanya punya `readWrite@warehouse_inventory`, sehingga `scripts/cek_koneksi.py` gagal di langkah "Izin tulis". Solusinya di Atlas:

**Database & Network Access → Database Users → Edit → Specific Privileges → Add Specific Privilege → `readWrite` @ `stokara`** (collection dikosongkan) → **Update User**.

Izin dibatasi per database (bukan "read and write to any database") supaya user aplikasi hanya bisa menyentuh database miliknya. Ini prinsip *least privilege*.

## Cara menjalankan

```powershell
cd D:\Stokara
.\venv\Scripts\activate
python run.py
```

Buka http://127.0.0.1:5000/health → harus tampil `"database": "terhubung"`.

Menjalankan test:

```powershell
python -m pytest
```

Cek koneksi dan izin database:

```powershell
python scripts/cek_koneksi.py
```

## Cek pemahaman

1. Apa beda `config.py` dan `.env`? Mana yang boleh di-upload ke GitHub?
2. Kenapa test memakai `TestConfig`, bukan database Atlas?
3. Di folder mana aturan "qty disetujui tidak boleh melebihi stok tersedia" akan ditulis? Kenapa bukan di `routes/`?
