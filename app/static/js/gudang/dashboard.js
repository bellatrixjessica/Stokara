/* =====================================================================
 * Dashboard insight (Kepala Gudang)
 * Menjawab dua pertanyaan:
 *   1. Apakah permintaan toko terpenuhi?  -> fill rate, tren, fill rate per toko
 *   2. Kapan harus restock?               -> status stok dan saran restock per produk
 * API: GET /api/dashboard (rumus ada di app/models/insight.py)
 * ===================================================================== */

const STATUS_INSIGHT = {
  KRITIS: '<span class="badge b-merah">Kritis</span>',
  PERLU_RESTOCK: '<span class="badge b-oranye">Perlu restock</span>',
  AMAN: '<span class="badge b-hijau">Aman</span>',
  TANPA_PERMINTAAN: '<span class="badge b-abu">Tidak ada permintaan</span>',
};

webix.ready(function () {
  // Empat kartu angka di atas. Di ponsel: 2 x 2.
  const kartu = [kartuAngka("kartuFill"), kartuAngka("kartuKritis"), kartuAngka("kartuRestock"), kartuAngka("kartuMenunggu")];
  const barisKartu = LAYAR_KECIL
    ? { rows: [{ cols: [kartu[0], kartu[1]], margin: 10 }, { cols: [kartu[2], kartu[3]], margin: 10 }], margin: 10 }
    : { cols: kartu, margin: 14 };

  const grafik = {
    css: "kartu-panel",
    rows: [
      { view: "template", id: "judulGrafik", css: "judul-panel", borderless: true, height: 44, template: "Tren permintaan 30 hari" },
      {
        view: "chart",
        id: "grafik",
        type: "bar",
        barWidth: 6,
        radius: 0,
        height: 220,
        xAxis: { template: (d) => d.tampilkan_label ? d.tanggal : "" },
        yAxis: {},
        legend: {
          values: [{ text: "Diminta", color: "#534AB7" }, { text: "Dikirim", color: "#EF9F27" }],
          valign: "top", align: "right", width: 80, layout: "x", marker: { type: "square", width: 10 },
        },
        series: [
          { value: "#diminta#", color: "#534AB7", tooltip: { template: "Diminta #diminta# (#tanggal#)" } },
          { value: "#dikirim#", color: "#EF9F27", tooltip: { template: "Dikirim #dikirim# (#tanggal#)" } },
        ],
      },
    ],
  };

  const perToko = {
    css: "kartu-panel",
    rows: [
      { view: "template", css: "judul-panel", borderless: true, height: 44, template: "Fill rate per toko" },
      {
        view: "datatable",
        id: "tabelToko",
        css: "tabel",
        header: false,
        scroll: "y",
        rowHeight: 44,
        columns: [
          { id: "toko", fillspace: 1, template: "#!toko#" },
          { id: "persen", width: 80, css: "kanan", template: kolomPersen },
        ],
      },
    ],
  };

  const tabelProduk = {
    view: "datatable",
    id: "tabelProduk",
    css: "tabel",
    rowHeight: 50,
    scroll: "y",
    columns: [
      { id: "status", header: "Status", width: LAYAR_KECIL ? 100 : 160, template: (p) => STATUS_INSIGHT[p.status] },
      {
        id: "nama", header: "Produk", fillspace: 1, minWidth: 150, css: "dua-baris",
        template: (p) => aman(p.nama) + '<span class="kecil">' + aman(p.kode) + " · lead time " + p.lead_time_hari + " hari</span>",
      },
      { id: "tersedia", header: { text: "Tersedia", css: "kanan" }, css: "kanan", width: 90, template: (p) => angka(p.tersedia), hidden: LAYAR_KECIL },
      { id: "demand", header: { text: "Demand/hari", css: "kanan" }, css: "kanan", width: 110, template: (p) => desimal(p.demand_per_hari), hidden: LAYAR_KECIL },
      { id: "ss", header: { text: "Safety stock", css: "kanan" }, css: "kanan", width: 125, template: (p) => angka(p.safety_stock), hidden: LAYAR_KECIL },
      { id: "rop", header: { text: "ROP", css: "kanan" }, css: "kanan", width: 70, template: (p) => angka(p.reorder_point), hidden: LAYAR_KECIL },
      { id: "habis", header: { text: "Habis dalam", css: "kanan" }, css: "kanan", width: 105, template: (p) => (p.habis_dalam === null ? "–" : desimal(p.habis_dalam) + " hari"), hidden: LAYAR_KECIL },
      { id: "saran", header: { text: "Saran restock", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 100 : 130, template: kolomSaran },
    ],
  };

  const toolbarProduk = [
    { view: "template", css: "judul-panel", borderless: true, template: "Saran restock" },
    {
      view: "segmented", id: "filterProduk", width: LAYAR_KECIL ? 190 : 250, value: "tindakan",
      options: [{ id: "tindakan", value: "Perlu tindakan" }, { id: "semua", value: "Semua produk" }],
      on: { onChange: saringProduk },
    },
  ];

  tampilkanHalaman({
    view: "scrollview",
    scroll: "y",
    body: {
      rows: [
        { view: "template", id: "judulDashboard", css: "judul-halaman", borderless: true, autoheight: true, template: "" },
        barisKartu,
        { height: 14 },
        LAYAR_KECIL
          ? { rows: [grafik, { height: 14 }, { height: 200, rows: [perToko] }] }
          : { height: 264, cols: [{ gravity: 2, rows: [grafik] }, { width: 14 }, { rows: [perToko] }] },
        { height: 14 },
        { height: 380, rows: [kartuTabel(toolbarProduk, tabelProduk)] },
      ],
    },
  });

  muatData();
});

function kartuAngka(id) {
  return { view: "template", id: id, css: "kartu-kpi", borderless: true, height: 104, template: "" };
}

function isiKartu(id, ikon, warna, angkaBesar, label, keterangan) {
  $$(id).setHTML(
    '<span class="kpi-ikon ' + warna + '"><span class="mdi ' + ikon + '"></span></span>' +
    "<b>" + angkaBesar + "</b>" +
    '<div class="kpi-label">' + label + "</div>" +
    '<div class="kpi-ket">' + keterangan + "</div>"
  );
}

// Fill rate di bawah 85% ditandai merah
function kolomPersen(t) {
  if (t.persen === null) return "–";
  const teks = desimal(t.persen) + "%";
  return t.persen < 85 ? '<b class="turun">' + teks + "</b>" : teks;
}

// Saran restock ditonjolkan hanya untuk Kritis / Perlu restock
function kolomSaran(p) {
  const teks = angka(p.saran_restock) + " " + aman(p.satuan);
  return ["KRITIS", "PERLU_RESTOCK"].includes(p.status) ? "<b>" + teks + "</b>" : '<span class="kecil" style="display:inline">' + teks + "</span>";
}

function saringProduk() {
  const nilai = $$("filterProduk").getValue();
  $$("tabelProduk").filter((p) => nilai === "semua" || ["KRITIS", "PERLU_RESTOCK"].includes(p.status));
}

async function muatData() {
  const d = await api("GET", "/api/dashboard");
  if (!d) return;

  $$("judulDashboard").setHTML(
    "<h2>Dashboard</h2><p>Dihitung dari permintaan " + d.periode.hari + " hari terakhir (" +
    d.periode.dari + " – " + d.periode.sampai + ").</p>"
  );

  const f = d.fill_rate;
  isiKartu("kartuFill", "mdi-check-decagram-outline", "hijau",
    f.persen === null ? "–" : desimal(f.persen) + "%", "Fill rate",
    angka(f.dikirim) + " dari " + angka(f.diminta) + " terkirim");
  isiKartu("kartuKritis", "mdi-alert-outline", "merah", angka(d.ringkasan.kritis), "Stok kritis", "Tersedia ≤ safety stock");
  isiKartu("kartuRestock", "mdi-refresh", "oranye", angka(d.ringkasan.perlu_restock), "Perlu restock", "Tersedia ≤ reorder point");
  isiKartu("kartuMenunggu", "mdi-timer-sand", "ungu", angka(d.ringkasan.menunggu_persetujuan), "Menunggu persetujuan",
    angka(d.ringkasan.menunggu_kirim) + " menunggu kirim");

  // Label tanggal di grafik cukup setiap 5 hari supaya tidak bertumpuk
  $$("grafik").clearAll();
  $$("grafik").parse(d.tren.map((t, i) => Object.assign({ tampilkan_label: i % 5 === 0 }, t)));

  $$("tabelToko").clearAll();
  $$("tabelToko").parse(d.fill_rate.per_toko);

  $$("tabelProduk").clearAll();
  $$("tabelProduk").parse(d.produk.map((p) => Object.assign({}, p, { id: p.kode })));
  saringProduk();
}
