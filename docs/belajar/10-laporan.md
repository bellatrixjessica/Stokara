# Tahap 10 – Laporan (Excel dan PDF)

Tujuan tahap ini: kepala bisa **merekap data untuk periode tertentu** dan **mengunduhnya** sebagai Excel atau PDF, sesuai layar 6 di mockup.

| Role | Laporan yang bisa dibuka |
|---|---|
| Kepala Gudang | Permintaan Toko (semua toko atau satu toko), Mutasi Stok, Barang Masuk, Saran Restock |
| Kepala Toko | Permintaan Toko, **hanya tokonya sendiri** |
| Admin, Staff Gudang | Tidak ada (menu tidak muncul, URL ditolak 403) |

## File yang dibuat

| File | Isi |
|---|---|
| `app/models/laporan.py` | Mengambil data dan menghitung ringkasan setiap laporan |
| `app/routes/laporan.py` | Halaman `/laporan` dan API `/api/laporan/<jenis>` |
| `app/static/js/laporan.js` | Filter, ringkasan, tabel, tombol Unduh Excel/PDF |
| `app/utils/validasi.py` | Fungsi baru `tanggal()` |
| `tests/test_laporan.py` | 20 test |

## Alur

```
Pilih jenis + tanggal ──► GET /api/laporan/permintaan?dari=2026-10-21&sampai=2026-11-19&toko=<id>
                                   │
                         routes/laporan.py : cek role, validasi tanggal
                                   │
                         models/laporan.py : ambil data, hitung ringkasan
                                   │
                         {"judul", "periode", "ringkasan": [...], "baris": [...]}
                                   │
       laporan.js : tampilkan 4 kotak ringkasan + tabel ──► Unduh Excel / Unduh PDF
```

Semua laporan mengembalikan **bentuk data yang sama** (judul, periode, ringkasan, baris). Karena itu satu halaman dan satu fungsi unduh cukup untuk empat laporan.

## Isi setiap laporan

| Laporan | Satu baris = | Ringkasan |
|---|---|---|
| Permintaan Toko | satu permintaan | jumlah permintaan (berapa dibatalkan), qty diminta, qty dikirim, fill rate |
| Mutasi Stok | satu perubahan stok | jumlah mutasi, total masuk, total keluar, penyesuaian opname |
| Barang Masuk | satu produk yang diterima | dokumen, supplier, jenis produk, total qty |
| Saran Restock | satu produk | stok kritis, perlu restock, produk dipantau, total saran |

**Fill rate di laporan memakai aturan yang sama dengan dashboard** (tahap 8): hanya permintaan Dikirim, Diterima, dan Ditolak yang dihitung; Ditolak dihitung dikirim 0; Dibatalkan tidak dihitung. Di tabel, permintaan yang belum selesai ditulis "belum selesai" dan yang dibatalkan "tidak dihitung".

**Saran Restock tidak memakai tanggal**, karena isinya keadaan stok *saat ini* (dihitung dari permintaan 30 hari terakhir). Saat laporan ini dipilih, kotak tanggal dinonaktifkan.

## Tanggal WIB vs waktu UTC

Pengguna memilih tanggal WIB, tetapi database menyimpan waktu UTC (tahap 5). `rentang_waktu()` mengubahnya:

```
Pilih 19 Nov 2026 s/d 19 Nov 2026
  awal  = 19 Nov 00.00 WIB = 18 Nov 17.00 UTC   ($gte, termasuk)
  akhir = 20 Nov 00.00 WIB = 19 Nov 17.00 UTC   ($lt, tidak termasuk)
```

Tanpa pengubahan ini, permintaan yang dibuat pukul 23.00 WIB (16.00 UTC) bisa masuk ke tanggal yang salah. Test `test_batas_tanggal_mengikuti_wib` membuktikannya.

## Keamanan

| Ancaman | Pencegahan | Lokasi |
|---|---|---|
| Kepala Toko membuka laporan toko lain dengan mengubah `?toko=` | Untuk Kepala Toko, `toko_id` **selalu** diambil dari akunnya; parameter `toko` diabaikan | `routes/laporan.py` |
| Kepala Toko membuka laporan gudang lewat URL | Jenis selain `permintaan` → 403 | `routes/laporan.py` |
| Tanggal aneh, contoh `2026-02-31` atau `{"$gt": ""}` | `tanggal()`: harus teks berformat tahun-bulan-hari dan tanggal yang benar | `utils/validasi.py` |
| Permintaan laporan sangat panjang yang membebani server | Periode maksimal 366 hari | `models/laporan.py` |

## Unduh Excel dan PDF

Memakai fitur bawaan Webix, **tanpa library Python tambahan**:

```js
webix.toExcel($$("tabel"), { filename, columns, docHeader, docFooter });
webix.toPDF($$("tabel"), { filename, columns, orientation: "landscape", docHeader, docHeaderImage });
```

- File dibuat **di browser**. Webix memuat pustaka Excel/PDF-nya dari CDN Webix saat tombol pertama kali diklik.
- Yang diunduh **semua baris**, bukan hanya halaman tabel yang sedang tampil.
- Kolom unduhan berbeda dari kolom layar (`KOLOM[jenis].ekspor`): teks biasa tanpa HTML, kode dan nama produk dipisah, kolom qty bertipe **angka** di Excel sehingga bisa langsung dijumlahkan.
- Excel: baris judul di atas, baris ringkasan dan "Dicetak oleh ..." di bawah.
- PDF: logo, judul, periode, ringkasan, dan "Dicetak oleh ..." di setiap halaman, lalu "Halaman 1 dari 5" di bawah.
- Pustaka PDF Webix hanya menerima gambar JPEG, jadi `logoJpeg()` menggambar ulang logo SVG menjadi JPEG di browser.

## Tampilan

- Desktop: pilihan laporan berupa tombol (segmented), filter satu baris, tabel 15 baris per halaman (pager).
- Ponsel: pilihan laporan menjadi dropdown, filter ditumpuk, kolom yang kurang penting disembunyikan (nama toko pindah ke bawah nomor).
- Kepala Toko: tidak ada pilihan jenis dan pilihan toko; kolom toko disembunyikan.
- Kalender Webix diubah ke bahasa Indonesia di `app.js` (nama bulan dan hari, "Halaman ... dari ..." di PDF).

## Test (`tests/test_laporan.py`, 20 test)

| Test | Membuktikan |
|---|---|
| `test_rentang_satu_hari_wib_dalam_utc` | Tanggal WIB diubah ke rentang UTC yang benar |
| `test_format_tanggal_salah_ditolak` | `19/11/2026`, `2026-02-31`, angka, dan objek ditolak |
| `test_laporan_permintaan_fill_rate_sama_dengan_aturan_dashboard` | Ditolak = dikirim 0, Dibatalkan tidak dihitung |
| `test_batas_tanggal_mengikuti_wib` | Pukul 23.00 WIB masih masuk tanggal itu, 01.00 WIB masuk tanggal berikutnya |
| `test_kepala_toko_hanya_melihat_tokonya_walaupun_mengirim_toko_lain` | Parameter `toko` tidak bisa dipakai mengintip toko lain |
| `test_kepala_toko_tidak_boleh_laporan_gudang` | Mutasi, barang masuk, restock → 403 |
| `test_role_lain_tidak_boleh_membuka_laporan` | Admin dan Staff Gudang → 403 |
| `test_laporan_mutasi_menjumlahkan_per_jenis` | Total masuk, keluar, penyesuaian |
| `test_laporan_barang_masuk_satu_baris_per_produk` | Satu dokumen 2 produk = 2 baris |

Unduhan Excel/PDF dicek langsung di browser (dibuat tanpa disimpan, lalu dibaca isinya): Excel berisi 57 baris data + judul + ringkasan, kolom qty bertipe angka; PDF 5 halaman landscape dengan logo dan nomor halaman.

Total test sekarang **127**.

## Cek pemahaman

1. Kenapa keempat laporan mengembalikan bentuk data yang sama?
2. Kenapa memilih 19 Nov memakai batas `$lt` 20 Nov 00.00 WIB, bukan `$lte` 19 Nov 23.59?
3. Kepala Toko mengubah URL menjadi `?toko=<id toko lain>`. Apa yang terjadi, dan di baris kode mana itu dicegah?
4. Kenapa laporan Saran Restock tidak memakai tanggal?
5. Kenapa kolom unduhan dibuat terpisah dari kolom di layar?
