# Stokara

Sistem inventory gudang untuk melayani permintaan barang dari toko-toko. Studi kasus: **Warehouse Branch Semarang**, yang melayani 3 toko.

Stokara mencatat stok, barang masuk dari supplier, permintaan dari toko, pengiriman, dan stock opname. Dari data itu Stokara menghitung **fill rate** (seberapa banyak permintaan toko terpenuhi) dan **saran restock** (kapan dan berapa banyak harus memesan ke supplier).

| | |
|---|---|
| **Demo** | _(diisi setelah deploy)_ |
| **Repository** | https://github.com/bellatrixjessica/Stokara |
| **Dokumen** | [SRS](docs/SRS.md) · [System Design](docs/SYSTEM-DESIGN.md) · [Mockup](docs/mockup/index.html) · [Catatan per tahap](docs/belajar/) |

**Teknologi:** Python 3 · Flask 3.1 · MongoDB Atlas (PyMongo 4.20) · Webix 11.4 · pytest · Vercel

## Pemenuhan ketentuan tugas

| Ketentuan | Di Stokara |
|---|---|
| Flask | Application factory, 13 Blueprint, struktur MVC (`app/models`, `app/routes`, `app/templates` + `app/static`) |
| MongoDB | MongoDB Atlas, 9 collection, aggregation pipeline untuk insight |
| Collection `master_*` | `master_produk`, `master_toko`, `master_supplier` |
| Deploy | Vercel + MongoDB Atlas |
| Authentication | Login username + password, password disimpan sebagai hash scrypt, session cookie 8 jam |
| Authorization | Decorator `@wajib_login(role...)` di setiap route; Kepala Toko hanya bisa melihat data tokonya |
| Validasi & sanitasi | `app/utils/validasi.py`: cek tipe, panjang, format, key yang boleh; mencegah NoSQL injection dan XSS |
| Multi user / multi role | 4 role: Admin, Kepala Gudang, Staff Gudang, Kepala Toko |
| Dokumentasi teknis | [SRS](docs/SRS.md) dan [System Design](docs/SYSTEM-DESIGN.md) |
| Webix _(opsional)_ | Semua halaman dibuat dengan Webix (datatable, form, chart, dataview, window, pager, export) |
| Responsive UI _(opsional)_ | Tampilan ponsel: sidebar ikon, form layar penuh, kolom tabel menyesuaikan |
| Indexing _(opsional)_ | 13 index: 7 unique, 5 composite, 1 text (dibuktikan dengan `explain()`) |
| Unit testing _(opsional)_ | 127 test pytest dengan database palsu (mongomock) |

## Fitur per role

| Role | Yang bisa dilakukan |
|---|---|
| **Admin** | Kelola data master: produk, toko, supplier, karyawan (tambah, ubah, nonaktifkan, reset password) |
| **Kepala Gudang** | Dashboard insight; menyetujui, mengubah qty, atau menolak permintaan toko; memeriksa stock opname; melihat stok; laporan semua jenis |
| **Staff Gudang** | Mencatat barang masuk; mengirim permintaan yang sudah disetujui; menghitung stock opname; melihat stok |
| **Kepala Toko** | Mengajukan dan membatalkan permintaan; menandai barang diterima; laporan permintaan tokonya sendiri |

Semua role punya **Beranda** (kartu menu dengan jumlah pekerjaan yang menunggu) dan **lonceng notifikasi**.

### Alur utama: permintaan toko

```
Kepala Toko          Kepala Gudang                 Staff Gudang        Kepala Toko
 ajukan ──► DIAJUKAN ──setujui──► DISETUJUI ──kirim──► DIKIRIM ──terima──► DITERIMA
              │                     │   (stok fisik berkurang)
              │                     └──tolak (wajib alasan)──► DITOLAK
              ├──tolak (wajib alasan)──► DITOLAK
              └──batal (Kepala Toko)──► DIBATALKAN
```

Aturan bisnis penting:

- **Stok tersedia = stok fisik − stok dipesan.** Stok dipesan adalah qty yang sudah disetujui tetapi belum dikirim. Qty disetujui tidak boleh melebihi stok tersedia.
- **Tidak ada pengiriman sebagian:** qty dikirim selalu sama dengan qty disetujui. Kalau stok fisik ternyata kurang saat akan dikirim, pengiriman ditolak. Kepala Gudang lalu mengubah qty disetujui atau menolak permintaan.
- Toko melihat label **"Qty disesuaikan"** kalau gudang menyetujui lebih sedikit dari yang diminta.
- **Stok fisik hanya berubah lewat 3 jalan**, dan semuanya tercatat di riwayat mutasi:
  - barang masuk (MASUK);
  - pengiriman (KELUAR);
  - opname yang disetujui (ADJUST).
- Stok dikurangi dengan **operasi atomik MongoDB**, jadi stok tidak pernah minus walaupun dua orang memproses bersamaan.

## Rumus insight (Dashboard dan laporan Saran Restock)

Dihitung dari permintaan **30 hari terakhir**:

| Istilah | Rumus |
|---|---|
| Demand per hari | total qty diminta ÷ 30 (semua status kecuali Dibatalkan) |
| Fill rate | total qty dikirim ÷ total qty diminta × 100% (hanya Dikirim, Diterima, Ditolak; **Ditolak dihitung dikirim 0**) |
| Safety stock (SS) | demand per hari × 2 hari, dibulatkan ke atas |
| Reorder point (ROP) | demand per hari × lead time + SS, dibulatkan ke atas |
| Habis dalam | stok tersedia ÷ demand per hari |
| Saran restock | demand per hari × (lead time + 7 hari) − stok tersedia, dibulatkan ke atas, minimal 0 |

Status produk: **Kritis** jika tersedia ≤ SS, **Perlu restock** jika tersedia ≤ ROP, **Aman** jika tersedia > ROP.

**Contoh perhitungan.** Produk dengan lead time 3 hari, stok tersedia 80, diminta 360 dalam 30 hari:

```
Demand per hari = 360 / 30          = 12
Safety stock    = 12 × 2            = 24
Reorder point   = 12 × 3 + 24       = 60
Habis dalam     = 80 / 12           = 6,7 hari
Saran restock   = 12 × (3 + 7) − 80 = 40
Status          = 80 > 60           → Aman
```

Kalau stok turun menjadi 50: 24 < 50 ≤ 60 → **Perlu restock**, saran 12 × 10 − 50 = **70**.

**Contoh fill rate.** Toko meminta 50 (dikirim 40), 30 (dikirim 30), dan 20 (ditolak). Fill rate = (40 + 30 + 0) ÷ (50 + 30 + 20) = **70%**.

Kedua contoh ini ada di test (`tests/test_insight.py`, `tests/test_laporan.py`).

## Menjalankan di laptop

Kebutuhan: Python 3.11 atau lebih baru, dan database MongoDB Atlas (paket gratis M0 cukup).

```powershell
git clone https://github.com/bellatrixjessica/Stokara.git
cd Stokara
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Isi `.env`:

| Variabel | Isi |
|---|---|
| `SECRET_KEY` | Kunci acak. Buat dengan `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MONGO_URI` | Connection string Atlas, diakhiri nama database `/stokara` |
| `DEMO_PASSWORD` | Password awal untuk akun contoh (minimal 8 karakter) |
| `FLASK_DEBUG` | `1` di laptop. Di server jangan diisi |

`.env` berisi rahasia dan tidak ikut di-upload (ada di `.gitignore`).

Siapkan database lalu jalankan:

```powershell
python scripts/cek_koneksi.py          # cek koneksi ke Atlas
python scripts/seed_akun.py            # 3 toko + 6 akun contoh
python scripts/seed_data.py            # supplier, produk, transaksi 30 hari
python scripts/buat_index.py --cek     # 13 index + bukti explain()
python run.py
```

Buka http://127.0.0.1:5000. Cek koneksi server di http://127.0.0.1:5000/health.

`seed_data.py --reset` menghapus semua transaksi lalu mengisinya ulang. Script meminta konfirmasi dengan mengetik `HAPUS`.

### Akun contoh

Semua akun memakai password `DEMO_PASSWORD` dari `.env`. Password akun demo yang di-deploy diberikan terpisah, tidak ditulis di repository.

| Username | Role | Toko |
|---|---|---|
| `admin` | Admin | – |
| `kepala.gudang` | Kepala Gudang | – |
| `staff.gudang` | Staff Gudang | – |
| `toko.salatiga01` | Kepala Toko | Toko Salatiga 01 |
| `toko.ungaran01` | Kepala Toko | Toko Ungaran 01 |
| `toko.semarang01` | Kepala Toko | Toko Semarang Tengah 01 |

Data contoh sudah disiapkan untuk demo:
- 1 permintaan menunggu persetujuan (untuk Kepala Gudang);
- 1 permintaan menunggu dikirim (untuk Staff Gudang);
- 1 produk kritis dan 1 produk perlu restock di dashboard;
- fill rate sekitar 87%.

## Test

```powershell
python -m pytest
```

127 test berjalan dengan **database palsu di memori** (mongomock), jadi tidak menyentuh data Atlas.

| File | Yang dites |
|---|---|
| `test_auth.py` | Login, logout, session, akun nonaktif, NoSQL injection di login |
| `test_tampilan.py` | Menu per role, halaman error 403/404 |
| `test_master.py` | CRUD produk, toko, supplier, karyawan; validasi; hanya Admin |
| `test_stok.py`, `test_barang_masuk.py` | Stok fisik/tersedia, mutasi, barang masuk |
| `test_permintaan.py` | Semua perubahan status, aturan stok, klik ganda, toko lain tidak bisa mengintip |
| `test_opname.py` | Selisih, koreksi stok, opname ganda |
| `test_insight.py` | Rumus insight dan fill rate (contoh di atas) |
| `test_laporan.py` | Isi laporan, batas tanggal WIB, hak akses laporan |
| `test_seed_dan_index.py` | Data contoh konsisten, unique index |

## Struktur folder

```
Stokara/
├── run.py, config.py          titik mulai aplikasi dan pengaturan
├── app/
│   ├── __init__.py            create_app(): daftar blueprint dan halaman error
│   ├── db.py                  koneksi MongoDB
│   ├── models/                logika bisnis + akses database (Model)
│   ├── routes/                URL halaman dan API JSON (Controller)
│   ├── templates/             kerangka HTML Jinja (View)
│   ├── static/                Webix: css, js per halaman, logo (View)
│   └── utils/                 validasi, login/role, waktu, nomor dokumen
├── scripts/                   cek koneksi, seed, buat index
├── tests/                     127 test pytest
└── docs/                      SRS, System Design, mockup, catatan per tahap
```

## Keterbatasan

- Satu gudang (Branch Semarang). Struktur data sudah memakai `toko_id`, tetapi belum ada `gudang_id` untuk banyak gudang.
- Harga dan nilai Rupiah belum dicatat. Laporan berbasis qty.
- Notifikasi muncul saat halaman dibuka atau lonceng diklik (tidak real-time / push).
- Unduh Excel/PDF memuat pustaka dari CDN Webix, jadi perlu koneksi internet.
- Belum ada pembatasan percobaan login (rate limiting).

Rencana pengembangan ada di [System Design bagian 13](docs/SYSTEM-DESIGN.md#13-keterbatasan-dan-pengembangan).
