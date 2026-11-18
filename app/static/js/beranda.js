/* =====================================================================
 * Beranda: kartu sambutan + kartu menu sesuai role.
 * ===================================================================== */

webix.ready(function () {
  const p = DATA.pengguna;

  // Kartu sambutan (ungu)
  let info = '<span class="sambutan-badge">' + aman(p.label_role) + "</span>";
  info += '<span class="sambutan-info">' + aman(p.toko || DATA.branch) + "</span>";

  const sambutan = {
    view: "template",
    css: "kartu-sambutan",
    borderless: true,
    height: LAYAR_KECIL ? 130 : 120,
    template:
      "<div>" +
      '<div class="sambutan-kecil">Selamat datang,</div>' +
      '<div class="sambutan-nama">' + aman(p.nama) + "</div>" +
      info +
      "</div>" +
      (LAYAR_KECIL ? "" : '<img src="/static/img/logo-stokara.svg" width="64" height="64" alt="">'),
  };

  // Kartu menu: semua menu kecuali Beranda
  const kartuMenu = {
    view: "dataview",
    id: "kartuMenu",
    css: "kartu-menu",
    borderless: true,
    select: false,
    scroll: "auto", // scrollbar hanya muncul kalau kartunya tidak muat
    xCount: LAYAR_KECIL ? 1 : 3, // jumlah kartu per baris
    type: { width: "auto", height: 116 }, // "auto" = lebar kartu menyesuaikan layar
    data: DATA.menu.filter((m) => m.id !== "beranda"),
    template: function (m) {
      // Label kecil di pojok kanan atas, contoh "2 menunggu persetujuan"
      let label = "";
      for (const b of m.label || []) {
        label += '<span class="badge ' + b.warna + '">' + aman(b.teks) + "</span>";
      }
      return (
        '<div class="kartu-isi">' +
        '<div class="kartu-label">' + label + "</div>" +
        '<span class="' + m.ikon + '"></span>' +
        "<b>" + aman(m.judul) + "</b>" +
        "<small>" + aman(m.keterangan) + "</small>" +
        "</div>"
      );
    },
    on: {
      onItemClick: function (id) {
        window.location.href = this.getItem(id).url;
      },
    },
  };

  tampilkanHalaman({
    rows: [
      sambutan,
      { view: "template", css: "label-seksi", borderless: true, height: 44, template: "MENU ANDA" },
      kartuMenu,
    ],
  });

  muatLabel();
});

// Ambil angka "perlu ditindaklanjuti" lalu tempel ke kartu menu yang sesuai
async function muatLabel() {
  const data = await api("GET", "/api/beranda");
  if (!data) return;
  const kartu = $$("kartuMenu");
  for (const idMenu in data) {
    if (kartu.exists(idMenu)) kartu.updateItem(idMenu, { label: data[idMenu] });
  }
}
