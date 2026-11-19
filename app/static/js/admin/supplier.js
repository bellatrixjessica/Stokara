webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 46,
    columns: [
      { id: "kode", header: "Kode", width: 100, template: "#!kode#", hidden: LAYAR_KECIL },
      { id: "nama", header: "Nama supplier", fillspace: 1, minWidth: 120, template: "#!nama#" },
      { id: "telepon", header: "Telepon", width: 140, template: "#!telepon#", hidden: LAYAR_KECIL },
      { id: "alamat", header: "Alamat", fillspace: 2, minWidth: 200, template: "#!alamat#", hidden: LAYAR_KECIL },
      { id: "aktif", header: "Status", width: LAYAR_KECIL ? 80 : 100, template: badgeStatus },
      { id: "aksi", header: "", width: LAYAR_KECIL ? 76 : 190, template: tombolAksi },
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
    { view: "search", id: "cari", placeholder: "Cari kode atau nama supplier...", maxWidth: 320, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {},
    { view: "button", value: LAYAR_KECIL ? "Tambah" : "Tambah Supplier", css: "webix_primary", width: LAYAR_KECIL ? 90 : 150, click: () => bukaForm(null) },
  ];

  tampilkanHalaman({
    rows: [judulHalaman("Supplier", "Data pemasok barang ke gudang."), kartuTabel(toolbar, tabel)],
  });

  buatJendela("jendela", "Tambah Supplier", [
    { view: "text", name: "kode", label: "Kode supplier", placeholder: "Contoh: SUP-05", required: true },
    { view: "text", name: "nama", label: "Nama supplier", required: true },
    { view: "text", name: "telepon", label: "Telepon", placeholder: "Contoh: 024-7601234" },
    { view: "textarea", name: "alamat", label: "Alamat", height: 90 },
  ], simpan);

  muatData();
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
  const data = await api("GET", "/api/master/supplier");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((s) => (s.kode + " " + s.nama).toLowerCase().includes(kata));
}

function bukaForm(supplier) {
  const form = $$("jendela_form");
  form.clear();
  form.clearValidation();

  if (supplier) {
    $$("jendela_judul").setValue("Ubah Supplier");
    form.setValues(supplier);
    form.elements.kode.disable();
  } else {
    $$("jendela_judul").setValue("Tambah Supplier");
    form.elements.kode.enable();
  }
  $$("jendela").show();
}

async function simpan() {
  const form = $$("jendela_form");
  if (!form.validate()) return;
  const v = form.getValues();
  const isi = { nama: v.nama, telepon: v.telepon || "", alamat: v.alamat || "" };

  let hasil;
  if (v.id) {
    hasil = await api("PUT", "/api/master/supplier/" + v.id, isi);
  } else {
    isi.kode = v.kode;
    hasil = await api("POST", "/api/master/supplier", isi);
  }
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendela").hide();
  muatData();
}

async function ubahStatus(supplier) {
  const aktifkan = !supplier.aktif;
  const judul = (aktifkan ? "Aktifkan " : "Nonaktifkan ") + supplier.nama + "?";
  const teks = aktifkan
    ? "Supplier bisa dipilih lagi saat mencatat barang masuk."
    : "Supplier tidak bisa dipilih untuk produk dan barang masuk baru. Data lama tetap tersimpan.";
  if (!(await konfirmasi(judul, teks))) return;

  const hasil = await api("POST", "/api/master/supplier/" + supplier.id + "/status", { aktif: aktifkan });
  if (!hasil) return;
  berhasil(hasil.pesan);
  muatData();
}
