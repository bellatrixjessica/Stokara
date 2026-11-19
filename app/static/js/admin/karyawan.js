webix.ready(function () {
  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 46,
    columns: [
      { id: "username", header: "Username", width: 160, template: "#!username#", hidden: LAYAR_KECIL },
      { id: "nama", header: "Nama", fillspace: 1, minWidth: 110, template: "#!nama#" },
      { id: "label_role", header: "Role", width: 130, template: "#!label_role#", hidden: LAYAR_KECIL },
      { id: "toko", header: "Toko", width: 180, template: (u) => (u.toko ? aman(u.toko) : "–"), hidden: LAYAR_KECIL },
      { id: "aktif", header: "Status", width: LAYAR_KECIL ? 80 : 100, template: badgeStatus },
      { id: "aksi", header: "", width: LAYAR_KECIL ? 100 : 280, template: tombolAksi },
    ],
    onClick: {
      "aksi-ubah": function (e, id) {
        bukaForm(this.getItem(id));
      },
      "aksi-password": function (e, id) {
        bukaFormPassword(this.getItem(id));
      },
      "aksi-status": function (e, id) {
        ubahStatus(this.getItem(id));
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari username atau nama...", maxWidth: 320, on: { onTimedKeyPress: saring } },
    LAYAR_KECIL ? { width: 8 } : {},
    { view: "button", value: LAYAR_KECIL ? "Tambah" : "Tambah Karyawan", css: "webix_primary", width: LAYAR_KECIL ? 90 : 150, click: () => bukaForm(null) },
  ];

  tampilkanHalaman({
    rows: [judulHalaman("Karyawan", "Akun login, role, dan toko untuk Kepala Toko."), kartuTabel(toolbar, tabel)],
  });

  buatJendela("jendela", "Tambah Karyawan", [
    { view: "text", name: "username", label: "Username", placeholder: "Contoh: toko.kendal01", required: true },
    { view: "text", name: "nama", label: "Nama lengkap", required: true },
    {
      view: "richselect", name: "role", label: "Role", options: DATA.role, required: true,
      on: { onChange: aturPilihanToko },
    },
    { view: "richselect", name: "toko_id", id: "pilihToko", label: "Toko", options: [], hidden: true },
    {
      view: "text", type: "password", name: "password", id: "isiPassword", label: "Password awal",
      bottomLabel: "Minimal 8 karakter. Sampaikan ke karyawan secara langsung.",
    },
  ], simpan);

  buatJendela("jendelaPassword", "Reset Password", [
    { view: "template", id: "infoPassword", borderless: true, autoheight: true, css: "info-form", template: "" },
    {
      view: "text", type: "password", name: "password", label: "Password baru", required: true,
      bottomLabel: "Minimal 8 karakter.",
    },
  ], simpanPassword, 420);

  muatData();
  muatToko();
});

function tombolAksi(baris) {
  const status = baris.aktif ? "Nonaktifkan" : "Aktifkan";
  if (LAYAR_KECIL) {
    return '<span class="aksi aksi-ubah mdi mdi-pencil-outline" title="Ubah"></span>' +
      '<span class="aksi aksi-password mdi mdi-key-outline" title="Reset password"></span>' +
      '<span class="aksi aksi-status mdi mdi-power" title="' + status + '"></span>';
  }
  return '<span class="aksi aksi-ubah">Ubah</span>' +
    '<span class="aksi aksi-password">Reset password</span>' +
    '<span class="aksi aksi-status ' + (baris.aktif ? "merah" : "hijau") + '">' + status + "</span>";
}

async function muatData() {
  const data = await api("GET", "/api/master/karyawan");
  if (!data) return;
  $$("tabel").clearAll();
  $$("tabel").parse(data);
  saring();
}

async function muatToko() {
  const data = await api("GET", "/api/master/toko");
  if (!data) return;
  const pilihan = data.filter((t) => t.aktif).map((t) => ({ id: t.id, value: t.nama }));
  $$("pilihToko").define("options", pilihan);
  $$("pilihToko").refresh();
}

function saring() {
  const kata = $$("cari").getValue().toLowerCase();
  $$("tabel").filter((u) => (u.username + " " + u.nama).toLowerCase().includes(kata));
}

function aturPilihanToko(role) {
  if (role === "kepala_toko") {
    $$("pilihToko").show();
  } else {
    $$("pilihToko").hide();
  }
}

function bukaForm(user) {
  const form = $$("jendela_form");
  form.clear();
  form.clearValidation();

  if (user) {
    $$("jendela_judul").setValue("Ubah Karyawan");
    form.setValues(user);
    form.elements.username.disable();
    $$("isiPassword").hide();
  } else {
    $$("jendela_judul").setValue("Tambah Karyawan");
    form.elements.username.enable();
    $$("isiPassword").show();
  }
  aturPilihanToko(form.getValues().role);
  $$("jendela").show();
}

async function simpan() {
  const form = $$("jendela_form");
  if (!form.validate()) return;
  const v = form.getValues();
  const isi = { nama: v.nama, role: v.role, toko_id: v.toko_id || "" };

  let hasil;
  if (v.id) {
    hasil = await api("PUT", "/api/master/karyawan/" + v.id, isi);
  } else {
    isi.username = v.username;
    isi.password = v.password;
    hasil = await api("POST", "/api/master/karyawan", isi);
  }
  if (!hasil) return;

  berhasil(hasil.pesan);
  $$("jendela").hide();
  muatData();
}

function bukaFormPassword(user) {
  const form = $$("jendelaPassword_form");
  form.clear();
  form.clearValidation();
  form.setValues({ id: user.id });
  $$("infoPassword").setHTML("Password baru untuk <b>" + aman(user.nama) + "</b> (" + aman(user.username) + ").");
  $$("jendelaPassword").show();
}

async function simpanPassword() {
  const form = $$("jendelaPassword_form");
  if (!form.validate()) return;
  const v = form.getValues();

  const hasil = await api("POST", "/api/master/karyawan/" + v.id + "/password", { password: v.password });
  if (!hasil) return;
  berhasil(hasil.pesan);
  $$("jendelaPassword").hide();
}

async function ubahStatus(user) {
  const aktifkan = !user.aktif;
  const judul = (aktifkan ? "Aktifkan akun " : "Nonaktifkan akun ") + user.nama + "?";
  const teks = aktifkan
    ? "Pengguna ini bisa login kembali."
    : "Pengguna ini tidak bisa login lagi dan langsung keluar dari aplikasi.";
  if (!(await konfirmasi(judul, teks))) return;

  const hasil = await api("POST", "/api/master/karyawan/" + user.id + "/status", { aktif: aktifkan });
  if (!hasil) return;
  berhasil(hasil.pesan);
  muatData();
}
