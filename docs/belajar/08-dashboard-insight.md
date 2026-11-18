# Tahap 8 – Dashboard Insight

Dashboard menjawab dua pertanyaan Kepala Gudang:

1. **Apakah permintaan toko terpenuhi?** → fill rate, tren 30 hari, fill rate per toko
2. **Kapan harus restock, dan berapa?** → status stok dan saran restock per produk

## Rumus (sama persis dengan README)

Semua dihitung dari permintaan **30 hari terakhir**.

| Insight | Rumus |
|---|---|
| Stok tersedia | stok fisik − qty disetujui yang belum dikirim (tahap 5) |
| Demand per hari | total qty diminta ÷ 30 (semua status **kecuali DIBATALKAN**) |
| Fill rate | total qty dikirim ÷ total qty diminta × 100% (hanya **DIKIRIM, DITERIMA, DITOLAK**; DITOLAK dihitung dikirim 0) |
| Safety stock | demand per hari × 2 hari ↑ |
| Reorder point (ROP) | demand per hari × lead time + safety stock ↑ |
| Habis dalam | stok tersedia ÷ demand per hari |
| Saran restock | demand per hari × (lead time + 7) − stok tersedia ↑, minimal 0 |

↑ = dibulatkan ke atas (barang tidak dipesan pecahan).

| Status | Syarat |
|---|---|
| **Kritis** | tersedia ≤ safety stock |
| **Perlu restock** | tersedia ≤ ROP |
| **Aman** | tersedia > ROP |
| **Tidak ada permintaan** | demand per hari = 0 |

Angka 30, 2, dan 7 ada di `config.py` (`PERIODE_HARI`, `HARI_PENGAMAN`, `PERIODE_CADANGAN_HARI`), jadi bisa diubah tanpa menyentuh rumus.

### Contoh perhitungan (README = test)

Minyak Goreng 1L, lead time 3 hari, diminta 360 dalam 30 hari, tersedia 80:

```
Demand per hari = 360 ÷ 30          = 12
Safety stock    = 12 × 2            = 24
ROP             = 12 × 3 + 24       = 60
Habis dalam     = 80 ÷ 12           = 6,7 hari
Saran restock   = 12 × (3 + 7) − 80 = 40
Status          = 80 > 60           → Aman
```

Angka ini diuji di `test_contoh_readme_status_aman`, jadi README dan aplikasi dijamin sama.

## Di mana rumusnya? (`app/models/insight.py`)

| Fungsi | Isi |
|---|---|
| `rumus_produk()` | Rumus untuk **satu produk**. Tidak menyentuh database (fungsi murni), jadi paling mudah diuji dan dijelaskan |
| `demand_per_produk()` | Total qty diminta per produk memakai **aggregation pipeline** MongoDB |
| `insight_produk()` | Gabungan stok tersedia + demand + rumus untuk semua produk |
| `fill_rate()` | Fill rate keseluruhan dan per toko |
| `tren_harian()` | Qty diminta dan dikirim per hari (tanggal WIB) untuk grafik |
| `dashboard()` | Semua data di atas dalam satu paket untuk `/api/dashboard` |

### Aggregation pipeline

```python
pipeline = [
    {"$match": {"dibuat": {"$gte": awal_periode()}, "status": {"$ne": "DIBATALKAN"}}},
    {"$unwind": "$items"},
    {"$group": {"_id": "$items.produk_id", "total": {"$sum": "$items.qty_diminta"}}},
]
```

| Tahap | Seperti di SQL | Arti |
|---|---|---|
| `$match` | `WHERE` | Ambil permintaan 30 hari terakhir yang tidak dibatalkan |
| `$unwind` | (memecah baris) | Satu permintaan berisi 3 produk → menjadi 3 dokumen, satu per produk |
| `$group` | `GROUP BY ... SUM()` | Jumlahkan qty diminta per produk |

Penjumlahannya dikerjakan **di server MongoDB**, jadi yang dikirim ke Flask hanya hasil akhirnya (satu baris per produk), bukan semua dokumen permintaan.

## Halaman Dashboard (`gudang/dashboard.js`)

Sesuai mockup:

| Bagian | Komponen Webix |
|---|---|
| 4 kartu angka: Fill rate, Stok kritis, Perlu restock, Menunggu persetujuan | `template` (di ponsel 2 × 2) |
| Tren permintaan 30 hari (ungu = diminta, kuning = dikirim) | `chart` tipe `bar` dengan 2 `series` |
| Fill rate per toko (di bawah 85% berwarna merah) | `datatable` tanpa header |
| Saran restock, dengan pilihan "Perlu tindakan / Semua produk" | `datatable` + `segmented` |

## Angka di kartu beranda

`/api/beranda` (`app/models/beranda.py`) memberi label "perlu ditindaklanjuti" per role:

| Role | Contoh label |
|---|---|
| Kepala Gudang | Permintaan Toko: *2 menunggu persetujuan* · Dashboard: *1 kritis, 1 perlu restock* · Stock Opname: *1 menunggu pemeriksaan* |
| Staff Gudang | Permintaan Toko: *1 siap dikirim* · Stock Opname: *1 ditolak* |
| Kepala Toko | Permintaan Barang: *1 perlu dikonfirmasi* |

## Test (`tests/test_insight.py`, 9 test)

| Test | Membuktikan |
|---|---|
| `test_contoh_readme_status_aman` | Semua angka contoh README |
| `test_contoh_readme_setelah_stok_turun_perlu_restock` | Tersedia 50 → Perlu restock, saran 70 |
| `test_stok_di_bawah_safety_stock_kritis_dan_dibulatkan_ke_atas` | Pembulatan ke atas (31,2 → 32) |
| `test_saran_restock_tidak_pernah_negatif` | Saran minimal 0 |
| `test_demand_tanpa_dibatalkan_dan_hanya_30_hari` | Data 40 hari lalu dan DIBATALKAN tidak dihitung |
| `test_fill_rate_ditolak_dihitung_nol_dibatalkan_tidak` | 270 ÷ 300 = 90% |
| `test_dashboard_hanya_untuk_kepala_gudang` | Staff Gudang mendapat 403 |

Total test sekarang **99**.

## Cek pemahaman

1. Kenapa permintaan DITOLAK ikut dihitung di demand, tetapi DIBATALKAN tidak?
2. Hitung sendiri: demand 300 dalam 30 hari, lead time 2 hari, tersedia 25. Berapa SS, ROP, saran restock, dan statusnya?
3. Jelaskan tiga tahap aggregation pipeline dengan bahasa sendiri.
4. Kenapa `rumus_produk()` sengaja dibuat tanpa database?

<details><summary>Jawaban nomor 2</summary>

Demand 10/hari · SS = 20 · ROP = 10 × 2 + 20 = 40 · Saran = 10 × 9 − 25 = 65 · 20 < 25 ≤ 40 → **Perlu restock**
</details>
