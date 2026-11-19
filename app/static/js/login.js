webix.ready(function () {
  const logo = '<img src="/static/img/logo-stokara.svg" width="38" height="38" alt="">';
  const judulBesar = "Stok gudang terkendali,<br>permintaan toko terpenuhi.";

  let isiPanel;
  if (LAYAR_KECIL) {
    isiPanel =
      '<div class="login-brand">' + logo + " Stokara</div>" +
      '<div class="login-judul-besar">' + judulBesar + "</div>";
  } else {
    isiPanel =
      '<div class="login-brand">' + logo + " Stokara</div>" +
      "<div>" +
      '<div class="login-judul-besar">' + judulBesar + "</div>" +
      "<p>Kelola stok gudang, permintaan toko, dan kebutuhan restock dalam satu aplikasi.</p>" +
      '<div class="login-fitur">' +
      '<div><span class="mdi mdi-package-variant-closed"></span> Stok gudang terpantau setiap saat</div>' +
      '<div><span class="mdi mdi-swap-horizontal"></span> Permintaan toko tercatat dari pengajuan hingga diterima</div>' +
      '<div><span class="mdi mdi-trending-up"></span> Saran restock dari data permintaan 30 hari terakhir</div>' +
      "</div>" +
      "</div>" +
      '<div class="login-hak-cipta">© 2026 Stokara</div>';
  }

  const panel = {
    view: "template",
    css: LAYAR_KECIL ? "login-kiri kecil" : "login-kiri",
    borderless: true,
    template: isiPanel,
  };
  if (LAYAR_KECIL) {
    panel.height = 170;
  }

  const form = {
    view: "form",
    id: "formLogin",
    css: "login-form",
    borderless: true,
    elements: [
      {
        view: "template",
        css: "login-judul",
        borderless: true,
        height: 74,
        template: "<h1>Selamat datang</h1><p>Silakan masuk ke akun Anda.</p>",
      },
      {
        view: "text", name: "username", label: "Username", labelPosition: "top",
        placeholder: "Masukkan username", required: true, invalidMessage: "Username wajib diisi",
        on: { onEnter: enterDiUsername },
      },
      {
        view: "text", type: "password", name: "password", id: "isiPassword", label: "Password", labelPosition: "top",
        placeholder: "Masukkan password", required: true, invalidMessage: "Password wajib diisi",
        on: { onEnter: masuk },
      },
      { height: 6 },
      { view: "button", id: "tombolMasuk", value: "Masuk", css: "webix_primary", height: 42, click: masuk },
    ],
  };

  if (!LAYAR_KECIL) {
    form.width = 360;
  }

  const sisiForm = {
    css: "login-kanan",
    padding: LAYAR_KECIL ? 10 : 0,
    cols: [{}, { rows: [{}, form, {}] }, {}],
  };
  if (LAYAR_KECIL) {
    sisiForm.cols = [{ rows: [form, {}] }];
  }

  webix.ui(LAYAR_KECIL ? { rows: [panel, sisiForm] } : { cols: [panel, sisiForm] });
  $$("formLogin").focus("username");
});

function enterDiUsername() {
  if ($$("isiPassword").getValue() === "") {
    $$("isiPassword").focus();
  } else {
    masuk();
  }
}

async function masuk() {
  const tombol = $$("tombolMasuk");
  if (!tombol.isEnabled()) {
    return;
  }
  const form = $$("formLogin");
  if (!form.validate()) {
    return;
  }

  tombol.disable();
  const hasil = await api("POST", "/api/login", form.getValues());
  if (!hasil) {
    tombol.enable();
    return;
  }
  window.location.href = hasil.redirect;
}
