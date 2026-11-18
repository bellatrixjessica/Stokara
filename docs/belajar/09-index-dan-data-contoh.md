# Tahap 9 – Index MongoDB dan Data Contoh

Tujuan tahap ini: memenuhi ketentuan **MongoDB indexing (text, composite)**, lalu mengisi database dengan **data contoh 30 hari** supaya dashboard dan laporan punya isi saat presentasi.

## Apa itu index?

Index seperti **daftar isi buku**. Tanpa index, MongoDB membaca semua dokumen satu per satu (**COLLSCAN**). Dengan index, MongoDB langsung melompat ke dokumen yang dicari (**IXSCAN**).

## Index Stokara (`app/models/indeks.py`)

### Unique: mencegah data ganda

| Collection | Field | Mencegah |
|---|---|---|
| `users` | `username` | Dua akun dengan username sama |
| `master_produk`, `master_toko`, `master_supplier` | `kode` | Dua produk/toko/supplier dengan kode sama |
| `permintaan`, `barang_masuk`, `opname` | `nomor` | Dua dokumen dengan nomor sama |

Aplikasi sudah mengecek kode ganda sebelum menyimpan (tahap 4). Unique index adalah **pengaman terakhir di database**: kalau dua orang menyimpan kode yang sama di detik yang sama, penyimpanan kedua tetap ditolak MongoDB (`DuplicateKeyError`). Ini juga menutup keterbatasan nomor dokumen dari tahap 5.

### Composite: untuk query yang sering dijalankan

| Index | Field (urutan penting) | Dipakai oleh |
|---|---|---|
| `toko_status_tanggal` | `toko_id`, `status`, `dibuat` ↓ | Halaman Kepala Toko: permintaan tokonya, difilter status, terbaru dulu |
| `status_tanggal` | `status`, `dibuat` ↓ | Halaman gudang, dashboard, beranda |
| `produk_waktu` | `produk_id`, `waktu` ↓ | Riwayat stok satu produk |
| `role_waktu`, `toko_waktu` | `untuk_role`/`untuk_toko_id`, `waktu` ↓ | Lonceng notifikasi |

Urutan field mengikuti query: **field filter dulu, lalu field urutan (sort)**. Contoh: "permintaan toko X berstatus Y, urut terbaru" → `toko_id`, `status`, lalu `dibuat`.

### Text: pencarian kata

```python
("master_produk", [("nama", TEXT), ("kategori", TEXT)],
 {"weights": {"nama": 3, "kategori": 1}, "default_language": "none"})
```

- **weights**: kata yang cocok di **nama** bernilai 3 kali lebih tinggi daripada di kategori.
- **default_language "none"**: tanpa aturan bahasa Inggris (bahasa Indonesia tidak didukung MongoDB untuk *stemming*), jadi kata dicocokkan apa adanya.

Dipakai di kotak **cari** halaman **Stok Gudang** (`filter_cari()` di `app/models/stok.py`):

| Yang diketik | Cara mencari |
|---|---|
| Ada angkanya, contoh `P-0004`, `0004` | Awalan kode (memakai unique index kode) |
| Kata, contoh `minyak`, `sembako` | `$text` → **text index** |

Kode dipisah karena text index menganggap tanda `-` sebagai "kecuali": mencari `P-0001` dengan `$text` justru berarti "P tetapi bukan 0001".

## Membuat index dan membuktikannya dipakai

```powershell
python scripts/buat_index.py --cek
```

Script membuat semua index (aman diulang), lalu menjalankan `explain()` untuk tiga query dan menampilkan rencana MongoDB. Yang dicari adalah kata **IXSCAN** (memakai index) atau **TEXT_MATCH** (memakai text index), bukan **COLLSCAN**. Hasil dari Atlas ditempel di bagian akhir catatan ini.

## Data contoh 30 hari (`scripts/seed_data.py`)

```powershell
python scripts/seed_akun.py          # akun dan toko (tahap 2)
python scripts/seed_data.py          # supplier, produk, transaksi 30 hari
python scripts/seed_data.py --reset  # hapus semua transaksi lalu isi ulang (ketik HAPUS)
```

Isi yang dibuat:

| Data | Isi |
|---|---|
| Supplier | 4 (SUP-01 sampai SUP-04) |
| Produk | 12 (P-0001 sampai P-0012), 4 kategori |
| Barang masuk | Stok awal 30 hari lalu + 3 kali restock mingguan |
| Permintaan | ±2 permintaan per hari dari 3 toko, dengan semua status |
| Opname | 1 opname disetujui (ada selisih −2 dan −1) |
| Mutasi stok | Otomatis dari semua kejadian di atas |

Data dibuat langsung ke database, tetapi **mengikuti aturan bisnis yang sama** dengan aplikasi:
- qty disetujui = terkecil antara diminta dan stok tersedia; kalau semuanya 0 → ditolak "Stok kosong";
- qty dikirim = qty disetujui (tidak ada pengiriman sebagian);
- setiap perubahan stok tercatat di `mutasi_stok`, jadi **stok produk = jumlah semua mutasinya**.

`random.Random(2026)` membuat angka acak yang **selalu sama** setiap dijalankan, jadi hasil dashboard bisa diprediksi:

| Hasil | Nilai |
|---|---|
| Fill rate 30 hari | ± 87% |
| Stok kritis | 1 (Air Mineral 600ml) |
| Perlu restock | 1 (Mi Instan Goreng 85g) |
| Menunggu persetujuan | 1 (untuk demo Kepala Gudang) |
| Menunggu dikirim | 1 (untuk demo Staff Gudang) |

Script menolak berjalan kalau database sudah berisi transaksi, supaya data asli tidak tertimpa. `--reset` meminta konfirmasi dengan mengetik **HAPUS**.

## Test (`tests/test_seed_dan_index.py`, 8 test)

| Test | Membuktikan |
|---|---|
| `test_stok_produk_sama_dengan_jumlah_mutasi` | Data contoh konsisten: stok = jumlah mutasi, tidak ada yang minus |
| `test_tidak_ada_pengiriman_sebagian` | Qty dikirim = qty disetujui |
| `test_hasil_dashboard_data_contoh` | 1 kritis, 1 perlu restock, fill rate 80–92% |
| `test_index_unique_menolak_kode_ganda` | Unique index menolak kode ganda |
| `test_cari_stok_berdasarkan_kode` | Pencarian kode di halaman stok |

`$text` tidak bisa dites dengan database palsu (mongomock tidak mendukungnya), jadi buktinya memakai `explain()` di Atlas.

Total test sekarang **107**.

## Hasil di MongoDB Atlas (19 Nov 2026)

```
13 index siap.

  users            : username_unik
  master_produk    : kode_produk_unik, cari_produk
  master_toko      : kode_toko_unik
  master_supplier  : kode_supplier_unik
  permintaan       : nomor_permintaan_unik, toko_status_tanggal, status_tanggal
  barang_masuk     : nomor_barang_masuk_unik
  opname           : nomor_opname_unik
  mutasi_stok      : produk_waktu
  notifikasi       : role_waktu, toko_waktu

Bukti index dipakai (explain):
  - Permintaan satu toko, status DIKIRIM, terbaru dulu
      FETCH -> IXSCAN (toko_status_tanggal)
  - Cari produk dengan kata 'minyak' (text index)
      TEXT_MATCH (cari_produk) -> FETCH -> IXSCAN (cari_produk)
  - Produk berkode P-0001 (unique index)
      EXPRESS_IXSCAN (kode_produk_unik)
```

Tidak ada **COLLSCAN**: ketiga query memakai index. `EXPRESS_IXSCAN` adalah jalur cepat MongoDB 8 untuk mencari satu dokumen lewat unique index.

Data contoh di Atlas:

```
  barang_masuk  : 16 dokumen
  permintaan    : 57 dokumen
  mutasi_stok   : 191 dokumen
  opname        : 1 dokumen

Fill rate 30 hari : 86.8%
Stok kritis       : 1
Perlu restock     : 1
Menunggu setuju   : 1, menunggu kirim: 1
```

Pencarian di halaman Stok Gudang lewat aplikasi:

```
'minyak'       -> P-0001 Minyak Goreng 1L
'sembako'      -> P-0001 Minyak Goreng 1L, P-0002 Beras Premium 5kg, P-0003 Gula Pasir 1kg
'air mineral'  -> P-0005 Air Mineral 600ml
'P-0004'       -> P-0004 Mi Instan Goreng 85g
```

## Cek pemahaman

1. Apa beda COLLSCAN dan IXSCAN?
2. Aplikasi sudah mengecek kode ganda. Kenapa masih perlu unique index?
3. Kenapa urutan field di index `toko_status_tanggal` adalah toko, status, lalu tanggal?
4. Kenapa pencarian `P-0001` tidak memakai text index?
5. Kenapa data contoh memakai `random.Random(2026)`, bukan angka acak biasa?
