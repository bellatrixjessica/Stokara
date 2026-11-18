# Tahap 2 – Login dan Role

Tujuan tahap ini: memenuhi ketentuan **authentication**, **authorization**, **multi user / multi role**, dan awal **validasi & sanitasi**.

| Istilah | Pertanyaan yang dijawab | Di Stokara |
|---|---|---|
| Authentication | *Siapa kamu?* | Login dengan username + password, lalu disimpan di session |
| Authorization | *Kamu boleh melakukan ini?* | Setiap route dicek rolenya dengan `@wajib_login(...)` |

## File yang dibuat

| File | Lapisan | Isi |
|---|---|---|
| `app/models/user.py` | Model | Daftar 4 role, `buat_user()`, `cek_login()`, `data_publik()` |
| `app/utils/validasi.py` | Utilitas | `ValidasiError`, `ambil_json()`, `teks()` |
| `app/utils/auth.py` | Utilitas | Decorator `@wajib_login()` |
| `app/routes/auth.py` | Controller | `POST /api/login`, `POST /api/logout`, `GET /api/saya` |
| `scripts/seed_akun.py` | Script | Membuat 3 toko dan 6 akun contoh |
| `tests/test_auth.py` | Test | 15 test login, validasi, session, dan role |

## Empat role

| Role | Kode | Contoh akun |
|---|---|---|
| Admin | `admin` | `admin` |
| Kepala Gudang | `kepala_gudang` | `kepala.gudang` |
| Staff Gudang | `staff_gudang` | `staff.gudang` |
| Kepala Toko | `kepala_toko` | `toko.salatiga01`, `toko.ungaran01`, `toko.semarang01` |

Password semua akun contoh = `DEMO_PASSWORD` di `.env`. Kepala Toko punya `toko_id`, jadi nanti hanya bisa melihat permintaan tokonya sendiri.

## Alur login

```
Browser: POST /api/login {"username": "kepala.gudang", "password": "..."}
  │
  ├─ ambil_json()  → data harus JSON, hanya boleh key username & password   (gagal → 400)
  ├─ teks()        → username harus teks, wajib, maks 50 huruf               (gagal → 400)
  ├─ cek_login()   → cari user, cek aktif, cocokkan password dengan hash     (gagal → 401)
  └─ session["user_id"] = id user  → browser menyimpan cookie session
     ← {"pesan": "Login berhasil.", "redirect": "/beranda"}
```

## Alur saat membuka fitur yang dibatasi

```python
@bp.post("/api/permintaan/<id>/setujui")
@wajib_login(KEPALA_GUDANG)
def setujui(id):
    ...
```

Decorator adalah **pembungkus yang jalan sebelum fungsi route**:

```
Request masuk
  ├─ ambil user_id dari session → cari user di database
  │     tidak ada / nonaktif  → 401 "Silakan login terlebih dahulu."
  ├─ role user ada di daftar yang diizinkan?
  │     tidak                 → 403 "Anda tidak punya akses ke fitur ini."
  └─ ya → g.user = user, lalu fungsi setujui() dijalankan
```

`@wajib_login()` tanpa isi berarti *semua role yang sudah login*.

## Poin keamanan (bagus untuk presentasi)

| Ancaman | Pencegahan | Lokasi |
|---|---|---|
| Password bocor kalau database dicuri | Disimpan sebagai **hash scrypt**, bukan teks asli | `buat_user()` |
| Menebak username yang terdaftar | Pesan error **sama** untuk username salah dan password salah | `routes/auth.py` |
| NoSQL injection: `{"username": {"$ne": ""}}` | Nilai harus bertipe **teks**, objek ditolak | `teks()` |
| Menyelipkan field lain, misalnya `"role": "admin"` | Key yang tidak dikenal **ditolak** | `ambil_json()` |
| Cookie dicuri lewat JavaScript | `SESSION_COOKIE_HTTPONLY` | `config.py` |
| Cookie dikirim dari situs lain | `SESSION_COOKIE_SAMESITE = "Lax"` | `config.py` |
| Cookie disadap di jaringan | `SESSION_COOKIE_SECURE` (HTTPS di Vercel) | `config.py` |
| Akun dinonaktifkan tapi masih login | User **dibaca ulang dari database** di setiap request | `wajib_login()` |

Contoh percobaan injeksi pada aplikasi yang berjalan dengan Atlas:

```
login injeksi $ne   : 400 {'pesan': 'Username harus berupa teks.'}
```

## Test

```powershell
python -m pytest tests/test_auth.py -v
```

Test memakai database palsu yang di setiap test sudah berisi 1 toko dan 4 akun (lihat `tests/conftest.py`). Test `test_hanya_role_yang_diizinkan_bisa_akses` membuat route contoh khusus Admin, lalu membuktikan Kepala Toko mendapat 403 dan Admin mendapat 200.

## Keterbatasan (ditulis jujur di System Design)

- Belum ada pembatasan jumlah percobaan login (rate limiting).
- Belum ada fitur lupa password; password direset oleh Admin (tahap 4).

## Cek pemahaman

1. Apa beda 401 dan 403?
2. Kenapa password tidak disimpan apa adanya? Bagaimana `cek_login()` mencocokkannya?
3. Kenapa user dibaca ulang dari database di setiap request, bukan cukup dari session?
4. Apa yang terjadi kalau seseorang mengirim `{"username": {"$ne": ""}}`? Fungsi mana yang menolaknya?
