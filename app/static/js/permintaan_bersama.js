const STATUS_PERMINTAAN = {
  DIAJUKAN: { label: "Diajukan", css: "b-biru" },
  DISETUJUI: { label: "Disetujui", css: "b-ungu" },
  DIKIRIM: { label: "Dikirim", css: "b-oranye" },
  DITERIMA: { label: "Diterima", css: "b-hijau" },
  DITOLAK: { label: "Ditolak", css: "b-merah" },
  DIBATALKAN: { label: "Dibatalkan", css: "b-abu" },
};

function opsiStatus() {
  const opsi = [{ id: "semua", value: "Semua status" }];
  for (const kode in STATUS_PERMINTAAN) {
    opsi.push({ id: kode, value: STATUS_PERMINTAAN[kode].label });
  }
  return opsi;
}

function labelStatus(status) {
  const s = STATUS_PERMINTAAN[status];
  return '<span class="badge ' + s.css + '">' + s.label + "</span>";
}

function qtyDisesuaikan(p) {
  if (!["DISETUJUI", "DIKIRIM", "DITERIMA"].includes(p.status)) return false;
  return p.items.some((i) => i.qty_disetujui < i.qty_diminta);
}

function badgePermintaan(p) {
  let html = labelStatus(p.status);
  if (qtyDisesuaikan(p)) {
    html += ' <span class="badge b-amber">Qty disesuaikan</span>';
  }
  return html;
}

function totalQty(p, kolom) {
  if (p.items.every((i) => i[kolom] === null || i[kolom] === undefined)) return "–";
  return angka(p.items.reduce((jumlah, i) => jumlah + (i[kolom] || 0), 0));
}

function angkaAtauStrip(n) {
  return n === null || n === undefined ? "–" : angka(n);
}

function nomorDariAlamat() {
  return new URLSearchParams(window.location.search).get("nomor");
}

function kolomNomor() {
  return {
    id: "nomor", header: "Nomor", width: 170, css: "dua-baris",
    template: (p) => aman(p.nomor) + '<span class="kecil">' + tanggalWaktu(p.dibuat) + "</span>",
  };
}


function buatJendelaPermintaan(kolom, tombol) {
  webix.ui({
    view: "window",
    id: "jendelaPermintaan",
    modal: true,
    position: "center",
    width: 900,
    fullscreen: LAYAR_KECIL,
    css: "jendela",
    head: {
      view: "toolbar", css: "jendela-head", height: 54, padding: { left: 16, right: 6 },
      cols: [
        { view: "template", id: "judulPermintaan", css: "judul-jendela", borderless: true, template: "" },
        { view: "icon", icon: "mdi mdi-close", click: () => $$("jendelaPermintaan").hide() },
      ],
    },
    body: {
      padding: 16,
      rows: [
        { view: "template", id: "infoPermintaan", css: "info-dokumen", borderless: true, autoheight: true, template: "" },
        { height: 12 },
        {
          view: "datatable",
          id: "tabelPermintaan",
          css: "tabel",
          autoheight: true,
          maxHeight: 300,
          scroll: "y",
          rowHeight: 50,
          editaction: "click",
          columns: kolom,
        },
        { height: 12 },
        { view: "template", id: "riwayatPermintaan", css: "info-dokumen", borderless: true, autoheight: true, template: "" },
        { height: 8 },
        { cols: [{}].concat(tombol) },
      ],
    },
  });
}

function isiJendelaPermintaan(p, baris) {
  $$("judulPermintaan").setHTML("Permintaan " + aman(p.nomor) + " " + badgePermintaan(p));

  let info =
    '<div class="info-grid">' +
    "<div><span>Toko</span>" + aman(p.toko) + "</div>" +
    "<div><span>Diajukan</span>" + tanggalWaktu(p.dibuat) + "</div>" +
    "<div><span>Oleh</span>" + aman(p.diajukan_oleh.nama) + "</div>" +
    "<div><span>Catatan</span>" + aman(p.catatan || "–") + "</div>" +
    "</div>";
  if (p.alasan_tolak) {
    info += '<div class="kotak-alasan"><b>Alasan ditolak:</b> ' + aman(p.alasan_tolak) + "</div>";
  }
  $$("infoPermintaan").setHTML(info);

  const tabel = $$("tabelPermintaan");
  tabel.clearAll();
  tabel.parse(baris);

  let riwayat = '<div class="riwayat-judul">Riwayat</div><div class="riwayat">';
  for (const r of p.riwayat) {
    const label = r.catatan === "Qty disetujui diubah" ? "Qty diubah" : STATUS_PERMINTAAN[r.status].label;
    riwayat +=
      "<div><b>" + label + "</b> · " + tanggalWaktu(r.waktu) + " · " + aman(r.oleh) +
      (r.catatan && r.catatan !== "Qty disetujui diubah" ? '<span class="kecil">' + aman(r.catatan) + "</span>" : "") +
      "</div>";
  }
  $$("riwayatPermintaan").setHTML(riwayat + "</div>");

  $$("jendelaPermintaan").show();
  $$("jendelaPermintaan").resize();
}
