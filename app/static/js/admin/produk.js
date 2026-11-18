/* =====================================================================
 * Master Produk (Admin): daftar, tambah, ubah, aktif/nonaktif.
 * API: GET/POST /api/master/produk, PUT /api/master/produk/<id>,
 *      POST /api/master/produk/<id>/status
 * DATA.satuan dikirim dari Flask: ["PCS", "PACK", "KARTON", "BOX", "LUSIN"]
 * ===================================================================== */

webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 46,
    columns: [
      { id: "kode", header: "Kode", width: 90, template: "#!kode#", hidden: LAYAR_KECIL },
      { id: "nama", header: "Nama produk", fillspace: 1, minWidth: 120, template: "#!nama#" },
      { id: "kategori", header: "Kategori", width: 120, template: "#!kategori#", hidden: LAYAR_KECIL },
      { id: "satuan", header: "Satuan", width: 85, template: "#!satuan#", hidden: LAYAR_KECIL },
      { id: "supplier", header: "Supplier", width: 170, template: "#!supplier#", hidden: LAYAR_KECIL },
      { id: "lead_time_hari", header: { text: "Lead time", css: "kanan" }, width: 95, css: "kanan", template: "#lead_time_hari# hari", hidden: LAYAR_KECIL },
      { id: "aktif", header: "Status", width: LAYAR_KECIL ? 80 : 100, template: badgeStatus },
      { id: "aksi", header: "", width: LAYAR_KECIL ? 76 : 180, template: tombolAksi },
    ],
    onClick: {
      "aksi-ubah": function (e, id) {
        bukaForm(this.getItem(id));
      },
      "aksi-status": function (e, id) {
        ubahStatus(this.getItem(id));
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari kode, nama, atau kategori...", maxWidth: 320, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {}, // jarak antara kotak cari dan tombol
    { view: "button", value: LAYAR_KECIL ? "Tambah" : "Tambah Produk", css: "webix_primary", width: LAYAR_KECIL ? 90 : 140, click: () => bukaForm(null) },
  ];

  tampilkanHalaman({
    rows: [
      judulHalaman("Produk", "Data produk, satuan, supplier, dan lead time. Stok berubah lewat barang masuk, pengiriman, dan opname."),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatJendela("jendela", "Tambah Produk", [
    {
      cols: [
        { view: "text", name: "kode", label: "Kode produk", placeholder: "P-0013", required: true, width: 140 },
        { width: 12 },
        { view: "text", name: "nama", label: "Nama produk", placeholder: "Contoh: Gula Pasir 1kg", required: true },
      ],
    },
    {
      cols: [
        { view: "text", name: "kategori", label: "Kategori", placeholder: "Contoh: Sembako", required: true },
        { width: 12 },
        { view: "richselect", name: "satuan", label: "Satuan", options: DATA.satuan, required: true, width: 140 },
      ],
    },
    { view: "richselect", name: "supplier_id", id: "pilihSupplier", label: "Supplier", options: [], required: true },
    {
      view: "counter", name: "lead_time_hari", label: "Lead time (hari)", value: 2, min: 1, max: 60,
      bottomLabel: "Berapa hari barang datang setelah dipesan ke supplier.",
    },
  ], simpan, 520);

  muatData();
  muatSupplier();
});

function tombolAksi(baris) {
  const status = baris.aktif ? "Nonaktifkan" : "Aktifkan";
  if (LAYAR_KECIL) {
    return '<span class="aksi aksi-ubah mdi mdi-pencil-outline" title="Ubah"></span>' +
      '<span class="aksi aksi-status mdi mdi-power" title="' + status + '"></span>';
  }
  return '<span class="aksi aksi-ubah">Ubah</span>' +
    '<span class="aksi aksi-status ' + (baris.aktif ? "merah" : "hijau") + '">' + status + "</span>";
}

async function muatData() {
  const data = await api("GET", "/api/master/produk");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

// Pilihan supplier di form: hanya supplier yang aktif
async function muatSupplier() {
  const data = await api("GET", "/api/master/supplier");
  if (!data) return;
  const pilihan = data.filter((s) => s.aktif).map((s) => ({ id: s.id, value: s.nama }));
  $$("pilihSupplier").define("options", pilihan);
  $$("pilihSupplier").refresh();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((p) => (p.kode + " " + p.nama + " " + p.kategori).toLowerCase().includes(kata));
}

function bukaForm(produk) {
  const form = $$("jendela_form");
  form.clear();
  form.clearValidation();

  if (produk) {
    $$("jendela_judul").setValue("Ubah Produk");
    form.setValues(produk);
    form.elements.kode.disable();
  } else {
    $$("jendela_judul").setValue("Tambah Produk");
    form.setValues({ lead_time_hari: 2, satuan: "PCS" });
    form.elements.kode.enable();
  }
  $$("jendela").show();
}

async function simpan() {
  const form = $$("jendela_form");
  if (!form.validate()) return;
  const v = form.getValues();
  const isi = {
    nama: v.nama,
    kategori: v.kategori,
    satuan: v.satuan,
    supplier_id: v.supplier_id,
    lead_time_hari: Number(v.lead_time_hari),
  };

  let hasil;
  if (v.id) {
    hasil = await api("PUT", "/api/master/produk/" + v.id, isi);
  } else {
    isi.kode = v.kode;
    hasil = await api("POST", "/api/master/produk", isi);
  }
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendela").hide();
  muatData();
}

async function ubahStatus(produk) {
  const aktifkan = !produk.aktif;
  const judul = (aktifkan ? "Aktifkan " : "Nonaktifkan ") + produk.nama + "?";
  const teks = aktifkan
    ? "Produk bisa diminta toko dan dicatat di barang masuk lagi."
    : "Produk tidak bisa diminta toko atau dicatat di barang masuk baru. Riwayat tetap tersimpan.";
  if (!(await konfirmasi(judul, teks))) return;

  const hasil = await api("POST", "/api/master/produk/" + produk.id + "/status", { aktif: aktifkan });
  if (!hasil) return;
  berhasil(hasil.pesan);
  muatData();
}
