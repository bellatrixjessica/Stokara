"""Membuat data contoh 30 hari: supplier, produk, barang masuk, permintaan toko, dan opname.

Jalankan dari folder D:\\Stokara (setelah seed_akun.py):
    python scripts/seed_data.py            -> isi data contoh (hanya jika belum ada transaksi)
    python scripts/seed_data.py --reset    -> hapus semua transaksi lalu isi ulang (ada konfirmasi)

Data dibuat langsung ke database, tetapi mengikuti aturan bisnis yang sama dengan aplikasi:
- qty disetujui <= stok tersedia, tidak ada pengiriman sebagian, stok tidak pernah minus
- setiap perubahan stok tercatat di mutasi_stok (MASUK, KELUAR, ADJUST)
- angka acak memakai random.seed tetap, jadi hasilnya selalu sama setiap dijalankan
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.waktu import WIB  # noqa: E402

SUPPLIER = [
    ("SUP-01", "PT Sumber Pangan Jaya", "024-7601234", "Jl. Industri Raya 3, Semarang"),
    ("SUP-02", "CV Manis Abadi", "024-6581122", "Jl. Kaligawe 17, Semarang"),
    ("SUP-03", "CV Tirta Makmur", "024-6712345", "Jl. Raya Ungaran 21, Ungaran"),
    ("SUP-04", "PT Bersih Sentosa", "024-8442210", "Jl. Majapahit 120, Semarang"),
]

# kode, nama, kategori, satuan, supplier, lead time, (qty min, qty max per permintaan), stok awal, restock
PRODUK = [
    ("P-0001", "Minyak Goreng 1L", "Sembako", "PCS", "SUP-01", 2, (14, 34), 220, 150),
    ("P-0002", "Beras Premium 5kg", "Sembako", "PCS", "SUP-01", 3, (10, 26), 170, 115),
    ("P-0003", "Gula Pasir 1kg", "Sembako", "PCS", "SUP-02", 2, (12, 28), 190, 125),
    ("P-0004", "Mi Instan Goreng 85g", "Makanan", "KARTON", "SUP-01", 3, (12, 30), 150, 40),   # -> Perlu restock
    ("P-0005", "Air Mineral 600ml", "Minuman", "KARTON", "SUP-03", 2, (16, 40), 70, 30),     # -> Kritis
    ("P-0006", "Teh Kotak 200ml", "Minuman", "KARTON", "SUP-03", 2, (8, 20), 120, 80),
    ("P-0007", "Susu UHT 1L", "Minuman", "PCS", "SUP-03", 3, (8, 22), 130, 90),
    ("P-0008", "Kopi Sachet", "Minuman", "PACK", "SUP-02", 3, (10, 24), 150, 95),
    ("P-0009", "Sabun Mandi 85g", "Kebersihan", "PCS", "SUP-04", 4, (12, 28), 200, 120),
    ("P-0010", "Deterjen 800g", "Kebersihan", "PCS", "SUP-04", 4, (8, 20), 140, 85),
    ("P-0011", "Tisu Wajah", "Kebersihan", "PACK", "SUP-04", 3, (8, 20), 130, 80),
    ("P-0012", "Roti Tawar", "Makanan", "PCS", "SUP-02", 1, (10, 22), 110, 75),
]

HARI_RESTOCK = [22, 15, 8]   # hari ke berapa (dari sekarang) barang masuk mingguan datang
KOLEKSI_TRANSAKSI = ["barang_masuk", "permintaan", "mutasi_stok", "opname", "notifikasi"]


def pastikan_master(db, sekarang_utc):
    """Tambahkan supplier dan produk contoh yang belum ada (berdasarkan kode)."""
    for kode, nama, telepon, alamat in SUPPLIER:
        if not db.master_supplier.find_one({"kode": kode}):
            db.master_supplier.insert_one({"kode": kode, "nama": nama, "telepon": telepon, "alamat": alamat,
                                           "aktif": True, "dibuat": sekarang_utc})
    for kode, nama, kategori, satuan, sup, lead, *_ in PRODUK:
        if not db.master_produk.find_one({"kode": kode}):
            supplier = db.master_supplier.find_one({"kode": sup})
            db.master_produk.insert_one({"kode": kode, "nama": nama, "kategori": kategori, "satuan": satuan,
                                         "supplier_id": supplier["_id"], "lead_time_hari": lead, "stok": 0,
                                         "aktif": True, "dibuat": sekarang_utc})


def buat_data_contoh(db, sekarang_utc=None):
    """Isi transaksi 30 hari. Mengembalikan ringkasan jumlah dokumen yang dibuat."""
    acak = random.Random(2026)
    sekarang_utc = sekarang_utc or datetime.now(timezone.utc)
    hari_ini = sekarang_utc.astimezone(WIB).date()
    pastikan_master(db, sekarang_utc)

    kepala_gudang = db.users.find_one({"role": "kepala_gudang", "aktif": True})
    staff = db.users.find_one({"role": "staff_gudang", "aktif": True})
    toko_daftar = []
    for toko in db.master_toko.find({"aktif": True}).sort("kode", 1):
        kepala_toko = db.users.find_one({"role": "kepala_toko", "toko_id": toko["_id"], "aktif": True})
        if kepala_toko:
            toko_daftar.append((toko, kepala_toko))
    if not (kepala_gudang and staff and toko_daftar):
        raise RuntimeError("Akun belum lengkap. Jalankan dulu: python scripts/seed_akun.py")

    produk = {p["kode"]: p for p in db.master_produk.find({"kode": {"$in": [x[0] for x in PRODUK]}})}
    profil = {x[0]: x for x in PRODUK}
    stok = {kode: 0 for kode in produk}
    nomor_terakhir = {}
    dokumen = {nama: [] for nama in ["barang_masuk", "permintaan", "mutasi_stok", "opname"]}

    # ---------------------------------------------------------- bantuan
    def waktu(hari_lalu, jam, menit=0):
        """Waktu WIB pada hari tertentu, diubah ke UTC. Tidak pernah melewati waktu sekarang."""
        tanggal = hari_ini - timedelta(days=hari_lalu)
        hasil = datetime(tanggal.year, tanggal.month, tanggal.day, jam, menit, tzinfo=WIB).astimezone(timezone.utc)
        batas = sekarang_utc - timedelta(minutes=1)
        return hasil if hasil <= batas else batas - timedelta(minutes=acak.randint(1, 50))

    def nomor(awalan, saat):
        tanggal = saat.astimezone(WIB).strftime("%y%m%d")
        kunci = (awalan, tanggal)
        nomor_terakhir[kunci] = nomor_terakhir.get(kunci, 0) + 1
        return f"{awalan}-{tanggal}-{nomor_terakhir[kunci]:04d}"

    def oleh(user):
        return {"id": user["_id"], "nama": user["nama"]}

    def mutasi(kode, jenis, perubahan, referensi, keterangan, user, saat):
        stok[kode] += perubahan
        p = produk[kode]
        dokumen["mutasi_stok"].append({
            "produk_id": p["_id"], "kode": kode, "nama": p["nama"], "jenis": jenis, "perubahan": perubahan,
            "stok_sebelum": stok[kode] - perubahan, "stok_sesudah": stok[kode], "referensi": referensi,
            "keterangan": keterangan, "oleh": oleh(user), "waktu": saat,
        })

    def barang_masuk(hari_lalu, daftar_qty):
        """daftar_qty: {kode: qty}. Satu dokumen per supplier."""
        per_supplier = {}
        for kode, qty in daftar_qty.items():
            if qty > 0:
                per_supplier.setdefault(profil[kode][4], []).append((kode, qty))
        for i, (sup_kode, isi) in enumerate(sorted(per_supplier.items())):
            saat = waktu(hari_lalu, 7, 30 + i * 5)
            no = nomor("BM", saat)
            supplier = db.master_supplier.find_one({"kode": sup_kode})
            dokumen["barang_masuk"].append({
                "nomor": no, "supplier_id": supplier["_id"], "supplier": supplier["nama"],
                "no_surat_jalan": f"SJ-{sup_kode[-2:]}{saat.astimezone(WIB).strftime('%m%d')}",
                "catatan": "Stok awal" if hari_lalu == 29 else "",
                "items": [{"produk_id": produk[k]["_id"], "kode": k, "nama": produk[k]["nama"],
                           "satuan": produk[k]["satuan"], "qty": q} for k, q in isi],
                "oleh": oleh(staff), "dibuat": saat,
            })
            for kode, qty in isi:
                mutasi(kode, "MASUK", qty, no, "Barang masuk dari " + supplier["nama"], staff, saat)

    # ---------------------------------------------------------- simulasi per hari
    barang_masuk(29, {x[0]: x[7] for x in PRODUK})            # stok awal
    dipesan = {kode: 0 for kode in produk}                     # qty DISETUJUI belum dikirim
    jumlah_hari_ini = 0

    for hari_lalu in range(28, -1, -1):
        if hari_lalu in HARI_RESTOCK:
            barang_masuk(hari_lalu, {x[0]: x[8] for x in PRODUK})

        if hari_lalu == 12:  # stock opname: ada barang rusak/hilang
            saat = waktu(12, 16)
            hitung = {"P-0001": -2, "P-0009": -1, "P-0003": 0}
            items = []
            for kode, selisih in hitung.items():
                items.append({"produk_id": produk[kode]["_id"], "kode": kode, "nama": produk[kode]["nama"],
                              "satuan": produk[kode]["satuan"], "stok_sistem": stok[kode],
                              "stok_hitung": stok[kode] + selisih, "selisih": selisih})
            no = nomor("OPN", saat)
            dokumen["opname"].append({
                "nomor": no, "status": "DISETUJUI", "catatan": "Opname rak A dan C", "items": items,
                "dihitung_oleh": oleh(staff), "dibuat": saat, "diperiksa_oleh": oleh(kepala_gudang),
                "diperiksa": saat + timedelta(hours=1), "alasan_tolak": None,
            })
            for item in items:
                if item["selisih"]:
                    mutasi(item["kode"], "ADJUST", item["selisih"], no, "Stock opname " + no,
                           kepala_gudang, saat + timedelta(hours=1))

        for urutan, (toko, kepala_toko) in enumerate(toko_daftar):
            if acak.random() > 0.7:
                continue  # toko ini tidak meminta hari ini
            dibuat = waktu(hari_lalu, 8 + urutan, acak.randint(0, 50))
            kode_dipilih = acak.sample(sorted(produk), acak.randint(2, 4))
            items = []
            for kode in kode_dipilih:
                lo, hi = profil[kode][6]
                p = produk[kode]
                items.append({"produk_id": p["_id"], "kode": kode, "nama": p["nama"], "satuan": p["satuan"],
                              "qty_diminta": acak.randint(lo, hi), "qty_disetujui": None, "qty_dikirim": None})
            doc = {
                "nomor": nomor("PRM", dibuat), "toko_id": toko["_id"], "toko": toko["nama"], "status": "DIAJUKAN",
                "catatan": acak.choice(["", "", "Stok akhir pekan", "Untuk promo minggu ini"]), "items": items,
                "alasan_tolak": None, "diajukan_oleh": oleh(kepala_toko), "dibuat": dibuat, "diperbarui": dibuat,
                "riwayat": [{"status": "DIAJUKAN", "waktu": dibuat, "oleh": kepala_toko["nama"], "catatan": ""}],
            }
            dokumen["permintaan"].append(doc)

            def ubah(status, user, jam_ke, catatan=""):
                saat = min(dibuat + timedelta(hours=jam_ke), sekarang_utc - timedelta(minutes=1))
                doc["status"] = status
                doc["diperbarui"] = saat
                doc["riwayat"].append({"status": status, "waktu": saat, "oleh": user["nama"], "catatan": catatan})
                return saat

            if hari_lalu == 0:
                jumlah_hari_ini += 1
                if jumlah_hari_ini == 1:
                    continue  # permintaan pertama hari ini dibiarkan DIAJUKAN (menunggu persetujuan)

            if acak.random() < 0.06:
                ubah("DIBATALKAN", kepala_toko, 1)
                continue

            # Persetujuan: qty disetujui = terkecil antara diminta dan stok tersedia
            for item in items:
                tersedia = stok[item["kode"]] - dipesan[item["kode"]]
                item["qty_disetujui"] = max(0, min(item["qty_diminta"], tersedia))
            if sum(i["qty_disetujui"] for i in items) == 0 or acak.random() < 0.07:
                alasan = "Stok kosong, menunggu barang masuk" if sum(i["qty_disetujui"] for i in items) == 0 \
                    else "Armada pengiriman penuh hari ini"
                for item in items:
                    item["qty_disetujui"] = None
                doc["alasan_tolak"] = alasan
                ubah("DITOLAK", kepala_gudang, 1, alasan)
                continue
            ubah("DISETUJUI", kepala_gudang, 1)

            if hari_lalu == 0 and jumlah_hari_ini == 2:
                for item in items:   # permintaan kedua hari ini menunggu dikirim
                    dipesan[item["kode"]] += item["qty_disetujui"]
                continue

            # Pengiriman: qty dikirim = qty disetujui (tidak ada pengiriman sebagian)
            saat_kirim = ubah("DIKIRIM", staff, 2)
            for item in items:
                item["qty_dikirim"] = item["qty_disetujui"]
                if item["qty_dikirim"] > 0:
                    mutasi(item["kode"], "KELUAR", -item["qty_dikirim"], doc["nomor"], "Dikirim ke " + toko["nama"],
                           staff, saat_kirim)
            if hari_lalu >= 2:
                ubah("DITERIMA", kepala_toko, 26)

    # ---------------------------------------------------------- simpan ke database
    for nama, isi in dokumen.items():
        if isi:
            db[nama].insert_many(isi)
    for kode, jumlah in stok.items():
        db.master_produk.update_one({"kode": kode}, {"$set": {"stok": jumlah}})
    return {nama: len(isi) for nama, isi in dokumen.items()}


def ada_transaksi(db):
    return any(db[nama].count_documents({}) for nama in KOLEKSI_TRANSAKSI)


def hapus_transaksi(db):
    for nama in KOLEKSI_TRANSAKSI:
        db[nama].delete_many({})
    db.master_produk.update_many({}, {"$set": {"stok": 0}})


if __name__ == "__main__":
    from app import create_app
    from app.models import insight

    app = create_app()
    with app.app_context():
        db = app.db
        if "--reset" in sys.argv:
            jawaban = input("Semua transaksi (barang masuk, permintaan, mutasi, opname, notifikasi) akan DIHAPUS.\n"
                            "Ketik HAPUS untuk melanjutkan: ")
            if jawaban.strip() != "HAPUS":
                print("Dibatalkan.")
                sys.exit(0)
            hapus_transaksi(db)
        elif ada_transaksi(db):
            print("Database sudah berisi transaksi. Pakai --reset untuk menghapus lalu mengisi ulang.")
            sys.exit(1)

        ringkasan = buat_data_contoh(db)
        for nama, jumlah in ringkasan.items():
            print(f"  {nama:14}: {jumlah} dokumen")

        data = insight.dashboard()
        print(f"\nFill rate 30 hari : {data['fill_rate']['persen']}%")
        print(f"Stok kritis       : {data['ringkasan']['kritis']}")
        print(f"Perlu restock     : {data['ringkasan']['perlu_restock']}")
        print(f"Menunggu setuju   : {data['ringkasan']['menunggu_persetujuan']}, menunggu kirim: "
              f"{data['ringkasan']['menunggu_kirim']}")
