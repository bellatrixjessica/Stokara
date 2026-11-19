const KEPALA_GUDANG = DATA.pengguna.role === "kepala_gudang";
let opnameAktif = null;

const STATUS_OPNAME = {
  MENUNGGU: '<span class="badge b-biru">Menunggu</span>',
  DISETUJUI: '<span class="badge b-hijau">Disetujui</span>',
  DITOLAK: '<span class="badge b-merah">Ditolak</span>',
};

webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 50,
    columns: [
      {
        id: "nomor", header: "Nomor", width: 170, css: "dua-baris",
        template: (o) => aman(o.nomor) + '<span class="kecil">' + tanggalWaktu(o.dibuat) + "</span>",
      },
      { id: "oleh", header: "Dihitung oleh", fillspace: 1, minWidth: 150, template: (o) => aman(o.dihitung_oleh.nama), hidden: LAYAR_KECIL },
      { id: "produk", header: { text: "Produk", css: "kanan" }, css: "kanan", width: 80, template: (o) => o.items.length },
      { id: "selisih", header: { text: "Ada selisih", css: "kanan" }, css: "kanan", width: 100, template: (o) => o.items.filter((i) => i.selisih !== 0).length, hidden: LAYAR_KECIL },
      { id: "status", header: "Status", width: 120, template: (o) => STATUS_OPNAME[o.status] },
    ],
    on: {
      onItemClick: function (id) {
        bukaDetail(this.getItem(id));
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari nomor opname...", maxWidth: 280, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {},
  ];
  if (!KEPALA_GUDANG) {
    toolbar.push({ view: "button", value: LAYAR_KECIL ? "Hitung" : "Mulai Opname", css: "webix_primary", width: LAYAR_KECIL ? 90 : 140, click: bukaForm });
  }

  tampilkanHalaman({
    rows: [
      judulHalaman(
        "Stock Opname",
        KEPALA_GUDANG
          ? "Periksa hasil hitung fisik. Setelah disetujui, stok dikoreksi sebesar selisihnya."
          : "Hitung barang di rak, lalu catat hasilnya. Stok baru berubah setelah disetujui Kepala Gudang."
      ),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatJendelaDetail();
  if (!KEPALA_GUDANG) buatForm();

  muatData().then(() => {
    const nomor = new URLSearchParams(window.location.search).get("nomor");
    if (nomor) {
      const o = $$("tabel").find((x) => x.nomor === nomor, true);
      if (o) bukaDetail(o);
    }
  });
});

async function muatData() {
  const data = await api("GET", "/api/opname");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((o) => o.nomor.toLowerCase().includes(kata));
}

function kolomSelisih(i) {
  if (i.selisih === "" || i.selisih === undefined) return "";
  return i.selisih === 0 ? '<span class="kecil" style="display:inline">sesuai</span>' : perubahan(i.selisih);
}


function buatJendelaDetail() {
  webix.ui({
    view: "window",
    id: "jendelaDetail",
    modal: true,
    position: "center",
    width: 760,
    fullscreen: LAYAR_KECIL,
    css: "jendela",
    head: {
      view: "toolbar", css: "jendela-head", height: 54, padding: { left: 16, right: 6 },
      cols: [
        { view: "template", id: "judulDetail", css: "judul-jendela", borderless: true, template: "" },
        { view: "icon", icon: "mdi mdi-close", click: () => $$("jendelaDetail").hide() },
      ],
    },
    body: {
      padding: 16,
      rows: [
        { view: "template", id: "infoDetail", css: "info-dokumen", borderless: true, autoheight: true, template: "" },
        { height: 12 },
        {
          view: "datatable",
          id: "tabelDetail",
          css: "tabel",
          autoheight: true,
          maxHeight: 320,
          scroll: "y",
          rowHeight: 50,
          columns: [
            {
              id: "nama", header: "Produk", fillspace: 1, minWidth: LAYAR_KECIL ? 110 : 180, css: "dua-baris",
              template: (i) => aman(i.nama) + '<span class="kecil">' + aman(i.kode) + " · " + aman(i.satuan) + "</span>",
            },
            { id: "stok_sistem", header: { text: "Sistem", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 90, template: (i) => angka(i.stok_sistem) },
            { id: "stok_hitung", header: { text: "Hitung", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 90, template: (i) => angka(i.stok_hitung) },
            { id: "selisih", header: { text: "Selisih", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 70 : 100, template: kolomSelisih },
          ],
        },
        { height: 12 },
        {
          cols: [
            {},
            { view: "button", id: "tombolTolak", value: "Tolak", css: "tombol-bahaya", width: 100, hidden: true, click: tolak },
            { width: 8 },
            { view: "button", id: "tombolSetujui", value: "Setujui & koreksi stok", css: "webix_primary", width: 200, hidden: true, click: setujui },
          ],
        },
      ],
    },
  });
}

function bukaDetail(o) {
  opnameAktif = o;
  $$("judulDetail").setHTML("Opname " + aman(o.nomor) + " " + STATUS_OPNAME[o.status]);

  let info =
    '<div class="info-grid">' +
    "<div><span>Dihitung</span>" + tanggalWaktu(o.dibuat) + "</div>" +
    "<div><span>Oleh</span>" + aman(o.dihitung_oleh.nama) + "</div>" +
    "<div><span>Diperiksa</span>" + (o.diperiksa_oleh ? aman(o.diperiksa_oleh.nama) : "–") + "</div>" +
    "<div><span>Catatan</span>" + aman(o.catatan || "–") + "</div>" +
    "</div>";
  if (o.alasan_tolak) {
    info += '<div class="kotak-alasan"><b>Alasan ditolak:</b> ' + aman(o.alasan_tolak) + "</div>";
  }
  $$("infoDetail").setHTML(info);

  $$("tabelDetail").clearAll();
  $$("tabelDetail").parse(o.items.map((item) => Object.assign({ id: item.produk_id }, item)));

  const bolehPeriksa = KEPALA_GUDANG && o.status === "MENUNGGU";
  if (bolehPeriksa) {
    $$("tombolTolak").show();
    $$("tombolSetujui").show();
  } else {
    $$("tombolTolak").hide();
    $$("tombolSetujui").hide();
  }

  $$("jendelaDetail").show();
  $$("jendelaDetail").resize();
}

async function setujui() {
  const yakin = await konfirmasi(
    "Setujui " + opnameAktif.nomor + "?",
    "Stok setiap produk dikoreksi sebesar selisihnya dan tercatat sebagai penyesuaian (ADJUST)."
  );
  if (!yakin) return;
  selesai(await api("POST", "/api/opname/" + opnameAktif.id + "/setujui"));
}

async function tolak() {
  const alasan = await mintaTeks("Tolak " + opnameAktif.nomor + "?", "Tulis alasan. Staff Gudang akan menghitung ulang.", "Contoh: jumlah minyak perlu dihitung ulang");
  if (!alasan) return;
  selesai(await api("POST", "/api/opname/" + opnameAktif.id + "/tolak", { alasan: alasan }));
}

function selesai(hasil) {
  if (!hasil) return;
  berhasil(hasil.pesan);
  $$("jendelaDetail").hide();
  muatData();
  muatNotifikasi();
}


function buatForm() {
  buatJendela("jendelaHitung", "Mulai Opname", [
    {
      view: "template", borderless: true, autoheight: true, css: "info-form",
      template: "Klik kolom <b>Hitung fisik</b> lalu ketik jumlah barang di rak. Produk yang tidak dihitung biarkan kosong.",
    },
    {
      view: "datatable",
      id: "tabelHitung",
      css: "tabel sedang-edit",
      height: 320,
      scroll: "y",
      editable: true,
      editaction: "click",
      rowHeight: 46,
      columns: [
        {
          id: "nama", header: "Produk", fillspace: 1, minWidth: 140, css: "dua-baris",
          template: (p) => aman(p.nama) + '<span class="kecil">' + aman(p.kode) + " · " + aman(p.satuan) + "</span>",
        },
        { id: "stok", header: { text: "Sistem", css: "kanan" }, css: "kanan", width: 75, template: (p) => angka(p.stok) },
        { id: "hitung", header: { text: "Hitung fisik", css: "kanan" }, css: "kanan kolom-edit", width: 100, editor: "text" },
        {
          id: "selisih", header: { text: "Selisih", css: "kanan" }, css: "kanan", width: 80,
          template: (p) => (p.hitung === "" || p.hitung === undefined ? "" : kolomSelisih({ selisih: Number(p.hitung) - p.stok })),
        },
      ],
    },
    { view: "text", name: "catatan", label: "Catatan", placeholder: "Opsional, contoh: rak B, 2 dus penyok dibuang" },
  ], simpanHitung, 700);
}

async function bukaForm() {
  const produk = await api("GET", "/api/opname/produk");
  if (!produk) return;
  $$("jendelaHitung_form").clear();
  $$("tabelHitung").clearAll();
  $$("tabelHitung").parse(produk.map((p) => Object.assign({ hitung: "" }, p)));
  $$("jendelaHitung").show();
}

async function simpanHitung() {
  const tabel = $$("tabelHitung");
  tabel.editStop();

  const items = [];
  for (const p of tabel.serialize()) {
    if (p.hitung === "" || p.hitung === undefined) continue;
    const qty = Number(p.hitung);
    if (!Number.isInteger(qty) || qty < 0) {
      webix.message({ type: "error", text: aman(p.nama + ": hasil hitung harus angka bulat 0 atau lebih.") });
      return;
    }
    items.push({ produk_id: p.id, qty: qty });
  }
  if (items.length === 0) {
    webix.message({ type: "error", text: "Isi hasil hitung minimal satu produk." });
    return;
  }

  const hasil = await api("POST", "/api/opname", {
    catatan: $$("jendelaHitung_form").getValues().catatan || "",
    items: items,
  });
  if (!hasil) return;
  berhasil(hasil.pesan);
  $$("jendelaHitung").hide();
  muatData();
}
