(() => {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor("#0d0a16");
      tg.setBackgroundColor("#07060c");
    } catch (_) {}
  }

  const state = {
    initData: tg?.initData || "",
    catalog: {},
    category: null,
    product: null,
    me: null,
    promo: null,
    cryptoEnabled: false,
    starsUser: "mukhammad_im",
    channelUrl: null,
    apkUrl: null,
    pendingOrderId: null,
  };

  const $ = (id) => document.getElementById(id);
  const show = (el) => el && el.classList.remove("hidden");
  const hide = (el) => el && el.classList.add("hidden");

  function toast(msg) {
    const el = $("toast");
    el.textContent = msg;
    show(el);
    clearTimeout(toast._t);
    toast._t = setTimeout(() => hide(el), 2800);
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function api(path, opts = {}) {
    const headers = Object.assign(
      { "Content-Type": "application/json", "X-Telegram-Init-Data": state.initData },
      opts.headers || {}
    );
    const res = await fetch(path, { ...opts, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText || "Ошибка");
    return data;
  }

  /* ── Onboarding ── */
  async function runOnboarding() {
    show($("onboard"));
    hide($("shop"));
    $("obStatus").textContent = "✨ Проверяем подписку…";
    show($("obLoader"));
    hide($("obActions"));
    hide($("obNick"));

    try {
      const data = await api("/api/bootstrap");
      applyBootstrap(data);

      if (data.me?.registered && data.me?.nickname) {
        $("obStatus").textContent = "✅ Добро пожаловать!";
        hide($("obLoader"));
        setTimeout(openShop, 500);
        return;
      }

      if (!data.subscribed) {
        $("obStatus").innerHTML = "📢 Подпишись на канал,<br>чтобы открыть магазин";
        hide($("obLoader"));
        if (data.channel_url) {
          $("subLink").href = data.channel_url;
          show($("subLink"));
        } else {
          hide($("subLink"));
        }
        show($("obActions"));
        return;
      }

      // subscribed but no nick
      showNickStep();
    } catch (e) {
      hide($("obLoader"));
      $("obStatus").textContent = "⚠️ " + (e.message || "Ошибка загрузки");
      // allow retry as subscribe check
      show($("obActions"));
    }
  }

  function applyBootstrap(data) {
    state.catalog = data.catalog || {};
    state.me = data.me;
    state.cryptoEnabled = !!data.crypto_enabled;
    state.starsUser = data.stars_user || "mukhammad_im";
    state.channelUrl = data.channel_url;
    state.apkUrl = data.apk_url;
    if (state.apkUrl) {
      $("apkFull").href = state.apkUrl;
      $("btnApk").onclick = () => openApk();
    }
  }

  function openApk() {
    if (!state.apkUrl) {
      toast("Ссылка на APK не настроена");
      return;
    }
    if (tg?.openLink) tg.openLink(state.apkUrl);
    else window.open(state.apkUrl, "_blank");
  }

  function showNickStep() {
    $("obStatus").textContent = "🎮 Регистрация аккаунта";
    hide($("obLoader"));
    hide($("obActions"));
    show($("obNick"));
    $("nickInput").focus();
  }

  $("btnCheckSub").onclick = async () => {
    $("obStatus").textContent = "🔍 Проверяем подписку…";
    show($("obLoader"));
    hide($("obActions"));
    try {
      const data = await api("/api/check_sub", { method: "POST", body: "{}" });
      if (!data.subscribed) {
        hide($("obLoader"));
        $("obStatus").innerHTML = "❌ Подписка не найдена.<br>Подпишись и нажми снова";
        show($("obActions"));
        toast("Подписка не найдена");
        return;
      }
      toast("✅ Подписка подтверждена");
      showNickStep();
    } catch (e) {
      hide($("obLoader"));
      $("obStatus").textContent = e.message;
      show($("obActions"));
    }
  };

  $("btnReg").onclick = async () => {
    const nick = $("nickInput").value.trim();
    $("nickErr").textContent = "";
    if (!/^[A-Za-z0-9_\[\]-]{3,24}$/.test(nick)) {
      $("nickErr").textContent = "⚠️ Ник 3–24: латиница, цифры, _ - []";
      return;
    }
    $("btnReg").disabled = true;
    $("obStatus").textContent = "🔎 Ищем аккаунт в базе…";
    show($("obLoader"));
    try {
      const data = await api("/api/register", {
        method: "POST",
        body: JSON.stringify({ nickname: nick }),
      });
      state.me = data.me || state.me;
      state.me.nickname = nick;
      state.me.registered = true;
      hide($("obLoader"));
      $("obStatus").textContent = "✅ Аккаунт подтверждён!";
      toast("🎉 Добро пожаловать, " + nick);
      setTimeout(openShop, 600);
    } catch (e) {
      hide($("obLoader"));
      $("obStatus").textContent = "🎮 Введи игровой ник";
      $("nickErr").textContent = "❌ " + (e.message || "Аккаунт не найден");
    } finally {
      $("btnReg").disabled = false;
    }
  };

  function openShop() {
    hide($("onboard"));
    show($("shop"));
    $("userChip").textContent = state.me?.nickname || ("ID " + (state.me?.telegram_id || "?"));
    renderCats();
    renderProducts();
    renderProfile();
    try { tg?.HapticFeedback?.notificationOccurred("success"); } catch (_) {}
  }

  /* ── Tabs / catalog ── */
  document.querySelectorAll(".tab").forEach((b) =>
    b.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
      document.querySelectorAll(".panel").forEach((p) =>
        p.classList.toggle("active", p.id === "tab-" + b.dataset.tab)
      );
      if (b.dataset.tab === "orders") loadOrders();
      if (b.dataset.tab === "profile") renderProfile();
    })
  );

  function renderCats() {
    const box = $("cats");
    box.innerHTML = "";
    const keys = Object.keys(state.catalog);
    if (!state.category && keys.length) state.category = keys[0];
    keys.forEach((k) => {
      const btn = document.createElement("button");
      btn.className = "cat" + (k === state.category ? " active" : "");
      btn.textContent = state.catalog[k].title;
      btn.onclick = () => {
        state.category = k;
        renderCats();
        renderProducts();
      };
      box.appendChild(btn);
    });
  }

  function renderProducts() {
    const box = $("products");
    box.innerHTML = "";
    const sec = state.catalog[state.category];
    if (!sec) return;
    sec.products.forEach((p, i) => {
      const el = document.createElement("div");
      el.className = "product";
      el.style.animationDelay = i * 0.04 + "s";
      el.innerHTML = `
        <div>
          <h4>${escapeHtml(p.title)}</h4>
          <div class="meta">${escapeHtml(p.kind)}</div>
        </div>
        <div class="right">
          <div class="cost">${p.price} ₽</div>
          <button class="btn btn-glow">Купить</button>
        </div>`;
      el.querySelector("button").onclick = () => openBuy(p);
      box.appendChild(el);
    });
  }

  function openBuy(p) {
    state.product = p;
    $("mTitle").textContent = p.title;
    let price = p.price;
    if (state.promo) {
      price = Math.max(1, Math.floor((p.price * (100 - state.promo.percent)) / 100));
      $("mPrice").textContent = `${price} ₽  (−${state.promo.percent}%)`;
    } else {
      $("mPrice").textContent = `${price} ₽`;
    }
    $("mNick").textContent = "🎮 Ник: " + (state.me?.nickname || "—");
    $("mStatus").textContent = "";
    $("payCrypto").style.display = state.cryptoEnabled ? "block" : "none";
    show($("modal"));
  }

  $("mClose").onclick = () => hide($("modal"));

  async function createOrder(method) {
    if (!state.product) return;
    $("mStatus").textContent = "⏳ Создаём заказ…";
    $("payStars").disabled = true;
    $("payCrypto").disabled = true;
    try {
      const data = await api("/api/order", {
        method: "POST",
        body: JSON.stringify({
          product_id: state.product.id,
          payment_method: method,
          promo: state.promo?.code || null,
        }),
      });
      hide($("modal"));
      state.pendingOrderId = data.order_id;
      if (method === "crypto" && data.pay_url) {
        toast("🪙 Открываем CryptoBot…");
        if (tg?.openLink) tg.openLink(data.pay_url);
        else window.open(data.pay_url, "_blank");
        loadOrders();
        document.querySelector('.tab[data-tab="orders"]').click();
      } else {
        $("payStarsUser").textContent = "@" + state.starsUser;
        $("payText").innerHTML = `Заказ <b>#${data.order_id}</b> — <b>${data.price} ₽</b>`;
        $("uploadStatus").textContent = "";
        $("receiptFile").value = "";
        show($("payModal"));
      }
    } catch (e) {
      $("mStatus").textContent = "❌ " + e.message;
      toast(e.message);
    } finally {
      $("payStars").disabled = false;
      $("payCrypto").disabled = false;
    }
  }

  $("payStars").onclick = () => createOrder("stars");
  $("payCrypto").onclick = () => createOrder("crypto");
  $("payClose").onclick = () => {
    hide($("payModal"));
    document.querySelector('.tab[data-tab="orders"]').click();
  };
  $("okClose").onclick = () => {
    hide($("okModal"));
    document.querySelector('.tab[data-tab="orders"]').click();
  };

  $("receiptFile").onchange = async (ev) => {
    const file = ev.target.files?.[0];
    if (!file || !state.pendingOrderId) return;
    $("uploadStatus").textContent = "⏳ Отправляем чек…";
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("order_id", String(state.pendingOrderId));
      const res = await fetch("/api/receipt", {
        method: "POST",
        headers: { "X-Telegram-Init-Data": state.initData },
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Ошибка загрузки");
      hide($("payModal"));
      show($("okModal"));
      toast("✅ Чек отправлен админам");
      try { tg?.HapticFeedback?.notificationOccurred("success"); } catch (_) {}
      loadOrders();
    } catch (e) {
      $("uploadStatus").textContent = "❌ " + e.message;
      toast(e.message);
    }
  };

  async function loadOrders() {
    const box = $("ordersList");
    box.innerHTML = "<p class='muted'>⏳ Загрузка…</p>";
    try {
      const data = await api("/api/orders");
      if (!data.orders?.length) {
        box.innerHTML = "<p class='muted'>Пока пусто — выбери товар в магазине</p>";
        return;
      }
      const icons = {
        delivered: "✅", rejected: "❌", cancelled: "🚫", review: "⏳",
        awaiting_receipt: "📷", awaiting_crypto: "🪙", processing: "⚙️",
      };
      box.innerHTML = "";
      data.orders.forEach((o) => {
        const el = document.createElement("div");
        el.className = "order";
        el.innerHTML = `
          <div><b>${icons[o.status] || "•"} #${o.id}</b> ${escapeHtml(o.item_title)}</div>
          <div>${o.price} ₽ · ${escapeHtml(o.payment_method || "")}</div>
          <div class="st">${escapeHtml(o.status)} · ${escapeHtml(o.created_at || "")}</div>`;
        box.appendChild(el);
      });
    } catch (e) {
      box.innerHTML = `<p class="muted">${escapeHtml(e.message)}</p>`;
    }
  }

  function renderProfile() {
    const m = state.me || {};
    const p = m.player || {};
    $("profileCard").innerHTML = `
      <h3>👤 Профиль</h3>
      <div class="stat-grid">
        <div class="stat">Ник<b>${escapeHtml(m.nickname || "—")}</b></div>
        <div class="stat">TG ID<b>${m.telegram_id || "—"}</b></div>
        <div class="stat">⭐ Уровень<b>${p.level ?? "—"}</b></div>
        <div class="stat">🛡 Админ<b>${p.admin ?? "—"}</b></div>
        <div class="stat">🧍 Скин<b>${p.skin ?? "—"}</b></div>
        <div class="stat">💰 Валюта<b>${p.money ?? "—"}</b></div>
      </div>`;
  }

  $("promoBtn").onclick = async () => {
    const code = $("promoInput").value.trim();
    if (!code) return;
    try {
      const data = await api("/api/promo", { method: "POST", body: JSON.stringify({ code }) });
      state.promo = data;
      $("promoMsg").textContent = `✅ ${data.code} −${data.percent}% на следующий заказ`;
      toast("🎟 Промокод применён");
    } catch (e) {
      state.promo = null;
      $("promoMsg").textContent = "❌ " + e.message;
    }
  };

  runOnboarding();
})();
