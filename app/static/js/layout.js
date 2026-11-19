function tampilkanHalaman(isi) {
  webix.ui({
    rows: [
      buatHeader(),
      {
        cols: [
          buatSidebar(),
          { css: "app-konten", padding: LAYAR_KECIL ? 12 : 24, rows: [isi] },
        ],
      },
    ],
  });
  buatPopupNotifikasi();
  muatNotifikasi();
}

function buatHeader() {
  const p = DATA.pengguna;
  const keterangan = p.toko ? p.label_role + " · " + p.toko : p.label_role;

  let brand = '<img src="/static/img/logo-stokara.svg" alt=""> <b>Stokara</b>';
  if (!LAYAR_KECIL) {
    brand += ' <span class="app-branch">' + aman(DATA.branch) + "</span>";
  }

  let akun = '<div class="app-avatar">' + aman(p.nama.charAt(0)) + "</div>";
  if (!LAYAR_KECIL) {
    akun += '<div class="app-akun-teks">' + aman(p.nama) + "<small>" + aman(keterangan) + "</small></div>";
  }

  return {
    view: "toolbar",
    css: "app-header",
    height: 58,
    padding: { left: 8, right: 14 },
    cols: [
      { view: "icon", icon: "mdi mdi-menu", tooltip: "Buka/tutup menu", click: () => $$("menu").toggle() },
      { view: "template", css: "app-brand", borderless: true, width: LAYAR_KECIL ? 120 : 280, template: brand },
      {},
      { view: "icon", id: "lonceng", css: "app-lonceng", icon: "mdi mdi-bell-outline", tooltip: "Notifikasi", popup: "popupNotif" },
      { view: "template", css: "app-akun", borderless: true, width: LAYAR_KECIL ? 44 : 270, template: akun },
      LAYAR_KECIL
        ? { view: "icon", icon: "mdi mdi-logout", tooltip: "Keluar", click: keluar }
        : { view: "button", value: "Keluar", width: 88, css: "tombol-garis", click: keluar },
    ],
  };
}

function buatSidebar() {
  return {
    view: "sidebar",
    id: "menu",
    css: "app-sidebar",
    width: 220,
    collapsed: LAYAR_KECIL,
    data: DATA.menu.map((m) => ({ id: m.id, value: m.judul, icon: m.ikon, url: m.url })),
    on: {
      onItemClick: function (id) {
        window.location.href = this.getItem(id).url;
      },
    },
    ready: function () {
      this.select(DATA.aktif);
    },
  };
}

function judulHalaman(judul, keterangan) {
  return {
    view: "template",
    css: "judul-halaman",
    borderless: true,
    autoheight: true,
    template: "<h2>" + aman(judul) + "</h2><p>" + aman(keterangan) + "</p>",
  };
}

function kartuTabel(isiToolbar, tabel) {
  return {
    css: "kartu-tabel",
    rows: [
      { view: "toolbar", css: "toolbar-tabel", height: 58, padding: { left: 12, right: 12 }, cols: isiToolbar },
      tabel,
    ],
  };
}

function buatJendela(id, judul, elemen, saatSimpan, lebar) {
  webix.ui({
    view: "window",
    id: id,
    modal: true,
    position: "center",
    width: lebar || 480,
    fullscreen: LAYAR_KECIL,
    css: "jendela",
    head: {
      view: "toolbar",
      css: "jendela-head",
      height: 54,
      padding: { left: 16, right: 6 },
      cols: [
        { view: "label", id: id + "_judul", label: judul },
        { view: "icon", icon: "mdi mdi-close", click: () => $$(id).hide() },
      ],
    },
    body: {
      view: "form",
      id: id + "_form",
      padding: 18,
      elementsConfig: { labelPosition: "top" },
      elements: elemen.concat([
        { height: 6 },
        {
          cols: [
            {},
            { view: "button", value: "Batal", width: 100, css: "tombol-garis", click: () => $$(id).hide() },
            { view: "button", value: "Simpan", width: 120, css: "webix_primary", click: saatSimpan },
          ],
        },
      ]),
    },
  });
}


function buatPopupNotifikasi() {
  webix.ui({
    view: "popup",
    id: "popupNotif",
    css: "popup-notif",
    width: LAYAR_KECIL ? 320 : 360,
    body: {
      rows: [
        {
          view: "toolbar", css: "notif-head", height: 46, padding: { left: 14, right: 6 },
          cols: [
            { view: "label", label: "Notifikasi" },
            { view: "button", value: "Tandai semua dibaca", css: "tombol-teks", width: 160, click: tandaiNotifikasiDibaca },
          ],
        },
        {
          view: "list",
          id: "daftarNotif",
          css: "daftar-notif",
          autoheight: true,
          maxHeight: 380,
          scroll: "y",
          select: false,
          type: { height: 84 },
          template: function (n) {
            if (n.kosong) {
              return '<div class="notif-kosong">Belum ada notifikasi.</div>';
            }
            return (
              '<div class="notif-item' + (n.dibaca ? "" : " baru") + '">' +
              '<span class="notif-titik"></span>' +
              "<div><b>" + aman(n.judul) + "</b>" +
              "<small>" + aman(n.pesan) + "</small>" +
              "<small>" + tanggalWaktu(n.waktu) + "</small></div>" +
              "</div>"
            );
          },
          on: {
            onItemClick: function (id) {
              const n = this.getItem(id);
              if (!n.kosong) window.location.href = n.link;
            },
          },
        },
      ],
    },
  });
}

async function muatNotifikasi() {
  const data = await api("GET", "/api/notifikasi");
  if (!data) return;

  const lonceng = $$("lonceng");
  lonceng.config.badge = data.belum_dibaca > 0 ? data.belum_dibaca : "";
  lonceng.refresh();

  const daftar = $$("daftarNotif");
  daftar.clearAll();
  daftar.parse(data.daftar.length > 0 ? data.daftar : [{ id: "kosong", kosong: true }]);
}

async function tandaiNotifikasiDibaca() {
  const hasil = await api("POST", "/api/notifikasi/baca");
  if (hasil) muatNotifikasi();
}

async function keluar() {
  await api("POST", "/api/logout");
  window.location.href = "/login";
}
