let permintaanAktif = null;
let pilihanProduk = [];

webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 50,
    columns: [
      kolomNomor(),
      { id: "item", header: { text: "Item", css: "kanan" }, css: "kanan", width: 70, template: (p) => p.items.length, hidden: LAYAR_KECIL },
      { id: "diminta", header: { text: "Diminta", css: "kanan" }, css: "kanan", width: 90, template: (p) => totalQty(p, "qty_diminta") },
      { id: "disetujui", header: { text: "Disetujui", css: "kanan" }, css: "kanan", width: 95, template: (p) => totalQty(p, "qty_disetujui"), hidden: LAYAR_KECIL },
      { id: "status", header: "Status", fillspace: 1, minWidth: LAYAR_KECIL ? 100 : 230, template: badgePermintaan },
    ],
    on: {
      onItemClick: function (id) {
        bukaDetail(id);
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari nomor permintaan...", maxWidth: 260, hidden: LAYAR_KECIL, on: { onTimedKeyPress: saring } },
    { width: 10, hidden: LAYAR_KECIL },
    { view: "richselect", id: "filterStatus", options: opsiStatus(), value: "semua", width: LAYAR_KECIL ? 130 : 180, on: { onChange: muatData } },
    {},
    { view: "button", value: LAYAR_KECIL ? "Ajukan" : "Ajukan Permintaan", css: "webix_primary", width: LAYAR_KECIL ? 90 : 170, click: bukaFormAjukan },
  ];

  tampilkanHalaman({
    rows: [
      judulHalaman("Permintaan Barang", "Ajukan permintaan ke gudang dan pantau statusnya. Klik baris untuk melihat detail."),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatFormAjukan();
  buatJendelaPermintaan(
    [
      {
        id: "nama", header: "Produk", fillspace: 1, minWidth: LAYAR_KECIL ? 110 : 160, css: "dua-baris",
        template: (i) => aman(i.nama) + '<span class="kecil">' + aman(i.kode) + " · " + aman(i.satuan) + "</span>",
      },
      { id: "qty_diminta", header: { text: "Diminta", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 85, template: (i) => angka(i.qty_diminta) },
      { id: "qty_disetujui", header: { text: "Disetujui", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 95, template: kolomDisetujui },
      { id: "qty_dikirim", header: { text: "Dikirim", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 85, template: (i) => angkaAtauStrip(i.qty_dikirim) },
    ],
    [
      { view: "button", id: "tombolBatal", value: "Batalkan permintaan", css: "tombol-bahaya", width: 180, hidden: true, click: batalkan },
      { width: 8 },
      { view: "button", id: "tombolTerima", value: "Konfirmasi diterima", css: "webix_primary", width: 180, hidden: true, click: terima },
    ]
  );

  muatPilihanProduk();
  muatData().then(() => {
    const nomor = nomorDariAlamat();
    if (nomor) {
      const p = $$("tabel").find((x) => x.nomor === nomor, true);
      if (p) bukaDetail(p.id);
    }
  });
});

function kolomDisetujui(i) {
  if (i.qty_disetujui === null) return "–";
  if (i.qty_disetujui < i.qty_diminta) return '<b class="teks-amber">' + angka(i.qty_disetujui) + "</b>";
  return angka(i.qty_disetujui);
}

async function muatData() {
  const status = $$("filterStatus").getValue();
  const data = await api("GET", "/api/permintaan" + (status === "semua" ? "" : "?status=" + status));
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((p) => p.nomor.toLowerCase().includes(kata));
}


async function bukaDetail(id) {
  const p = await api("GET", "/api/permintaan/" + id);
  if (!p) return;
  permintaanAktif = p;

  aturTombol("tombolBatal", p.status === "DIAJUKAN");
  aturTombol("tombolTerima", p.status === "DIKIRIM");

  const baris = p.items.map((item) => Object.assign({ id: item.produk_id }, item));
  isiJendelaPermintaan(p, baris);
}

function aturTombol(id, tampil) {
  if (tampil) $$(id).show(); else $$(id).hide();
}

async function batalkan() {
  const yakin = await konfirmasi("Batalkan " + permintaanAktif.nomor + "?", "Permintaan yang dibatalkan tidak bisa diaktifkan lagi.");
  if (!yakin) return;
  selesaiAksi(await api("POST", "/api/permintaan/" + permintaanAktif.id + "/batal"));
}

async function terima() {
  const yakin = await konfirmasi("Barang sudah diterima?", "Pastikan jumlah barang sesuai kolom Dikirim.");
  if (!yakin) return;
  selesaiAksi(await api("POST", "/api/permintaan/" + permintaanAktif.id + "/terima"));
}

function selesaiAksi(hasil) {
  if (!hasil) return;
  berhasil(hasil.pesan);
  $$("jendelaPermintaan").hide();
  muatData();
}


function buatFormAjukan() {
  buatJendela("jendelaAjukan", "Ajukan Permintaan", [
    { view: "label", label: "Produk yang diminta", css: "label-kecil", height: 30 },
    {
      cols: [
        { view: "combo", id: "pilihProduk", placeholder: "Ketik kode atau nama produk", options: [] },
        { width: 8 },
        { view: "counter", id: "isiQty", value: 1, min: 1, max: 100000, width: 140 },
        { width: 8 },
        { view: "button", value: "Tambah", css: "tombol-garis", width: 90, click: tambahItem },
      ],
    },
    {
      view: "datatable",
      id: "tabelAjukan",
      css: "tabel",
      height: 200,
      scroll: "y",
      columns: [
        { id: "nama", header: "Produk", fillspace: 1, template: "#!nama#" },
        { id: "qty", header: { text: "Qty", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 90, template: (i) => angka(i.qty) },
        { id: "satuan", header: "Satuan", width: 80, template: "#!satuan#" },
        { id: "hapus", header: "", width: 50, template: '<span class="aksi merah hapus mdi mdi-delete-outline" title="Hapus"></span>' },
      ],
      onClick: {
        hapus: function (e, id) {
          this.remove(id);
        },
      },
    },
    { view: "textarea", name: "catatan", label: "Catatan untuk gudang", placeholder: "Opsional, contoh: stok untuk akhir pekan", height: 80 },
  ], ajukan, 640);
}

async function muatPilihanProduk() {
  const data = await api("GET", "/api/permintaan/pilihan-produk");
  if (!data) return;
  pilihanProduk = data;
  $$("pilihProduk").define("options", data);
  $$("pilihProduk").refresh();
}

function bukaFormAjukan() {
  $$("jendelaAjukan_form").clear();
  $$("tabelAjukan").clearAll();
  $$("pilihProduk").setValue("");
  $$("isiQty").setValue(1);
  $$("jendelaAjukan").show();
}

function tambahItem() {
  const produkId = $$("pilihProduk").getValue();
  const qty = Number($$("isiQty").getValue());
  if (!produkId) {
    webix.message({ type: "error", text: "Pilih produk dulu." });
    return;
  }

  const tabel = $$("tabelAjukan");
  if (tabel.exists(produkId)) {
    tabel.updateItem(produkId, { qty: tabel.getItem(produkId).qty + qty });
  } else {
    const produk = pilihanProduk.find((p) => p.id === produkId);
    tabel.add({ id: produkId, nama: produk.value, satuan: produk.satuan, qty: qty });
  }
  $$("pilihProduk").setValue("");
  $$("isiQty").setValue(1);
}

async function ajukan() {
  const items = $$("tabelAjukan").serialize().map((i) => ({ produk_id: i.id, qty: i.qty }));
  if (items.length === 0) {
    webix.message({ type: "error", text: "Tambahkan minimal satu produk." });
    return;
  }

  const hasil = await api("POST", "/api/permintaan", {
    catatan: $$("jendelaAjukan_form").getValues().catatan || "",
    items: items,
  });
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendelaAjukan").hide();
  muatData();
}
