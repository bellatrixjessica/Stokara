# Tahap 3 – Tampilan Webix

Tujuan tahap ini: kerangka tampilan sesuai mockup (login, header, sidebar, beranda, halaman error), memenuhi ketentuan **Webix** dan **responsive UI**.

## Pembagian tugas Jinja, Webix, dan CSS

| Bagian | Tugas | File |
|---|---|---|
| **Jinja** (Python) | Menyiapkan "panggung": memuat Webix, CSS, dan **mengirim data awal** dari server ke JavaScript | `templates/*.html` |
| **Webix** (JavaScript) | Membuat **seluruh tampilan**: form login, header, sidebar, kartu, tabel (nanti) | `static/js/*.js` |
| **CSS** | Memberi **warna, sudut, bayangan, huruf** sesuai logo Stokara. Ukuran dan posisi tetap diatur Webix | `static/css/app.css` |

Analogi: Jinja menyiapkan panggung dan naskah, Webix adalah para pemain, CSS adalah kostumnya.

## Alur saat membuka `/beranda`

```
1. Browser  GET /beranda
2. Flask    @wajib_login() → sudah login?  belum → redirect /login
3. Flask    render_halaman("beranda.js", "Beranda", "beranda")
               → menyiapkan DATA = {pengguna, menu sesuai role, aktif, branch}
4. Jinja    halaman.html:
               <script>const DATA = {...};</script>     ← data dari Python
               <script src="layout.js">                  ← kerangka header + sidebar
               <script src="beranda.js">                 ← isi halaman
5. Webix    beranda.js memanggil tampilkanHalaman({...isi...})
               → layout.js menggabungkan header + sidebar + isi menjadi satu tampilan
```

## File yang dibuat

| File | Isi |
|---|---|
| `app/utils/tampilan.py` | Daftar `MENU` beserta role yang boleh melihatnya, `menu_untuk(role)`, `render_halaman()`, `halaman_error()` |
| `app/routes/umum.py` | `/` → login atau beranda, `/login`, `/beranda` |
| `templates/base.html` | Memuat Webix 11.4 (skin Willow), ikon MDI, `app.css`, `app.js` |
| `templates/login.html` | Halaman login (memuat `login.js`) |
| `templates/halaman.html` | Semua halaman setelah login: mengirim `DATA`, memuat `layout.js` + JS halaman |
| `templates/error.html` | Halaman 403/404/500, cukup Jinja + CSS |
| `static/css/app.css` | Warna Stokara untuk komponen Webix |
| `static/js/app.js` | Fungsi bantu: `api()`, `aman()`, `angka()`, `rupiah()` |
| `static/js/layout.js` | `tampilkanHalaman()`, header, sidebar, `judulHalaman()`, `keluar()` |
| `static/js/login.js` | Form login Webix |
| `static/js/beranda.js` | Kartu sambutan + kartu menu |
| `tests/test_tampilan.py` | 12 test menu per role, halaman, dan error |

## Komponen Webix yang dipakai

| Komponen | Dipakai untuk |
|---|---|
| `toolbar` | Header: tombol menu, logo, nama pengguna, tombol Keluar |
| `sidebar` | Menu kiri; di ponsel otomatis hanya ikon (`collapsed`) |
| `form`, `text`, `button` | Form login, dengan validasi wajib isi (`required`) |
| `template` | Panel ungu login, kartu sambutan, label |
| `dataview` | Kartu menu di beranda (`xCount` = jumlah kartu per baris) |
| `webix.message` | Pesan error, misalnya "Username atau password salah." |

## Menu per role

Menu ditentukan **di server** (`MENU` di `tampilan.py`), bukan di JavaScript. Browser hanya menerima menu yang boleh dilihat rolenya.

| Role | Menu |
|---|---|
| Admin | Beranda, Produk, Toko, Supplier, Karyawan |
| Kepala Gudang | Beranda, Dashboard, Permintaan Toko, Stok Gudang, Barang Masuk, Stock Opname, Laporan |
| Staff Gudang | Beranda, Permintaan Toko, Stok Gudang, Barang Masuk, Stock Opname |
| Kepala Toko | Beranda, Permintaan Barang, Laporan |

Menyembunyikan menu **bukan** pengamanan. Pengamanannya tetap `@wajib_login(...)` di setiap route. Kalau Kepala Toko mengetik `/dashboard` langsung, server menolak dengan 403.

## Responsive

`app.js` mengecek lebar layar satu kali: `const LAYAR_KECIL = window.innerWidth < 768;`

| | Laptop | Ponsel |
|---|---|---|
| Login | Panel ungu kiri + form kanan | Panel ungu pendek di atas, form di bawah |
| Sidebar | Lebar 220 px, ada tulisan | Hanya ikon |
| Header | Logo, branch, nama + role, tombol Keluar | Logo, inisial, ikon keluar |
| Kartu beranda | 3 per baris | 1 per baris |

Keterbatasan: kalau jendela browser diubah ukurannya setelah halaman terbuka, tata letak baru menyesuaikan setelah halaman di-refresh.

## Keamanan tampilan (XSS)

Semua teks dari database ditampilkan lewat `aman()`:

```js
"<b>" + aman(p.nama) + "</b>"
```

Kalau ada nama karyawan berisi `<script>...</script>`, teks itu ditampilkan apa adanya, tidak dijalankan sebagai kode. Data dari Flask ke JavaScript dikirim dengan filter `tojson`, yang juga meng-escape karakter berbahaya.

## Penyesuaian warna Webix

Skin Willow punya warna biru bawaan. Contoh: garis penanda menu aktif awalnya biru. Supaya menjadi kuning (amber) Stokara, aturan CSS ditulis **lebih spesifik** dari aturan Willow:

```css
.app-sidebar.webix_sidebar .webix_tree_item.webix_selected {
  box-shadow: inset 3px 0 0 var(--amber);
}
```

## Cek pemahaman

1. Apa tugas Jinja di halaman beranda? Apa tugas Webix?
2. Dari mana `beranda.js` tahu nama pengguna yang sedang login?
3. Kepala Toko tidak melihat menu Dashboard. Apakah itu sudah cukup aman? Kenapa?
4. Kenapa nama pengguna ditampilkan dengan `aman(p.nama)`, bukan `p.nama` langsung?
