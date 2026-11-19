const KEPALA_GUDANG = DATA.pengguna.role === "kepala_gudang";
const UBAH_TANGGAL = webix.Date.dateToStr("%Y-%m-%d");
let laporan = null;

const LABEL_JENIS_MUTASI = { MASUK: "Masuk", KELUAR: "Keluar", ADJUST: "Penyesuaian" };
const CSS_JENIS_MUTASI = { MASUK: "b-hijau", KELUAR: "b-oranye", ADJUST: "b-ungu" };
const LABEL_INSIGHT = { KRITIS: "Kritis", PERLU_RESTOCK: "Perlu restock", AMAN: "Aman", TANPA_PERMINTAAN: "Tidak ada permintaan" };
const CSS_INSIGHT = { KRITIS: "b-merah", PERLU_RESTOCK: "b-oranye", AMAN: "b-hijau", TANPA_PERMINTAAN: "b-abu" };

function kolomAngka(id, judul, lebar, isi) {
  return { id: id, header: { text: judul, css: "kanan" }, css: "kanan", width: lebar, template: isi };
}

function teksFillRate(b) {
  if (b.fill_rate !== null) return desimal(b.fill_rate) + "%";
  return b.status === "DIBATALKAN" ? "tidak dihitung" : "belum selesai";
}

const KOLOM = {
  permintaan: {
    tabel: [
      {
        id: "nomor", header: "Nomor", minWidth: LAYAR_KECIL ? 100 : 150, fillspace: !KEPALA_GUDANG || LAYAR_KECIL, css: "dua-baris",
        template: (b) => aman(b.nomor) + (LAYAR_KECIL && KEPALA_GUDANG ? '<span class="kecil">' + aman(b.toko) + "</span>" : ""),
      },
      { id: "toko", header: "Toko", fillspace: 1, minWidth: 150, template: "#!toko#", hidden: !KEPALA_GUDANG || LAYAR_KECIL },
      { id: "dibuat", header: "Diajukan", width: 120, template: (b) => tanggal(b.dibuat), hidden: LAYAR_KECIL },
      { id: "status", header: "Status", width: LAYAR_KECIL ? 100 : 115, template: (b) => labelStatus(b.status) },
      Object.assign(kolomAngka("diminta", "Diminta", 85, (b) => angka(b.diminta)), { hidden: LAYAR_KECIL }),
      Object.assign(kolomAngka("disetujui", "Disetujui", 95, (b) => angkaAtauStrip(b.disetujui)), { hidden: LAYAR_KECIL }),
      Object.assign(kolomAngka("dikirim", "Dikirim", 85, (b) => angkaAtauStrip(b.dikirim)), { hidden: LAYAR_KECIL }),
      kolomAngka("fill_rate", "Fill rate", LAYAR_KECIL ? 80 : 110, (b) =>
        b.fill_rate === null ? '<span class="kecil" style="display:inline">' + teksFillRate(b) + "</span>"
          : b.fill_rate < 85 ? '<b class="turun">' + teksFillRate(b) + "</b>" : teksFillRate(b)),
    ],
    ekspor: [
      { id: "nomor", header: "Nomor", width: 115 },
      { id: "toko", header: "Toko", width: 175 },
      { id: "dibuat", header: "Diajukan", width: 95, template: (b) => tanggal(b.dibuat) },
      { id: "status", header: "Status", width: 75, template: (b) => STATUS_PERMINTAAN[b.status].label },
      { id: "diminta", header: "Diminta", width: 60, exportType: "number" },
      { id: "disetujui", header: "Disetujui", width: 65, exportType: "number", template: (b) => (b.disetujui === null ? "" : b.disetujui) },
      { id: "dikirim", header: "Dikirim", width: 60, exportType: "number", template: (b) => (b.dikirim === null ? "" : b.dikirim) },
      { id: "fill_rate", header: "Fill rate", width: 95, template: teksFillRate },
    ],
  },

  mutasi: {
    tabel: [
      { id: "waktu", header: "Waktu", width: 160, template: (b) => tanggalWaktu(b.waktu), hidden: LAYAR_KECIL },
      { id: "nama", header: "Produk", fillspace: 1, minWidth: 150, css: "dua-baris", template: (b) => aman(b.nama) + '<span class="kecil">' + aman(b.kode) + (LAYAR_KECIL ? " · " + tanggalWaktu(b.waktu) : "") + "</span>" },
      { id: "jenis", header: "Jenis", width: 120, template: (b) => '<span class="badge ' + CSS_JENIS_MUTASI[b.jenis] + '">' + LABEL_JENIS_MUTASI[b.jenis] + "</span>", hidden: LAYAR_KECIL },
      kolomAngka("perubahan", "Perubahan", 105, (b) => perubahan(b.perubahan)),
      Object.assign(kolomAngka("stok_sesudah", "Stok akhir", 100, (b) => angka(b.stok_sesudah)), { hidden: LAYAR_KECIL }),
      { id: "referensi", header: "Referensi", width: 200, css: "dua-baris", template: (b) => aman(b.referensi) + '<span class="kecil">' + aman(b.oleh) + "</span>", hidden: LAYAR_KECIL },
    ],
    ekspor: [
      { id: "waktu", header: "Waktu", width: 125, template: (b) => tanggalWaktu(b.waktu) },
      { id: "kode", header: "Kode", width: 55 },
      { id: "nama", header: "Produk", width: 135 },
      { id: "jenis", header: "Jenis", width: 80, template: (b) => LABEL_JENIS_MUTASI[b.jenis] },
      { id: "perubahan", header: "Perubahan", width: 70, exportType: "number" },
      { id: "stok_sesudah", header: "Stok akhir", width: 70, exportType: "number" },
      { id: "referensi", header: "Referensi", width: 110 },
      { id: "oleh", header: "Oleh", width: 125 },
    ],
  },

  "barang-masuk": {
    tabel: [
      { id: "dibuat", header: "Tanggal", width: 120, template: (b) => tanggal(b.dibuat), hidden: LAYAR_KECIL },
      { id: "nomor", header: "Nomor", width: 170, hidden: LAYAR_KECIL, css: "dua-baris", template: (b) => aman(b.nomor) + '<span class="kecil">' + aman(b.no_surat_jalan) + "</span>" },
      { id: "supplier", header: "Supplier", width: 200, template: "#!supplier#", hidden: LAYAR_KECIL },
      { id: "nama", header: "Produk", fillspace: 1, minWidth: 150, css: "dua-baris", template: (b) => aman(b.nama) + '<span class="kecil">' + aman(b.kode) + (LAYAR_KECIL ? " · " + tanggal(b.dibuat) : "") + "</span>" },
      kolomAngka("qty", "Qty", 110, (b) => angka(b.qty) + " " + aman(b.satuan)),
    ],
    ekspor: [
      { id: "dibuat", header: "Tanggal", width: 95, template: (b) => tanggal(b.dibuat) },
      { id: "nomor", header: "Nomor", width: 105 },
      { id: "no_surat_jalan", header: "No. surat jalan", width: 90 },
      { id: "supplier", header: "Supplier", width: 145 },
      { id: "kode", header: "Kode", width: 55 },
      { id: "nama", header: "Produk", width: 150 },
      { id: "qty", header: "Qty", width: 50, exportType: "number" },
      { id: "satuan", header: "Satuan", width: 55 },
    ],
  },

  restock: {
    tabel: [
      { id: "status", header: "Status", width: LAYAR_KECIL ? 95 : 160, template: (b) => '<span class="badge ' + CSS_INSIGHT[b.status] + '">' + LABEL_INSIGHT[b.status] + "</span>" },
      { id: "nama", header: "Produk", fillspace: 1, minWidth: 100, css: "dua-baris", template: (b) => aman(b.nama) + '<span class="kecil">' + aman(b.kode) + " · lead time " + b.lead_time_hari + " hari</span>" },
      Object.assign(kolomAngka("tersedia", "Tersedia", 90, (b) => angka(b.tersedia)), { hidden: LAYAR_KECIL }),
      Object.assign(kolomAngka("demand_per_hari", "Demand/hari", 110, (b) => desimal(b.demand_per_hari)), { hidden: LAYAR_KECIL }),
      Object.assign(kolomAngka("safety_stock", "Safety stock", 120, (b) => angka(b.safety_stock)), { hidden: LAYAR_KECIL }),
      Object.assign(kolomAngka("reorder_point", "ROP", 70, (b) => angka(b.reorder_point)), { hidden: LAYAR_KECIL }),
      kolomAngka("saran_restock", LAYAR_KECIL ? "Saran" : "Saran restock", LAYAR_KECIL ? 90 : 130, (b) => ["KRITIS", "PERLU_RESTOCK"].includes(b.status)
        ? "<b>" + angka(b.saran_restock) + " " + aman(b.satuan) + "</b>"
        : '<span class="kecil" style="display:inline">' + angka(b.saran_restock) + " " + aman(b.satuan) + "</span>"),
    ],
    ekspor: [
      { id: "kode", header: "Kode", width: 55 },
      { id: "nama", header: "Produk", width: 135 },
      { id: "status", header: "Status", width: 85, template: (b) => LABEL_INSIGHT[b.status] },
      { id: "tersedia", header: "Tersedia", width: 60, exportType: "number" },
      { id: "demand_per_hari", header: "Demand/hari", width: 75, exportType: "number" },
      { id: "safety_stock", header: "SS", width: 45, exportType: "number" },
      { id: "reorder_point", header: "ROP", width: 45, exportType: "number" },
      { id: "lead_time_hari", header: "Lead time", width: 65, exportType: "number" },
      { id: "habis_dalam", header: "Habis (hari)", width: 75, exportType: "number", template: (b) => (b.habis_dalam === null ? "" : b.habis_dalam) },
      { id: "saran_restock", header: "Saran", width: 55, exportType: "number" },
      { id: "satuan", header: "Satuan", width: 60 },
    ],
  },
};

webix.ready(function () {
  const hariIni = new Date();
  const awal = webix.Date.add(hariIni, -29, "day", true);

  const pilihJenis = {
    view: LAYAR_KECIL ? "richselect" : "segmented", id: "jenis", value: "permintaan",
    label: LAYAR_KECIL ? "Jenis laporan" : "", labelPosition: LAYAR_KECIL ? "top" : "left", labelWidth: LAYAR_KECIL ? 80 : 0,
    options: [
      { id: "permintaan", value: "Permintaan Toko" },
      { id: "mutasi", value: "Mutasi Stok" },
      { id: "barang-masuk", value: "Barang Masuk" },
      { id: "restock", value: "Saran Restock" },
    ],
    on: { onChange: gantiJenis },
  };

  const tanggalDari = { view: "datepicker", id: "dari", label: "Dari tanggal", labelPosition: "top", value: awal, format: "%d %M %Y", width: LAYAR_KECIL ? 0 : 160 };
  const tanggalSampai = { view: "datepicker", id: "sampai", label: "Sampai tanggal", labelPosition: "top", value: hariIni, format: "%d %M %Y", width: LAYAR_KECIL ? 0 : 160 };
  const pilihToko = {
    view: "richselect", id: "toko", label: "Toko", labelPosition: "top", width: LAYAR_KECIL ? 0 : 220, value: "semua",
    hidden: !KEPALA_GUDANG,
    options: [{ id: "semua", value: "Semua toko" }].concat(DATA.toko || []),
  };
  const tombolTampilkan = { view: "button", value: "Tampilkan", css: "webix_primary", width: LAYAR_KECIL ? 0 : 110, click: muatLaporan };
  const tombolUnduh = [
    { view: "button", id: "unduhExcel", type: "icon", icon: "mdi mdi-microsoft-excel", label: LAYAR_KECIL ? "Excel" : "Unduh Excel", css: "tombol-garis", width: LAYAR_KECIL ? 0 : 130, click: unduhExcel, disabled: true },
    { view: "button", id: "unduhPdf", type: "icon", icon: "mdi mdi-file-pdf-box", label: LAYAR_KECIL ? "PDF" : "Unduh PDF", css: "tombol-garis", width: LAYAR_KECIL ? 0 : 120, click: unduhPdf, disabled: true },
  ];

  const barisFilter = LAYAR_KECIL
    ? { rows: [{ cols: [tanggalDari, tanggalSampai], margin: 10 }, pilihToko, { cols: [tombolTampilkan].concat(tombolUnduh), margin: 8 }], margin: 10 }
    : { cols: [tanggalDari, tanggalSampai, pilihToko, { rows: [{}, tombolTampilkan] }, {}, { rows: [{}, { cols: tombolUnduh, margin: 8 }] }], margin: 12 };

  const kartuFilter = {
    css: "kartu-panel",
    padding: 14,
    rows: [
      { hidden: !KEPALA_GUDANG, cols: LAYAR_KECIL ? [pilihJenis] : [Object.assign(pilihJenis, { width: 560 }), {}] },
      { height: KEPALA_GUDANG ? 12 : 0 },
      { view: "form", id: "formFilter", borderless: true, padding: 0, elements: [barisFilter] },
      { height: 14 },
      { view: "template", id: "ringkasan", css: "ringkasan-laporan", borderless: true, autoheight: true, template: "" },
    ],
  };

  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    rowHeight: 50,
    scroll: LAYAR_KECIL ? "xy" : "y",
    columns: KOLOM.permintaan.tabel,
    pager: "halaman",
  };

  const pager = {
    view: "pager", id: "halaman", size: 15, group: 5, height: 46,
    template: (data, common) => '<span class="kecil" style="display:inline">' + infoHalaman(data) + "</span> " + common.prev(data) + common.pages(data) + common.next(data),
  };

  tampilkanHalaman({
    view: "scrollview",
    scroll: "y",
    body: {
      rows: [
        judulHalaman(KEPALA_GUDANG ? "Laporan" : "Laporan Permintaan",
          KEPALA_GUDANG ? "Rekap data gudang untuk periode tertentu. Pilih laporan dan periode, lalu tampilkan atau unduh."
            : "Rekap permintaan toko Anda untuk periode tertentu, bisa diunduh sebagai Excel atau PDF."),
        kartuFilter,
        { height: 14 },
        { css: "kartu-tabel", height: 15 * 50 + 50 + 46, rows: [tabel, pager] },
      ],
    },
  });

  muatLaporan();
});

function infoHalaman(data) {
  if (!data.count) return "Tidak ada data pada periode ini";
  const dari = data.page * data.size + 1;
  const sampai = Math.min(data.count, dari + data.size - 1);
  return "Menampilkan " + dari + "–" + sampai + " dari " + angka(data.count) + " baris";
}

function gantiJenis() {
  const jenis = $$("jenis").getValue();
  const pakaiTanggal = jenis !== "restock";
  ["dari", "sampai"].forEach((id) => (pakaiTanggal ? $$(id).enable() : $$(id).disable()));
  if (KEPALA_GUDANG) {
    jenis === "permintaan" ? $$("toko").show() : $$("toko").hide();
  }
  $$("tabel").clearAll();
  $$("tabel").refreshColumns(KOLOM[jenis].tabel);
  muatLaporan();
}

async function muatLaporan() {
  const jenis = $$("jenis").getValue();
  const parameter = new URLSearchParams();
  if (jenis !== "restock") {
    const dari = $$("dari").getValue();
    const sampai = $$("sampai").getValue();
    if (!dari || !sampai) {
      webix.message({ type: "error", text: "Isi tanggal awal dan tanggal akhir." });
      return;
    }
    parameter.set("dari", UBAH_TANGGAL(dari));
    parameter.set("sampai", UBAH_TANGGAL(sampai));
  }
  if (jenis === "permintaan" && KEPALA_GUDANG && $$("toko").getValue() !== "semua") {
    parameter.set("toko", $$("toko").getValue());
  }

  const data = await api("GET", "/api/laporan/" + jenis + "?" + parameter.toString());
  if (!data || jenis !== $$("jenis").getValue()) return;
  laporan = data;

  isiRingkasan(data);
  $$("tabel").clearAll();
  $$("tabel").parse(data.baris);
  $$("tabel").setPage(0);
  const adaData = data.baris.length > 0;
  [$$("unduhExcel"), $$("unduhPdf")].forEach((b) => (adaData ? b.enable() : b.disable()));
}

function nilaiRingkasan(r) {
  if (r.nilai === null) return "–";
  return r.persen ? desimal(r.nilai) + "%" : angka(r.nilai);
}

function isiRingkasan(data) {
  const kotak = data.ringkasan.map((r) =>
    '<div class="ringkasan-kotak"><b>' + nilaiRingkasan(r) + "</b><span>" + aman(r.label) + "</span>" +
    '<small>' + aman(r.ket) + "</small></div>"
  ).join("");
  $$("ringkasan").setHTML(
    '<div class="ringkasan-periode"><b>' + aman(data.judul) + "</b> · " + aman(data.periode) + "</div>" +
    '<div class="ringkasan-isi">' + kotak + "</div>"
  );
}


function namaFile() {
  const jenis = $$("jenis").getValue();
  if (jenis === "restock") return laporan.judul + " " + UBAH_TANGGAL(new Date());
  return laporan.judul + " " + UBAH_TANGGAL($$("dari").getValue()) + " sd " + UBAH_TANGGAL($$("sampai").getValue());
}

function kolomEkspor() {
  const jenis = $$("jenis").getValue();
  return KOLOM[jenis].ekspor.filter((k) => KEPALA_GUDANG || k.id !== "toko");
}

function teksRingkasan() {
  return laporan.ringkasan.map((r) => r.label + ": " + nilaiRingkasan(r)).join("  ·  ");
}

function teksDicetak() {
  return "Dicetak oleh " + DATA.pengguna.nama + ", " + tanggalWaktu(new Date().toISOString()) + " WIB";
}

function unduhExcel(unduh) {
  return webix.toExcel($$("tabel"), {
    download: unduh !== false,
    filename: namaFile(),
    name: "Laporan",
    columns: kolomEkspor(),
    docHeader: "Stokara " + DATA.branch + " – " + laporan.judul + " – " + laporan.periode,
    docFooter: teksRingkasan() + "  ·  " + teksDicetak(),
  });
}

async function unduhPdf(unduh) {
  const pesan = webix.message({ text: "Menyiapkan PDF...", expire: -1 });
  try {
    return await webix.toPDF($$("tabel"), {
      download: unduh !== false,
      filename: namaFile(),
      orientation: "landscape",
      autowidth: false,
      columns: kolomEkspor(),
      docHeaderImage: { url: await logoJpeg(), width: 36, height: 36, align: "left", order: 0 },
      docHeader: {
        text: "Stokara " + DATA.branch + "\n" + laporan.judul + "\n" + laporan.periode + "\n\n" + teksRingkasan() + "\n" + teksDicetak(),
        textAlign: "left", color: 0x26215c, order: 1,
      },
    });
  } finally {
    webix.message.hide(pesan);
  }
}

function logoJpeg() {
  return new Promise((selesai, gagal) => {
    const gambar = new Image();
    gambar.onload = () => {
      const kanvas = document.createElement("canvas");
      kanvas.width = kanvas.height = 128;
      const kuas = kanvas.getContext("2d");
      kuas.fillStyle = "#fff";
      kuas.fillRect(0, 0, 128, 128);
      kuas.drawImage(gambar, 0, 0, 128, 128);
      kanvas.toBlob((blob) => selesai(URL.createObjectURL(blob)), "image/jpeg", 0.92);
    };
    gambar.onerror = gagal;
    gambar.src = "/static/img/logo-stokara.svg";
  });
}
