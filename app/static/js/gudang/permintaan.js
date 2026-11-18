/* =====================================================================
 * Permintaan Toko (halaman gudang)
 * - Kepala Gudang : setujui (qty disetujui bisa diubah), ubah qty, tolak
 * - Staff Gudang  : kirim
 * Fungsi bersama (label status, jendela detail) ada di permintaan_bersama.js
 * ===================================================================== */

const KEPALA_GUDANG = DATA.pengguna.role === "kepala_gudang";
let permintaanAktif = null; // permintaan yang sedang dibuka di jendela detail

webix.ready(function () {
  // Kepala Gudang langsung melihat yang perlu disetujui, Staff Gudang yang perlu dikirim
  const statusAwal = KEPALA_GUDANG ? "DIAJUKAN" : "DISETUJUI";

  const tabel = {
    view: "datatable",
    id: "tabel",
    css: "tabel",
    select: "row",
    rowHeight: 50,
    columns: [
      kolomNomor(),
      { id: "toko", header: "Toko", fillspace: 1, minWidth: 140, template: "#!toko#" },
      { id: "item", header: { text: "Item", css: "kanan" }, css: "kanan", width: 70, template: (p) => p.items.length, hidden: LAYAR_KECIL },
      { id: "diminta", header: { text: "Diminta", css: "kanan" }, css: "kanan", width: 90, template: (p) => totalQty(p, "qty_diminta"), hidden: LAYAR_KECIL },
      { id: "disetujui", header: { text: "Disetujui", css: "kanan" }, css: "kanan", width: 95, template: (p) => totalQty(p, "qty_disetujui"), hidden: LAYAR_KECIL },
      { id: "status", header: "Status", width: LAYAR_KECIL ? 105 : 230, template: badgePermintaan },
    ],
    on: {
      onItemClick: function (id) {
        bukaDetail(id);
      },
    },
  };

  const toolbar = [
    { view: "search", id: "cari", placeholder: "Cari nomor atau toko...", maxWidth: 280, on: { onTimedKeyPress: saring } },
    { width: 10 },
    { view: "richselect", id: "filterStatus", options: opsiStatus(), value: statusAwal, width: LAYAR_KECIL ? 130 : 180, on: { onChange: muatData } },
    {},
    { view: "button", value: "Muat ulang", css: "tombol-garis", width: 110, hidden: LAYAR_KECIL, click: muatData },
  ];

  tampilkanHalaman({
    rows: [
      judulHalaman(
        "Permintaan Toko",
        KEPALA_GUDANG
          ? "Setujui atau tolak permintaan toko. Qty disetujui tidak boleh melebihi stok tersedia."
          : "Kirim permintaan yang sudah disetujui. Qty dikirim selalu sama dengan qty disetujui."
      ),
      kartuTabel(toolbar, tabel),
    ],
  });

  buatJendelaPermintaan(
    [
      {
        id: "nama", header: "Produk", fillspace: 1, minWidth: LAYAR_KECIL ? 110 : 160, css: "dua-baris",
        template: (i) => aman(i.nama) + '<span class="kecil">' + aman(i.kode) + " · " + aman(i.satuan) + "</span>",
      },
      { id: "qty_diminta", header: { text: "Diminta", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 85, template: (i) => angka(i.qty_diminta) },
      { id: "stok_fisik", header: { text: "Stok fisik", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 90, template: (i) => angka(i.stok_fisik), hidden: LAYAR_KECIL },
      { id: "tersedia", header: { text: "Tersedia", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 90, template: (i) => angka(i.tersedia) },
      {
        id: "qty_disetujui", header: { text: "Disetujui", css: "kanan" }, css: "kanan kolom-edit", width: LAYAR_KECIL ? 64 : 95,
        editor: "text", template: (i) => angkaAtauStrip(i.qty_disetujui),
      },
      { id: "qty_dikirim", header: { text: "Dikirim", css: "kanan" }, css: "kanan", width: LAYAR_KECIL ? 64 : 85, template: (i) => angkaAtauStrip(i.qty_dikirim) },
    ],
    [
      { view: "button", id: "tombolTolak", value: "Tolak", css: "tombol-bahaya", width: 100, hidden: true, click: tolak },
      { width: 8 },
      { view: "button", id: "tombolSimpanQty", value: "Simpan perubahan qty", css: "webix_primary", width: 190, hidden: true, click: simpanQty },
      { view: "button", id: "tombolSetujui", value: "Setujui", css: "webix_primary", width: 120, hidden: true, click: setujui },
      { view: "button", id: "tombolKirim", value: "Kirim", css: "webix_primary", width: 120, hidden: true, click: kirim },
    ]
  );

  muatData().then(() => {
    // Datang dari klik notifikasi: langsung buka permintaannya
    const nomor = nomorDariAlamat();
    if (nomor) bukaBerdasarkanNomor(nomor);
  });
});

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
  $$("tabel").filter((p) => (p.nomor + " " + p.toko).toLowerCase().includes(kata));
}

async function bukaBerdasarkanNomor(nomor) {
  // Permintaannya mungkin tidak ada di filter status saat ini, jadi cari di semua status
  const semua = await api("GET", "/api/permintaan");
  const p = semua && semua.find((x) => x.nomor === nomor);
  if (p) bukaDetail(p.id);
}

// ---------- Jendela detail ----------

async function bukaDetail(id) {
  const p = await api("GET", "/api/permintaan/" + id);
  if (!p) return;
  permintaanAktif = p;

  // Kepala Gudang boleh mengisi qty disetujui saat status Diajukan atau Disetujui
  const bolehUbahQty = KEPALA_GUDANG && ["DIAJUKAN", "DISETUJUI"].includes(p.status);

  const baris = p.items.map(function (item) {
    const isi = Object.assign({ id: item.produk_id }, item);
    if (p.status === "DIAJUKAN") {
      // Terisi otomatis: sebanyak yang bisa dipenuhi (terkecil antara diminta dan tersedia)
      isi.qty_disetujui = Math.min(item.qty_diminta, item.tersedia);
    }
    return isi;
  });

  const tabel = $$("tabelPermintaan");
  tabel.define("editable", bolehUbahQty);
  if (bolehUbahQty) {
    webix.html.addCss(tabel.$view, "sedang-edit");
  } else {
    webix.html.removeCss(tabel.$view, "sedang-edit");
  }
  // Kolom stok hanya berguna selama permintaan belum dikirim
  const masihProses = ["DIAJUKAN", "DISETUJUI"].includes(p.status);
  if (masihProses) tabel.showColumn("tersedia"); else tabel.hideColumn("tersedia");
  // Di ponsel kolom Dikirim (masih kosong) disembunyikan selama proses, supaya tabel muat
  if (LAYAR_KECIL && masihProses) tabel.hideColumn("qty_dikirim"); else tabel.showColumn("qty_dikirim");

  aturTombol("tombolTolak", KEPALA_GUDANG && masihProses);
  aturTombol("tombolSetujui", KEPALA_GUDANG && p.status === "DIAJUKAN");
  aturTombol("tombolSimpanQty", KEPALA_GUDANG && p.status === "DISETUJUI");
  aturTombol("tombolKirim", !KEPALA_GUDANG && p.status === "DISETUJUI");

  isiJendelaPermintaan(p, baris);
}

function aturTombol(id, tampil) {
  if (tampil) $$(id).show(); else $$(id).hide();
}

/**
 * Ambil qty disetujui dari tabel, contoh [{ produk_id: "...", qty: 30 }, ...].
 * Mengembalikan null (dan menampilkan pesan) kalau ada isian yang bukan angka bulat >= 0.
 */
function bacaQtyDisetujui() {
  const tabel = $$("tabelPermintaan");
  tabel.editStop(); // simpan angka yang sedang diketik
  const hasil = [];
  for (const baris of tabel.serialize()) {
    const qty = Number(baris.qty_disetujui);
    if (!Number.isInteger(qty) || qty < 0) {
      webix.message({ type: "error", text: aman(baris.nama + ": qty disetujui harus angka bulat 0 atau lebih.") });
      return null;
    }
    hasil.push({ produk_id: baris.id, qty: qty });
  }
  return hasil;
}

async function setujui() {
  const items = bacaQtyDisetujui();
  if (!items) return;
  const hasil = await api("POST", "/api/permintaan/" + permintaanAktif.id + "/setujui", { items: items });
  selesaiAksi(hasil);
}

async function simpanQty() {
  const items = bacaQtyDisetujui();
  if (!items) return;
  const hasil = await api("POST", "/api/permintaan/" + permintaanAktif.id + "/ubah-qty", { items: items });
  selesaiAksi(hasil);
}

async function tolak() {
  const alasan = await mintaTeks(
    "Tolak " + permintaanAktif.nomor + "?",
    "Tulis alasan penolakan. Alasan ini dikirim ke toko.",
    "Contoh: stok Air Mineral 600ml kosong"
  );
  if (!alasan) return;
  const hasil = await api("POST", "/api/permintaan/" + permintaanAktif.id + "/tolak", { alasan: alasan });
  selesaiAksi(hasil);
}

async function kirim() {
  const yakin = await konfirmasi(
    "Kirim " + permintaanAktif.nomor + "?",
    "Stok fisik akan dikurangi sesuai qty disetujui. Pengiriman tidak bisa dibatalkan."
  );
  if (!yakin) return;
  const hasil = await api("POST", "/api/permintaan/" + permintaanAktif.id + "/kirim");
  selesaiAksi(hasil);
}

function selesaiAksi(hasil) {
  if (!hasil) return; // gagal: pesan error sudah tampil, jendela tetap terbuka
  berhasil(hasil.pesan);
  $$("jendelaPermintaan").hide();
  muatData();
  muatNotifikasi();
}
