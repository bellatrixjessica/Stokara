# Tahap 11 – Dokumentasi Teknis

Tujuan tahap ini: memenuhi ketentuan **dokumentasi teknis (SRS, System Design)** dan membuat README yang cukup untuk menjalankan Stokara dari nol.

## Tiga dokumen, tiga pertanyaan

| Dokumen | Menjawab | Pembaca |
|---|---|---|
| [README](../../README.md) | *Bagaimana menjalankannya?* Fitur singkat, rumus + contoh angka, setup, akun contoh, test | Penguji yang membuka GitHub |
| [SRS](../SRS.md) | *Apa yang harus dilakukan sistem?* Role, kebutuhan fungsional (FR), aturan bisnis (BR), non-fungsional (NFR) | Dosen/penguji, pemilik proses bisnis |
| [System Design](../SYSTEM-DESIGN.md) | *Bagaimana sistem dibangun?* Arsitektur, MVC, database + index, API, keamanan, deploy | Programmer, penguji teknis |

Aturan sederhananya: **SRS tidak menyebut nama file kode**, System Design boleh. Contoh: SRS menulis "stok tidak pernah negatif" (BR-07); System Design menjelaskan caranya (`find_one_and_update` dengan `$gte` di `models/stok.py`).

## Isi penting

**SRS**
- Kebutuhan diberi kode (`FR-35`, `BR-04`, `NFR-05`) supaya bisa dirujuk saat presentasi, contoh: "BR-04: tidak ada pengiriman sebagian".
- Bagian 7 **ketertelusuran**: setiap kelompok kebutuhan ditunjukkan test yang membuktikannya.
- Bagian 8 memetakan ketentuan tugas ke bagian dokumen.

**System Design**
- 4 diagram Mermaid: arsitektur, alur satu request (sequence), relasi collection (ER), deploy. SRS punya 2: use case dan status permintaan. GitHub menampilkannya sebagai gambar secara otomatis.
- Bagian 7.3 tabel **ancaman → pencegahan → lokasi kode**, untuk sesi tanya jawab keamanan.
- Bagian 12 **keputusan desain dan alasannya**, untuk menjawab "kenapa begini, bukan begitu?".
- Bagian 13 **keterbatasan yang jujur** beserta rencana pengembangannya, termasuk belum adanya transaksi multi-dokumen MongoDB.

## Pemeriksaan

- Semua angka di dokumen dicocokkan dengan kode: 13 blueprint, 9 collection, 13 index, 127 test, daftar API dari `app.url_map`.
- Keenam diagram Mermaid dirender dengan Mermaid 11 tanpa error.
- Password demo **tidak** ditulis di dokumen mana pun; README menyebut password diberikan terpisah.

## Cek pemahaman

1. Apa beda SRS dan System Design? Beri satu contoh kebutuhan dan cara pembuatannya.
2. Kenapa kebutuhan diberi kode seperti FR-35?
3. Sebutkan dua keterbatasan Stokara dan cara mengembangkannya.
4. Kenapa diagram relasi menunjukkan `items` sebagai array di dalam dokumen, bukan collection sendiri?
