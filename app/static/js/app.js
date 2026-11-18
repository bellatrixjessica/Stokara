/* =====================================================================
 * Fungsi bantu yang dipakai semua halaman Stokara.
 * ===================================================================== */

// Ponsel atau layar sempit (dicek sekali saat halaman dibuka).
const LAYAR_KECIL = window.innerWidth < 768;

// Bahasa Indonesia untuk kalender Webix dan nomor halaman di PDF unduhan.
Object.assign(webix.i18n.calendar, {
  monthFull: ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
  monthShort: ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"],
  dayFull: ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"],
  dayShort: ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"],
  today: "Hari ini",
  clear: "Hapus",
});
webix.i18n.dataExport.page = "Halaman";
webix.i18n.dataExport.of = "dari";
webix.i18n.setLocale();

/**
 * Kirim atau ambil data JSON dari server.
 * Contoh: const saya = await api("GET", "/api/saya");
 *         const hasil = await api("POST", "/api/master/toko", { kode: "TK-04", ... });
 *
 * Berhasil -> mengembalikan data dari server.
 * Gagal    -> pesan error dari server ditampilkan, lalu mengembalikan null.
 *             Jadi di halaman cukup dicek:  if (!hasil) return;
 */
async function api(metode, url, data) {
  const opsi = { method: metode, headers: { "Content-Type": "application/json" } };
  if (data !== undefined) {
    opsi.body = JSON.stringify(data);
  }

  let respon;
  try {
    respon = await fetch(url, opsi);
  } catch (e) {
    webix.message({ type: "error", text: "Tidak bisa terhubung ke server. Periksa koneksi internet." });
    return null;
  }
  const hasil = await respon.json().catch(() => ({}));

  if (respon.status === 401 && url !== "/api/login") {
    window.location.href = "/login"; // session habis, login ulang
    return null;
  }
  if (!respon.ok) {
    webix.message({ type: "error", text: aman(hasil.pesan || "Terjadi kesalahan. Silakan coba lagi.") });
    return null;
  }
  return hasil;
}

/**
 * Ubah teks menjadi aman untuk ditampilkan di HTML.
 * Contoh: nama "<script>" ditampilkan sebagai teks biasa, bukan dijalankan (mencegah XSS).
 */
function aman(teks) {
  return webix.template.escape(teks === null || teks === undefined ? "" : String(teks));
}

// Pesan hijau di pojok kanan atas, contoh: "Toko berhasil ditambahkan."
function berhasil(pesan) {
  webix.message({ type: "success", text: aman(pesan) });
}

/**
 * Dialog konfirmasi "Ya / Batal".
 * Contoh: if (!(await konfirmasi("Nonaktifkan toko?", "Toko tidak bisa ..."))) return;
 */
function konfirmasi(judul, teks) {
  return webix
    .confirm({ title: aman(judul), text: aman(teks), ok: "Ya", cancel: "Batal", width: 380 })
    .then(() => true)
    .catch(() => false);
}

/**
 * Dialog yang meminta pengguna mengetik teks, contoh alasan penolakan.
 * Mengembalikan teks yang diketik, atau null kalau pengguna menekan Batal.
 */
function mintaTeks(judul, teks, contoh) {
  return webix
    .prompt({
      title: aman(judul), text: aman(teks), ok: "Kirim", cancel: "Batal", width: 420,
      input: { required: true, placeholder: contoh || "" },
    })
    .then((nilai) => nilai.trim() || null)
    .catch(() => null);
}

// Label status Aktif (hijau) / Nonaktif (abu-abu), dipakai di kolom tabel.
function badgeStatus(baris) {
  return baris.aktif
    ? '<span class="badge b-hijau">Aktif</span>'
    : '<span class="badge b-abu">Nonaktif</span>';
}

// Format angka Indonesia: 1558 -> "1.558"
function angka(n) {
  return Number(n).toLocaleString("id-ID");
}

// Angka dengan satu desimal: 15.6 -> "15,6"
function desimal(n) {
  return Number(n).toLocaleString("id-ID", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

// Format Rupiah: 15000 -> "Rp 15.000"
function rupiah(n) {
  return "Rp " + angka(n);
}

/**
 * Waktu dari server (UTC) ditampilkan dalam WIB.
 * "2026-11-19T02:15:00+00:00" -> "19 Nov 2026 09.15"
 */
function tanggalWaktu(iso) {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("id-ID", {
    timeZone: "Asia/Jakarta",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Tanggal saja (WIB): "2026-11-19T02:15:00+00:00" -> "19 Nov 2026"
function tanggal(iso) {
  if (!iso) return "–";
  return new Date(iso).toLocaleDateString("id-ID", { timeZone: "Asia/Jakarta", day: "numeric", month: "short", year: "numeric" });
}

// Angka perubahan stok dengan tanda: 40 -> "+40", -5 -> "−5"
function perubahan(n) {
  if (n > 0) return '<span class="naik">+' + angka(n) + "</span>";
  if (n < 0) return '<span class="turun">−' + angka(-n) + "</span>";
  return "0";
}
