/* =====================================================================
 * Master Toko (Admin): daftar, tambah, ubah, aktif/nonaktif.
 * API: GET/POST /api/master/toko, PUT /api/master/toko/<id>,
 *      POST /api/master/toko/<id>/status
 * ===================================================================== */

webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 46,
    columns: [
      { id: "kode", header: "Kode", width: 100, template: "#!kode#", hidden: LAYAR_KECIL },  // #!...# = isi di-escape (aman dari XSS)
      { id: "nama", header: "Nama toko", fillspace: 1, minWidth: 120, template: "#!nama#" },
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
    { view: "search", id: "cari", placeholder: "Cari kode, nama, atau alamat...", maxWidth: 320, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {}, // jarak antara kotak cari dan tombol
    { view: "button", value: LAYAR_KECIL ? "Tambah" : "Tambah Toko", css: "webix_primary", width: LAYAR_KECIL ? 90 : 130, click: () => bukaForm(null) },
  ];

  tampilkanHalaman({
    rows: [judulHalaman("Toko", "Data toko yang dilayani gudang."), kartuTabel(toolbar, tabel)],
  });

  buatJendela("jendela", "Tambah Toko", [
    { view: "text", name: "kode", label: "Kode toko", placeholder: "Contoh: TK-04", required: true },
    { view: "text", name: "nama", label: "Nama toko", placeholder: "Contoh: Toko Kendal 01", required: true },
    { view: "textarea", name: "alamat", label: "Alamat", height: 90, required: true },
  ], simpan);

  muatData();
});

// Tombol Ubah dan Aktifkan/Nonaktifkan di setiap baris
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
  const data = await api("GET", "/api/master/toko");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((t) => (t.kode + " " + t.nama + " " + t.alamat).toLowerCase().includes(kata));
}

function bukaForm(toko) {
  const form = $$("jendela_form");
  form.clear();
  form.clearValidation();

  if (toko) {
    $$("jendela_judul").setValue("Ubah Toko");
    form.setValues(toko);
    form.elements.kode.disable(); // kode tidak bisa diubah
  } else {
    $$("jendela_judul").setValue("Tambah Toko");
    form.elements.kode.enable();
  }
  $$("jendela").show();
}

async function simpan() {
  const form = $$("jendela_form");
  if (!form.validate()) return;
  const v = form.getValues();

  let hasil;
  if (v.id) {
    hasil = await api("PUT", "/api/master/toko/" + v.id, { nama: v.nama, alamat: v.alamat });
  } else {
    hasil = await api("POST", "/api/master/toko", { kode: v.kode, nama: v.nama, alamat: v.alamat });
  }
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendela").hide();
  muatData();
}

async function ubahStatus(toko) {
  const aktifkan = !toko.aktif;
  const judul = (aktifkan ? "Aktifkan " : "Nonaktifkan ") + toko.nama + "?";
  const teks = aktifkan
    ? "Toko bisa kembali mengajukan permintaan."
    : "Toko tidak bisa mengajukan permintaan baru. Data lama tetap tersimpan.";
  if (!(await konfirmasi(judul, teks))) return;

  const hasil = await api("POST", "/api/master/toko/" + toko.id + "/status", { aktif: aktifkan });
  if (!hasil) return;
  berhasil(hasil.pesan);
  muatData();
}
