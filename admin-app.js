  const SUPABASE_URL = "https://lnfcdtmcpiagyjnnobbo.supabase.co";
  const SUPABASE_KEY = "sb_publishable_ZUiOJTEU0DtDyC_i-8oSWA_SnUN_d9M";
  let sb = null;

  window.onerror = function (msg, src, line) {
    const el = document.getElementById("login-err");
    if (el) el.textContent = "ERR: " + msg + (line ? " (line " + line + ")" : "");
    return false;
  };
  try {
    sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  } catch (e) {
    document.getElementById("login-err").textContent = "supabase-js failed: " + e.message;
  }

  const $ = (id) => document.getElementById(id);
  const loginView = $("login-view"), appView = $("app-view");
  let current = null;       // product_id being edited
  let draft = [];           // current ordered urls (working copy)
  let dragIdx = -1;

  /* ---------- auth ---------- */
  async function showApp() {
    loginView.style.display = "none";
    appView.style.display = "block";
    buildPicker();
    await loadAll();
  }
  $("login-btn").onclick = async () => {
    $("login-err").textContent = "";
    const { error } = await sb.auth.signInWithPassword({
      email: $("email").value.trim(), password: $("pass").value,
    });
    if (error) { $("login-err").textContent = error.message; return; }
    showApp();
  };
  $("logout-btn").onclick = async () => { await sb.auth.signOut(); location.reload(); };

  /* ---------- data ---------- */
  const TABLE = "catalog_media";
  async function api() {
    const { data: { session } } = await sb.auth.getSession();
    const h = { apikey: SUPABASE_KEY, Authorization: "Bearer " + (session ? session.access_token : SUPABASE_KEY) };
    return h;
  }
  async function loadAll() {
    $("load-status").textContent = "loading…";
    try {
      const h = await api();
      const { data, error } = await sb.from(TABLE).select("product_id,image_urls,thumb_index");
      if (error) throw error;
      window.__media = {};
      (data || []).forEach((r) => { window.__media[r.product_id] = r; });
      const n = Object.keys(window.__media).length;
      $("load-status").textContent = n + " products loaded";
      $("no-table").style.display = n ? "none" : "block";
      if (current) renderEditor(current);
    } catch (e) {
      $("load-status").textContent = "load failed: " + e.message;
    }
  }
  async function saveRow() {
    if (!window.__media) return;
    const h = await api();
    const { error } = await sb.from(TABLE).upsert({
      product_id: current,
      image_urls: draft,
      thumb_index: 0,
      updated_at: new Date().toISOString(),
    }, { onConflict: "product_id" });
    if (error) throw error;
    if (!window.__media[current]) window.__media[current] = {};
    window.__media[current].image_urls = draft.slice();
    window.__media[current].thumb_index = 0;
  }

  /* ---------- picker ---------- */
  function buildPicker() {
    const picker = $("picker");
    picker.innerHTML = "";
    Object.keys(window.MIKOSHI_PRODUCTS).forEach((pid) => {
      const b = document.createElement("button");
      b.className = "pick";
      b.textContent = window.MIKOSHI_PRODUCTS[pid].name;
      b.onclick = () => { current = pid; renderEditor(pid); markPicker(b); };
      picker.appendChild(b);
    });
  }
  function markPicker(activeBtn) {
    document.querySelectorAll(".pick").forEach((b) => b.classList.remove("on"));
    if (activeBtn) activeBtn.classList.add("on");
  }

  /* ---------- editor ---------- */
  function renderEditor(pid) {
    const rec = (window.__media && window.__media[pid]);
    const stored = rec && rec.image_urls && rec.image_urls.length ? rec.image_urls : null;
    const fallback = window.MIKOSHI_IMAGES[pid] || [];
    draft = stored ? stored.slice() : fallback.slice();
    const p = window.MIKOSHI_PRODUCTS[pid];
    $("ed-name").textContent = p.name;
    $("ed-sub").textContent = pid + (stored ? " · saved order" : " · fallback order (not yet saved)");
    paintStrip();
    $("editor").style.display = "block";
    $("noproduct").style.display = "none";
    $("save-status").textContent = "";
    $("save-status").className = "status";
  }
  function paintStrip() {
    const strip = $("strip");
    strip.innerHTML = "";
    draft.forEach((url, i) => {
      const slot = document.createElement("div");
      slot.className = "slot";
      slot.draggable = true;
      slot.dataset.i = i;
      const isThumb = i === 0;
      slot.innerHTML =
        '<span class="idx' + (isThumb ? " is-thumb" : "") + '">' + (isThumb ? "★" : "#" + (i + 1)) + "</span>" +
        '<img src="' + url + '">' +
        '<div class="meta"><b>' + (isThumb ? "Thumbnail / hero" : "Image " + (i + 1)) + "</b><span>" + url.split("/").pop() + "</span></div>" +
        '<button class="thumb-btn' + (isThumb ? " on" : "") + '">Set as thumbnail</button>' +
        '<button class="del-btn" title="Delete this image">Delete</button>';
      slot.querySelector(".thumb-btn").onclick = () => { moveToTop(i); };
      slot.querySelector(".del-btn").onclick = () => { deleteAt(i); };
      slot.addEventListener("dragstart", () => { dragIdx = i; slot.classList.add("drag"); });
      slot.addEventListener("dragend", () => { slot.classList.remove("drag"); dragIdx = -1; });
      slot.addEventListener("dragover", (e) => { e.preventDefault(); });
      slot.addEventListener("drop", () => { if (dragIdx >= 0 && dragIdx !== i) { const [m] = draft.splice(dragIdx, 1); draft.splice(i, 0, m); paintStrip(); } });
      strip.appendChild(slot);
    });
  }
  function moveToTop(i) {
    const [m] = draft.splice(i, 1);
    draft.unshift(m);
    paintStrip();
  }
  function deleteAt(i) {
    const url = draft[i];
    if (!confirm("Delete this image from the product?\n" + url.split("/").pop())) return;
    draft.splice(i, 1);
    paintStrip();
    // only delete from storage if it lives in the catalog bucket (not a static /mikoshi-img asset)
    const m = url.match(/\/catalog\/([^/]+)\/([^/?#]+)/);
    if (m) {
      sb.storage.from("catalog").remove([m[1] + "/" + decodeURIComponent(m[2])])
        .then(({ error }) => { if (error) console.warn("storage delete failed (metadata still saved):", error.message); });
    }
  }

  $("seed-btn").onclick = async () => {
    const st = $("load-status");
    st.textContent = "seeding all products from static galleries…";
    try {
      const h = await api();
      const rows = Object.entries(window.MIKOSHI_IMAGES).map(([pid, urls]) => ({
        product_id: pid,
        image_urls: urls,
        thumb_index: 0,
        updated_at: new Date().toISOString(),
      }));
      const { error } = await sb.from(TABLE).upsert(rows, { onConflict: "product_id" });
      if (error) throw error;
      st.textContent = "seeded " + rows.length + " products ✓";
      await loadAll();
      if (current) renderEditor(current);
    } catch (e) {
      st.textContent = "seed failed: " + e.message;
    }
  };

  // ---------- upload ----------
  function downscale(file, max = 800) {
    return new Promise((res, rej) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        const s = Math.min(1, max / Math.max(img.width, img.height));
        const cv = document.createElement("canvas");
        cv.width = Math.max(1, Math.round(img.width * s));
        cv.height = Math.max(1, Math.round(img.height * s));
        cv.getContext("2d").drawImage(img, 0, 0, cv.width, cv.height);
        URL.revokeObjectURL(url);
        cv.toBlob((b) => (b ? res(b) : rej(new Error("canvas encode failed"))), "image/jpeg", 0.82);
      };
      img.onerror = () => { URL.revokeObjectURL(url); rej(new Error("unreadable image")); };
      img.src = url;
    });
  }
  async function uploadAll(files) {
    for (const f of files) {
      const blob = await downscale(f);
      const stamp = Date.now();
      const key = current + "/" + stamp + "-" + f.name.replace(/[^a-zA-Z0-9._-]/g, "_").slice(-60);
      const { error } = await sb.storage.from("catalog").upload(key, blob, { contentType: "image/jpeg" });
      if (error) throw error;
      draft.push(SUPABASE_URL + "/storage/v1/object/public/catalog/" + key);
    }
    paintStrip();
    await saveRow();
    $("save-status").textContent = files.length + " image" + (files.length > 1 ? "s" : "") + " added ✓ live";
    $("save-status").className = "status ok";
  }
  $("upfile").addEventListener("change", async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const st = $("save-status");
    st.textContent = "uploading " + files.length + "…";
    st.className = "status";
    try {
      await uploadAll(files);
    } catch (err) {
      st.textContent = "upload failed: " + err.message;
      st.className = "status err";
    }
    e.target.value = "";
  });

  $("save-btn").onclick = async () => {
    const st = $("save-status");
    st.textContent = "saving…";
    st.className = "status";
    try {
      await saveRow();
      st.textContent = "saved ✓ live on mikoshigear.ca";
      st.className = "status ok";
    } catch (e) {
      st.textContent = "save failed: " + e.message;
      st.className = "status err";
    }
  };

  /* ---------- resume session ---------- */
  sb.auth.getSession().then(({ data }) => {
    if (data.session) showApp();
  });
