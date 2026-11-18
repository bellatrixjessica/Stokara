# Tahap 5 – Stok dan Barang Masuk

Tujuan tahap ini: stok gudang tercatat rapi, dan **setiap** perubahan stok punya riwayat.

## Tiga angka stok

| Angka | Arti | Disimpan di |
|---|---|---|
| **Stok fisik** | Barang yang benar-benar ada di rak gudang | `master_produk.stok` |
| **Dipesan** | Qty yang sudah **disetujui** untuk toko tapi **belum dikirim** | Dihitung dari `permintaan` berstatus DISETUJUI |
| **Stok tersedia** | **Fisik − dipesan**. Ini yang boleh disetujui untuk permintaan baru | Dihitung |

Contoh: Minyak Goreng fisik 91, sudah disetujui 30 untuk Toko Salatiga tapi truknya belum berangkat → tersedia **61**. Kalau toko lain meminta 70, Kepala Gudang hanya boleh menyetujui maksimal 61 (aturan ini dipakai di tahap 6).

## Aturan: stok fisik hanya berubah lewat 3 fungsi

Semua ada di `app/models/stok.py`, dan setiap pemanggilan **otomatis** menulis satu dokumen di `mutasi_stok`:

| Fungsi | Jenis mutasi | Dipanggil oleh |
|---|---|---|
| `tambah_stok()` | MASUK (+) | Barang masuk dari supplier (tahap ini) |
| `kurangi_stok()` | KELUAR (−) | Pengiriman ke toko (tahap 6) |
| `sesuaikan_stok()` | ADJUST (±) | Stock opname yang disetujui (tahap 7) |

Tidak ada form yang bisa mengubah angka stok secara langsung, termasuk form Produk di tahap 4. Karena itu, angka stok selalu bisa dilacak asalnya lewat riwayat mutasi.

Contoh dokumen `mutasi_stok`:

```json
{
  "kode": "P-0001", "nama": "Minyak Goreng 1L",
  "jenis": "MASUK", "perubahan": 91,
  "stok_sebelum": 0, "stok_sesudah": 91,
  "referensi": "BM-261119-0001",
  "keterangan": "Barang masuk dari PT Sumber Pangan Jaya",
  "oleh": {"nama": "Staff Gudang Semarang"},
  "waktu": "2026-11-19T02:36:00+00:00"
}
```

## Stok tidak bisa minus

```python
produk = get_db().master_produk.find_one_and_update(
    {"_id": produk_id, "stok": {"$gte": qty}},   # syarat: stok masih cukup
    {"$inc": {"stok": -qty}},                    # kurangi
    return_document=ReturnDocument.AFTER,
)
if produk is None:
    raise ValidasiError("Stok fisik tidak cukup.")
```

Pengecekan syarat dan pengurangannya dikerjakan MongoDB dalam **satu langkah** (atomic). Bandingkan dengan cara dua langkah:

```python
# CARA YANG RAWAN (tidak dipakai):
produk = find_one(...)            # 1. baca stok = 10
if produk["stok"] >= qty:         # 2. cek
    update_one(... -qty ...)      # 3. kurangi
```

Kalau dua Staff Gudang mengirim 8 unit di detik yang sama, keduanya bisa membaca stok = 10 di langkah 1, lalu keduanya mengurangi, sehingga stok menjadi −6. Dengan `find_one_and_update` + `$gte`, permintaan kedua tidak menemukan dokumen yang cocok, jadi ditolak.

## Barang masuk

Alur saat Staff Gudang menekan **Simpan**:

```
1. Validasi isian       → supplier dipilih, surat jalan diisi, minimal 1 produk,
                          qty 1–100.000, produk tidak boleh ganda       (gagal → 400)
2. Periksa database     → supplier & semua produk masih aktif            (gagal → 400)
3. Buat nomor           → BM-261119-0002
4. Simpan dokumen       → collection barang_masuk
5. Tambah stok          → tambah_stok() per produk → mutasi MASUK tercatat
```

Semua pemeriksaan (langkah 1–2) selesai **sebelum** ada yang disimpan, jadi data salah tidak meninggalkan dokumen setengah jadi.

Kode, nama, dan satuan produk **ikut disimpan** di dokumen barang masuk. Kalau suatu hari Admin mengganti nama produk, dokumen lama tetap menampilkan nama saat barang itu diterima.

### Nomor dokumen

`app/utils/nomor.py` membuat nomor `BM-YYMMDD-urutan`, contoh `BM-261119-0002` = barang masuk ke-2 tanggal 19 Nov 2026. Urutan dihitung dari jumlah dokumen hari itu + 1. Pola yang sama dipakai untuk permintaan (`PRM-`) dan opname (`OPN-`).

Keterbatasan: kalau dua orang menyimpan di detik yang sama, keduanya bisa mendapat nomor yang sama. Di tahap 9, *unique index* pada `nomor` membuat penyimpanan kedua ditolak, jadi nomor tetap tidak pernah ganda.

## Hak akses

| | Kepala Gudang | Staff Gudang | Kepala Toko |
|---|---|---|---|
| Lihat stok & riwayat | ✓ | ✓ | ✗ (403) |
| Lihat barang masuk | ✓ | ✓ | ✗ (403) |
| Catat barang masuk | ✗ (403) | ✓ | ✗ (403) |

Tombol "Catat Barang Masuk" hanya muncul untuk Staff Gudang (`DATA.boleh_catat`), tetapi pengamanannya tetap di server: `@wajib_login(STAFF_GUDANG)`.

## Waktu: simpan UTC, tampil WIB

Server menyimpan waktu dalam **UTC** (`app/utils/waktu.py`). Browser mengubahnya ke **WIB** lewat `tanggalWaktu()` di `app.js` (`timeZone: "Asia/Jakarta"`). Jadi jam yang tampil tetap benar walaupun server Vercel berada di negara lain.

## Halaman Webix

| Halaman | Isi |
|---|---|
| Stok Gudang (`gudang/stok.js`) | Tabel fisik/dipesan/tersedia (tersedia 0 berwarna merah). Klik baris → jendela riwayat mutasi dengan label Masuk/Keluar/Penyesuaian |
| Barang Masuk (`gudang/barang_masuk.js`) | Tabel dokumen; klik baris → detail. Form: pilih supplier, isi surat jalan, lalu tambah produk satu per satu (combo + counter + Tambah) ke tabel kecil sebelum disimpan |

## Test

| File | Jumlah | Contoh |
|---|---|---|
| `tests/test_stok.py` | 5 | `test_stok_tidak_bisa_minus`, `test_stok_tersedia_dikurangi_qty_disetujui` |
| `tests/test_barang_masuk.py` | 6 | `test_barang_masuk_menambah_stok`, `test_validasi_barang_masuk` (6 isian salah, tidak ada yang tersimpan) |

Total test sekarang **57**, selesai sekitar 7 detik. Sebelumnya test butuh 44 detik karena setiap test membuat ulang hash password. Sekarang hash dibuat sekali di `tests/conftest.py` dan dipakai bersama.

## Cek pemahaman

1. Apa beda stok fisik dan stok tersedia? Mana yang dipakai saat menyetujui permintaan?
2. Kenapa form Produk tidak boleh mengubah stok langsung?
3. Jelaskan kenapa `find_one_and_update` dengan syarat `$gte` mencegah stok minus, sedangkan cara "baca dulu baru kurangi" tidak.
4. Kenapa nama produk ikut disimpan di dokumen barang masuk?
