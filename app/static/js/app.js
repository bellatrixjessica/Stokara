const LAYAR_KECIL = window.innerWidth < 768;

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
    window.location.href = "/login";
    return null;
  }
  if (!respon.ok) {
    webix.message({ type: "error", text: aman(hasil.pesan || "Terjadi kesalahan. Silakan coba lagi.") });
    return null;
  }
  return hasil;
}

function aman(teks) {
  return webix.template.escape(teks === null || teks === undefined ? "" : String(teks));
}

function berhasil(pesan) {
  webix.message({ type: "success", text: aman(pesan) });
}

function konfirmasi(judul, teks) {
  return webix
    .confirm({ title: aman(judul), text: aman(teks), ok: "Ya", cancel: "Batal", width: 380 })
    .then(() => true)
    .catch(() => false);
}

function mintaTeks(judul, teks, contoh) {
  return webix
    .prompt({
      title: aman(judul), text: aman(teks), ok: "Kirim", cancel: "Batal", width: 420,
      input: { required: true, placeholder: contoh || "" },
    })
    .then((nilai) => nilai.trim() || null)
    .catch(() => null);
}

function badgeStatus(baris) {
  return baris.aktif
    ? '<span class="badge b-hijau">Aktif</span>'
    : '<span class="badge b-abu">Nonaktif</span>';
}

function angka(n) {
  return Number(n).toLocaleString("id-ID");
}

function desimal(n) {
  return Number(n).toLocaleString("id-ID", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function rupiah(n) {
  return "Rp " + angka(n);
}

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

function tanggal(iso) {
  if (!iso) return "–";
  return new Date(iso).toLocaleDateString("id-ID", { timeZone: "Asia/Jakarta", day: "numeric", month: "short", year: "numeric" });
}

function perubahan(n) {
  if (n > 0) return '<span class="naik">+' + angka(n) + "</span>";
  if (n < 0) return '<span class="turun">−' + angka(-n) + "</span>";
  return "0";
}
