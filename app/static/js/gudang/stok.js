webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 50,
    columns: [
      {
        id: "nama", header: "Produk", fillspace: 1, minWidth: 150, css: "dua-baris",
        template: (p) => aman(p.nama) + '<span class="kecil">' + aman(p.kode) + " · " + aman(p.kategori) + "</span>",
      },
      { id: "satuan", header: "Satuan", width: 90, template: "#!satuan#", hidden: LAYAR_KECIL },
      { id: "fisik", header: { text: "Stok fisik", css: "kanan" }, css: "kanan", width: 110, template: (p) => angka(p.fisik), hidden: LAYAR_KECIL },
      { id: "dipesan", header: { text: "Dipesan", css: "kanan" }, css: "kanan", width: 100, template: (p) => angka(p.dipesan), hidden: LAYAR_KECIL },
      { id: "tersedia", header: { text: "Tersedia", css: "kanan" }, css: "kanan", width: 110, template: kolomTersedia },
      { id: "aksi", header: "", width: LAYAR_KECIL ? 50 : 120, template: () => (LAYAR_KECIL ? '<span class="aksi mdi mdi-history"></span>' : '<span class="aksi">Riwayat</span>') },
    ],
    on: {
      onItemClick: function (id) {
        bukaRiwayat(this.getItem(id));
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari kode, nama, atau kategori...", maxWidth: 320, on: { onTimedKeyPress: muatData } },
    {},
    { view: "button", value: "Muat ulang", css: "tombol-garis", width: 110, hidden: LAYAR_KECIL, click: muatData },
  ];

  tampilkanHalaman({
    rows: [
      judulHalaman("Stok Gudang", "Tersedia = stok fisik − dipesan (sudah disetujui untuk toko tapi belum dikirim). Klik produk untuk melihat riwayat."),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatJendelaRiwayat();
  muatData();
});

function kolomTersedia(p) {
  const teks = angka(p.tersedia);
  return p.tersedia <= 0 ? '<b class="turun">' + teks + "</b>" : "<b>" + teks + "</b>";
}

async function muatData() {
  const kata = $$("cari").getValue().trim();
  const data = await api("GET", "/api/stok" + (kata ? "?cari=" + encodeURIComponent(kata) : ""));
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
}


const LABEL_JENIS = {
  MASUK: '<span class="badge b-hijau">Masuk</span>',
  KELUAR: '<span class="badge b-oranye">Keluar</span>',
  ADJUST: '<span class="badge b-ungu">Penyesuaian</span>',
};

function buatJendelaRiwayat() {
  webix.ui({
    view: "window",
    id: "jendelaRiwayat",
    modal: true,
    position: "center",
    width: 860,
    height: 520,
    fullscreen: LAYAR_KECIL,
    css: "jendela",
    head: {
      view: "toolbar", css: "jendela-head", height: 54, padding: { left: 16, right: 6 },
      cols: [
        { view: "label", id: "judulRiwayat", label: "Riwayat stok" },
        { view: "icon", icon: "mdi mdi-close", click: () => $$("jendelaRiwayat").hide() },
      ],
    },
    body: {
      view: "datatable",
      id: "tabelRiwayat",
      scroll: "y",
      css: "tabel",
      rowHeight: 50,
      columns: [
        { id: "waktu", header: "Waktu", width: 150, template: (m) => tanggalWaktu(m.waktu) },
        { id: "jenis", header: "Jenis", width: 115, template: (m) => LABEL_JENIS[m.jenis] },
        { id: "perubahan", header: { text: "Perubahan", css: "kanan" }, css: "kanan", width: 100, template: (m) => perubahan(m.perubahan) },
        { id: "stok_sesudah", header: { text: "Stok akhir", css: "kanan" }, css: "kanan", width: 95, template: (m) => angka(m.stok_sesudah), hidden: LAYAR_KECIL },
        {
          id: "referensi", header: "Referensi", fillspace: 1, minWidth: 200, hidden: LAYAR_KECIL, css: "dua-baris",
          template: (m) => aman(m.referensi) + '<span class="kecil">' + aman(m.keterangan) + " · " + aman(m.oleh.nama) + "</span>",
        },
      ],
    },
  });
}

async function bukaRiwayat(produk) {
  $$("judulRiwayat").setValue("Riwayat stok · " + produk.kode + " " + produk.nama);
  $$("tabelRiwayat").clearAll();
  $$("jendelaRiwayat").show();

  const data = await api("GET", "/api/stok/" + produk.id + "/mutasi");
  if (!data) return;
  $$("tabelRiwayat").parse(data);
  if (data.length === 0) {
    webix.message("Belum ada perubahan stok untuk produk ini.");
  }
}
