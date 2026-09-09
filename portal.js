
/* surface any JS error into the login card */
window.onerror = function (msg, src, line) {
  const el = document.getElementById("login-err");
  if (el) el.textContent = "ERR: " + msg + (line ? " (line " + line + ")" : "");
  return false;
};
document.getElementById("boot-status").textContent = "JS loaded ✓";
const SUPABASE_URL = "https://lnfcdtmcpiagyjnnobbo.supabase.co";
const SUPABASE_KEY = "sb_publishable_ZUiOJTEU0DtDyC_i-8oSWA_SnUN_d9M";

let supabase = null;
try {
  if (typeof window.supabase === "undefined") throw new Error("supabase-js failed to load — check network");
  supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
} catch (e) {
  document.getElementById("login-err").textContent = "ERR: " + e.message;
}

const $ = id => document.getElementById(id);
let allShops = [];
let filtered = [];
let page = 0;
const PAGE_SIZE = 25;

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2000);
}

/* ---------- auth ---------- */
async function login() {
  const btn = $("login-btn");
  const email = $("login-email").value.trim();
  const pass = $("login-pass").value;
  $("login-err").textContent = "";
  if (!supabase) { $("login-err").textContent = "ERR: client not initialized"; return; }
  if (!email || !pass) { $("login-err").textContent = "Enter email and password"; return; }
  btn.textContent = "Connecting…";
  btn.disabled = true;
  try {
    const { error } = await supabase.auth.signInWithPassword({ email, password: pass });
    if (error) { $("login-err").textContent = error.message; return; }
    enterApp();
  } catch (e) {
    $("login-err").textContent = "ERR: " + e.message;
  } finally {
    btn.textContent = "Enter";
    btn.disabled = false;
  }
}
$("login-btn").addEventListener("click", login);
$("login-pass").addEventListener("keydown", e => { if (e.key === "Enter") login(); });
$("logout-btn").addEventListener("click", async () => {
  await supabase.auth.signOut();
  $("app-view").style.display = "none";
  $("login-view").style.display = "flex";
});

async function enterApp() {
  $("login-view").style.display = "none";
  $("app-view").style.display = "block";
  const { data: { user } } = await supabase.auth.getUser();
  $("whoami").textContent = user ? user.email : "";
  await loadShops();
}

/* ---------- data ---------- */
async function loadShops() {
  const { data, error } = await supabase.from("shops").select("*").order("name");
  if (error) {
    $("rows").innerHTML = `<tr><td colspan="4" class="empty">${error.message}</td></tr>`;
    return;
  }
  allShops = data || [];
  applyFilters();
}

function applyFilters() {
  const q = $("search").value.toLowerCase();
  const st = $("status-filter").value;
  const em = $("email-filter").value;
  filtered = allShops.filter(s => {
    if (q && !(s.name + " " + (s.city||"") + " " + (s.email||"")).toLowerCase().includes(q)) return false;
    if (st && s.status !== st) return false;
    if (em === "has" && !s.email) return false;
    if (em === "none" && s.email) return false;
    return true;
  });
  page = 0;
  render();
}

function render() {
  const start = page * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);
  $("count").textContent = `${filtered.length} shops`;
  $("empty").style.display = filtered.length ? "none" : "block";
  $("pageinfo").textContent = filtered.length ? `${start + 1}–${start + slice.length} of ${filtered.length}` : "";
  $("prev").disabled = page === 0;
  $("next").disabled = start + PAGE_SIZE >= filtered.length;

  $("rows").innerHTML = slice.map(s => {
    const statuses = ["prospect", "emailed", "samples", "order", "dead"];
    const opts = statuses.map(x => `<option value="${x}" ${s.status === x ? "selected" : ""}>${x}</option>`).join("");
    return `<tr data-id="${s.id}">
      <td>
        <div class="shop-name">${s.name}</div>
        <div class="shop-phone">${s.city || ""}${s.phone ? " · " + s.phone : ""}</div>
      </td>
      <td class="shop-email">${s.email ? `<a href="mailto:${s.email}">${s.email}</a>` : '<span style="color:#4d545e">—</span>'}</td>
      <td><select class="status-pill st-${s.status}" data-field="status" data-id="${s.id}">${opts}</select></td>
      <td class="notes-cell"><input data-field="notes" data-id="${s.id}" value="${(s.notes || "").replace(/"/g, "&quot;")}" placeholder="add note…"></td>
    </tr>`;
  }).join("");
}

/* ---------- edits ---------- */
$("rows").addEventListener("change", async e => {
  const el = e.target;
  if (!el.dataset.field) return;
  const id = el.dataset.id;
  const field = el.dataset.field;
  const value = field === "status" ? el.value : el.value;
  const { error } = await supabase.from("shops").update({ [field]: value }).eq("id", id);
  if (error) { toast("ERR: " + error.message); return; }
  if (field === "status") {
    el.className = "status-pill st-" + value;
    toast("Status → " + value);
  } else {
    toast("Note saved");
  }
});

/* ---------- filters / pager ---------- */
$("search").addEventListener("input", applyFilters);
$("status-filter").addEventListener("change", applyFilters);
$("email-filter").addEventListener("change", applyFilters);
$("prev").addEventListener("click", () => { page--; render(); });
$("next").addEventListener("click", () => { page++; render(); });

/* ---------- session restore ---------- */
supabase.auth.getSession().then(({ data }) => {
  if (data.session) enterApp();
});
