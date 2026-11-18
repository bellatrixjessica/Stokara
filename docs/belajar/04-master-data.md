# Tahap 4 – Master Data (Admin)

Tujuan tahap ini: Admin bisa mengelola **produk, toko, supplier, dan karyawan**. Ini memenuhi ketentuan **collection `master_*`**, dan melanjutkan **validasi & sanitasi** serta **multi user**.

## Collection

| Collection | Isi | Kunci unik |
|---|---|---|
| `master_produk` | kode, nama, kategori, satuan, supplier_id, lead_time_hari, **stok**, aktif | `kode` |
| `master_toko` | kode, nama, alamat, aktif | `kode` |
| `master_supplier` | kode, nama, telepon, alamat, aktif | `kode` |
| `users` | username, password_hash, nama, role, toko_id, aktif | `username` |

`master_produk.supplier_id` dan `users.toko_id` menyimpan **`_id` dokumen lain** (referensi), seperti *foreign key* di database relasional.

## Aturan yang dibuat

| Aturan | Alasan |
|---|---|
| Data **tidak dihapus**, hanya **dinonaktifkan** | Produk atau toko sudah dipakai di transaksi. Kalau dihapus, riwayat permintaan dan laporan jadi rusak |
| **Kode dan username tidak bisa diubah** | Kode adalah identitas yang dikenal pengguna; mengubahnya membingungkan riwayat |
| Kode otomatis **huruf besar**, hanya huruf, angka, dan `-` | `tk-01` dan `TK-01` dianggap sama, mencegah kode ganda |
| **Stok tidak bisa diisi dari form produk** | Stok hanya berubah lewat barang masuk, pengiriman, dan opname, supaya setiap perubahan tercatat (tahap 5) |
| Produk wajib punya **supplier yang aktif** | Lead time dan barang masuk berhubungan dengan supplier |
| Kepala Toko wajib punya **toko yang aktif** | Supaya permintaan selalu jelas berasal dari toko mana |
| Admin **tidak bisa menonaktifkan** atau **mengganti role** akunnya sendiri | Mencegah Admin mengunci dirinya dari menu Admin |
| Password baru **minimal 8 karakter**, disimpan sebagai hash | Keamanan akun |

## API (semua khusus Admin)

Pola yang sama untuk keempat master (contoh: toko):

| Method | URL | Fungsi |
|---|---|---|
| GET | `/api/master/toko` | Daftar semua toko |
| POST | `/api/master/toko` | Tambah toko |
| PUT | `/api/master/toko/<id>` | Ubah nama dan alamat |
| POST | `/api/master/toko/<id>/status` | Aktifkan atau nonaktifkan, isi `{"aktif": false}` |

Khusus karyawan ada tambahan `POST /api/master/karyawan/<id>/password` untuk reset password.

## Validasi baru di `app/utils/validasi.py`

| Fungsi | Memeriksa | Contoh ditolak |
|---|---|---|
| `kode()` | Huruf besar, angka, `-`, 2–20 karakter | `"TK 01!"` |
| `username()` | Huruf kecil, angka, `.`, `_`, 3–30 karakter | `"Toko Salatiga"` |
| `password()` | Minimal 8 karakter | `"123"` |
| `angka_bulat()` | Harus angka bulat dalam batas | `"3"` (teks), `true`, `0` untuk lead time |
| `pilihan()` | Harus salah satu dari daftar | satuan `"KILO"` |
| `ya_tidak()` | Harus `true`/`false` | `"tidak"` |
| `id_pilihan()` | ID data lain yang valid | supplier `"abc"` |
| `id_dari_url()` | ID di URL; rusak → 404 | `/api/master/toko/bukan-id` |

Ditambah `ambil_json()` dari tahap 2: field yang tidak dikenal ditolak. Contoh: mengirim `"stok": 999` ke form produk → **400**.

## Mengirim data MongoDB ke browser

Dokumen MongoDB berisi `ObjectId` dan `datetime` yang tidak bisa langsung diubah ke JSON. Fungsi `ke_json()` di `app/utils/data.py` mengubahnya:

```
{"_id": ObjectId("65f1..."), "toko_id": ObjectId("65a2..."), "dibuat": datetime(...)}
→ {"id": "65f1...", "toko_id": "65a2...", "dibuat": "2026-11-19T02:10:00+00:00"}
```

`_id` diganti nama menjadi `id` karena tabel Webix memakai `id` sebagai kunci baris. `password_hash` **selalu dibuang**.

## Halaman Webix

Keempat halaman memakai susunan yang sama:

```
judulHalaman(...)                       ← judul + keterangan
kartuTabel(toolbar, datatable)          ← kotak putih: cari + tombol Tambah, lalu tabel
buatJendela("jendela", ..., simpan)     ← popup form tambah/ubah
```

`kartuTabel()` dan `buatJendela()` ada di `layout.js` supaya tidak ditulis ulang di setiap halaman. Isi tabel dan form tetap ditulis langsung di file halaman masing-masing, jadi mudah dibaca.

| Komponen Webix | Dipakai untuk |
|---|---|
| `datatable` | Tabel data; kolom `onClick` untuk tombol Ubah/Nonaktifkan |
| `search` | Kotak cari; `filter()` menyaring baris tanpa memanggil server |
| `window` + `form` | Popup tambah/ubah; di ponsel tampil layar penuh |
| `richselect` | Pilihan satuan, supplier, role, toko |
| `counter` | Lead time (tombol − dan +) |
| `webix.confirm` | Dialog "Yakin nonaktifkan?" (fungsi `konfirmasi()`) |

### Escape di tabel

Kolom teks ditulis dengan `template: "#!nama#"`. Tanda **`!`** membuat Webix meng-escape isinya, jadi nama seperti `<b>Toko</b>` tampil sebagai teks, bukan HTML. Ini lanjutan pencegahan XSS dari tahap 3.

### Responsive

Di ponsel, kolom yang kurang penting (kode, alamat, kategori, supplier) disembunyikan dengan `hidden: LAYAR_KECIL`. Tombol aksi berubah menjadi ikon, dan label tombol "Tambah Produk" menjadi "Tambah".

## Test

`tests/test_master.py` berisi 18 test, contohnya:

| Test | Membuktikan |
|---|---|
| `test_selain_admin_tidak_bisa_membuka_master` | Kepala Gudang mendapat 403 |
| `test_kode_toko_duplikat_ditolak` | Kode ganda ditolak |
| `test_tambah_produk_stok_awal_nol` | Produk baru stoknya 0 |
| `test_validasi_isian_produk` | 6 isian salah, semuanya ditolak 400 |
| `test_reset_password` | Password lama tidak bisa dipakai lagi |
| `test_admin_tidak_bisa_mengunci_dirinya_sendiri` | Admin tidak bisa menonaktifkan diri sendiri |

Total test sekarang **46**.

## Cek pemahaman

1. Kenapa data master dinonaktifkan, bukan dihapus?
2. Apa yang terjadi kalau form produk mengirim `"stok": 999`? Fungsi mana yang menolaknya?
3. Kenapa kolom tabel ditulis `"#!nama#"`, bukan `"#nama#"`?
4. Apa isi `supplier_id` di dokumen produk, dan bagaimana nama supplier bisa tampil di tabel produk?
