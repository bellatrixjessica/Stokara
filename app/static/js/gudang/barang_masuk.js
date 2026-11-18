/* =====================================================================
 * Barang Masuk dari supplier
 * - Kepala Gudang & Staff Gudang: lihat daftar dan detail
 * - Staff Gudang: catat barang masuk (stok otomatis bertambah)
 * API: GET/POST /api/barang-masuk, GET /api/barang-masuk/pilihan
 * DATA.boleh_catat = true kalau yang login Staff Gudang
 * ===================================================================== */

webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 46,
    columns: [
      { id: "nomor", header: "Nomor", width: 160, template: "#!nomor#" },
      { id: "dibuat", header: "Tanggal", width: 160, template: (b) => tanggalWaktu(b.dibuat), hidden: LAYAR_KECIL },
      { id: "supplier", header: "Supplier", fillspace: 1, minWidth: 150, template: "#!supplier#" },
      { id: "no_surat_jalan", header: "Surat jalan", width: 130, template: "#!no_surat_jalan#", hidden: LAYAR_KECIL },
      { id: "jumlah", header: { text: "Item", css: "kanan" }, css: "kanan", width: 70, template: (b) => b.items.length, hidden: LAYAR_KECIL },
      { id: "total", header: { text: "Total qty", css: "kanan" }, css: "kanan", width: 100, template: (b) => angka(totalQty(b.items)) },
      { id: "oleh", header: "Dicatat oleh", width: 180, template: (b) => aman(b.oleh.nama), hidden: LAYAR_KECIL },
    ],
    on: {
      onItemClick: function (id) {
        lihatDetail(this.getItem(id));
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari nomor, supplier, atau surat jalan...", maxWidth: 320, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {},
  ];
  if (DATA.boleh_catat) {
    toolbar.push({
      view: "button", value: LAYAR_KECIL ? "Catat" : "Catat Barang Masuk", css: "webix_primary",
      width: LAYAR_KECIL ? 80 : 170, click: bukaForm,
    });
  }

  tampilkanHalaman({
    rows: [
      judulHalaman("Barang Masuk", "Penerimaan barang dari supplier. Stok bertambah otomatis saat dicatat. Klik baris untuk melihat detail."),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatJendelaDetail();
  if (DATA.boleh_catat) {
    buatForm();
    muatPilihan();
  }
  muatData();
});

function totalQty(items) {
  return items.reduce((jumlah, item) => jumlah + item.qty, 0);
}

async function muatData() {
  const data = await api("GET", "/api/barang-masuk");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((b) => (b.nomor + " " + b.supplier + " " + b.no_surat_jalan).toLowerCase().includes(kata));
}

// ---------- Form catat barang masuk (Staff Gudang) ----------

let pilihanProduk = []; // [{ id, value: "P-0001 · Minyak Goreng 1L", satuan }]

function buatForm() {
  buatJendela("jendela", "Catat Barang Masuk", [
    { view: "richselect", name: "supplier_id", id: "pilihSupplier", label: "Supplier", options: [], required: true },
    {
      cols: [
        { view: "text", name: "no_surat_jalan", label: "No. surat jalan", placeholder: "Contoh: SJ-7781", required: true },
        { width: 12 },
        { view: "text", name: "catatan", label: "Catatan", placeholder: "Opsional" },
      ],
    },
    { view: "label", label: "Produk yang diterima", css: "label-kecil", height: 30 },
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
      id: "tabelItem",
      scroll: "y",
      css: "tabel",
      height: 190,
      columns: [
        { id: "nama", header: "Produk", fillspace: 1, template: "#!nama#" },
        { id: "qty", header: { text: "Qty", css: "kanan" }, css: "kanan", width: 90, template: (i) => angka(i.qty) },
        { id: "satuan", header: "Satuan", width: 80, template: "#!satuan#" },
        { id: "hapus", header: "", width: 50, template: '<span class="aksi merah hapus mdi mdi-delete-outline" title="Hapus"></span>' },
      ],
      onClick: {
        hapus: function (e, id) {
          this.remove(id);
        },
      },
    },
  ], simpan, 680);
}

async function muatPilihan() {
  const data = await api("GET", "/api/barang-masuk/pilihan");
  if (!data) return;
  pilihanProduk = data.produk;
  $$("pilihSupplier").define("options", data.supplier);
  $$("pilihSupplier").refresh();
  $$("pilihProduk").define("options", data.produk);
  $$("pilihProduk").refresh();
}

function bukaForm() {
  const form = $$("jendela_form");
  form.clear();
  form.clearValidation();
  $$("tabelItem").clearAll();
  $$("pilihProduk").setValue("");
  $$("isiQty").setValue(1);
  $$("jendela").show();
}

// Tambah produk ke daftar. Kalau produknya sudah ada, qty-nya dijumlahkan.
function tambahItem() {
  const produkId = $$("pilihProduk").getValue();
  const qty = Number($$("isiQty").getValue());
  if (!produkId) {
    webix.message({ type: "error", text: "Pilih produk dulu." });
    return;
  }

  const tabelItem = $$("tabelItem");
  if (tabelItem.exists(produkId)) {
    const item = tabelItem.getItem(produkId);
    tabelItem.updateItem(produkId, { qty: item.qty + qty });
  } else {
    const produk = pilihanProduk.find((p) => p.id === produkId);
    tabelItem.add({ id: produkId, nama: produk.value, satuan: produk.satuan, qty: qty });
  }
  $$("pilihProduk").setValue("");
  $$("isiQty").setValue(1);
}

async function simpan() {
  const form = $$("jendela_form");
  if (!form.validate()) return;

  const items = $$("tabelItem").serialize().map((i) => ({ produk_id: i.id, qty: i.qty }));
  if (items.length === 0) {
    webix.message({ type: "error", text: "Tambahkan minimal satu produk." });
    return;
  }

  const v = form.getValues();
  const hasil = await api("POST", "/api/barang-masuk", {
    supplier_id: v.supplier_id,
    no_surat_jalan: v.no_surat_jalan,
    catatan: v.catatan || "",
    items: items,
  });
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendela").hide();
  muatData();
}

// ---------- Jendela detail ----------

function buatJendelaDetail() {
  webix.ui({
    view: "window",
    id: "jendelaDetail",
    modal: true,
    position: "center",
    width: 640,
    fullscreen: LAYAR_KECIL,
    css: "jendela",
    head: {
      view: "toolbar", css: "jendela-head", height: 54, padding: { left: 16, right: 6 },
      cols: [
        { view: "label", id: "judulDetail", label: "" },
        { view: "icon", icon: "mdi mdi-close", click: () => $$("jendelaDetail").hide() },
      ],
    },
    body: {
      padding: 16,
      rows: [
        { view: "template", id: "infoDetail", css: "info-dokumen", borderless: true, autoheight: true, template: "" },
        { height: 10 },
        {
          view: "datatable",
          id: "tabelDetail",
          scroll: "y",
          css: "tabel",
          autoheight: true,
          maxHeight: 320,
          columns: [
            { id: "kode", header: "Kode", width: 90, template: "#!kode#" },
            { id: "nama", header: "Produk", fillspace: 1, template: "#!nama#" },
            { id: "qty", header: { text: "Qty", css: "kanan" }, css: "kanan", width: 80, template: (i) => angka(i.qty) },
            { id: "satuan", header: "Satuan", width: 80, template: "#!satuan#" },
          ],
        },
      ],
    },
  });
}

function lihatDetail(bm) {
  $$("judulDetail").setValue("Barang masuk " + bm.nomor);
  $$("infoDetail").setHTML(
    '<div class="info-grid">' +
      "<div><span>Supplier</span>" + aman(bm.supplier) + "</div>" +
      "<div><span>Tanggal</span>" + tanggalWaktu(bm.dibuat) + "</div>" +
      "<div><span>Surat jalan</span>" + aman(bm.no_surat_jalan) + "</div>" +
      "<div><span>Dicatat oleh</span>" + aman(bm.oleh.nama) + "</div>" +
      (bm.catatan ? '<div class="penuh"><span>Catatan</span>' + aman(bm.catatan) + "</div>" : "") +
    "</div>"
  );
  $$("tabelDetail").clearAll();
  $$("tabelDetail").parse(bm.items.map((item, i) => Object.assign({ id: i + 1 }, item)));
  $$("jendelaDetail").show();
}
