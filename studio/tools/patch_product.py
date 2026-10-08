#!/usr/bin/env python3
"""Rewrite product.html's script tail so the shared detail page serves ALL 573
catalog lines (not just the 20 curated), with admin-overridable galleries.
Byte-safe: reads the live file, replaces from the first <script src="products.js">
to EOF, writes CRLF line endings (matching the repo)."""
import io, re, sys
from pathlib import Path

f = Path("product.html")
raw = f.read_text(encoding="utf-8")
marker = '<script src="products.js"></script>'
i = raw.find(marker)
if i < 0:
    sys.exit("marker not found")
head = raw[:i]

TAIL = '''<script src="products.js"></script>
<script src="catalog.js"></script>
<script src="catalog-admin.js"></script>
<script>
  const id = new URLSearchParams(location.search).get("id") || "";
  const cat = (window.MIKOSHI_CATALOG || {})[id] || null;
  const prod = (window.MIKOSHI_PRODUCTS || {})[id] || null;
  const p = prod ? { name: prod.name, notes: prod.notes, price: prod.price, cat: prod.cat } :
            (cat ? { name: cat.name, notes: cat.notes, price: cat.price, cat: cat.page } : null);

  if (!p) {
    document.getElementById("title").textContent = "Product not found";
    document.getElementById("notes").textContent = "This product doesn't exist \\u2014 head back to the catalog.";
  } else {
    document.title = "Mikoshi Gear \\u2014 " + p.name;
    document.getElementById("cat").textContent = p.cat || "Mikoshi Gear";
    document.getElementById("title").textContent = p.name;
    document.getElementById("notes").textContent = p.notes;
    document.getElementById("price").textContent = p.price;
    const backMap = { case: "cases.html", cable: "cables.html", adapter: "adapters.html", novelty: "adapters.html",
                      cases: "cases.html", cables: "cables.html", adapters: "adapters.html",
                      chargers: "chargers.html", power: "power.html", mounts: "mounts.html" };
    document.getElementById("back-link").href = backMap[p.cat] || "index.html";

    // gallery resolution: admin override > curated static gallery > catalog single image
    function gallery() {
      return fetch("catalog_admin.json?v=" + Date.now(), { cache: "no-store" })
        .then(r => r.ok ? r.json() : null).catch(() => null)
        .then(admin => {
          const ov = admin && admin.images && admin.images[id];
          if (ov && ov.length) return { urls: ov, thumb: 0 };
          const st = (window.MIKOSHI_IMAGES || {})[id];
          if (st && st.length) return { urls: st, thumb: 0 };
          if (cat && cat.imgs && cat.imgs.length) return { urls: cat.imgs, thumb: 0 };
          return { urls: [], thumb: 0 };
        });
    }
    gallery().then(m => {
      if (!m.urls.length) return;
      const hero = document.getElementById("hero");
      const thumbs = document.getElementById("thumbs");
      let idx = Math.min(m.thumb, m.urls.length - 1);
      function paint() {
        hero.src = m.urls[idx];
        hero.alt = p.name;
        thumbs.innerHTML = "";
        m.urls.forEach((u, i) => {
          const t = document.createElement("img");
          t.src = u; t.alt = (i + 1);
          if (i === idx) t.className = "on";
          t.onclick = () => { idx = i; paint(); };
          thumbs.appendChild(t);
        });
      }
      paint();
    });

    // family cross-links: every sibling variant of a folded family card
    if (cat && cat.fam) {
      const sibs = Object.values(window.MIKOSHI_CATALOG || {})
        .filter(v => v.fam === cat.fam && v.pid !== id)
        .sort((a, b) => a.name.localeCompare(b.name));
      if (sibs.length) {
        const blob = document.getElementById("blob");
        const wrap = document.createElement("p");
        wrap.className = "notes";
        wrap.style.marginTop = "14px";
        wrap.innerHTML = "<b>Also in this family:</b> " + sibs.map(s =>
          '<a href="product.html?id=' + encodeURIComponent(s.pid) + '" style="color:inherit">' +
          s.name.replace(/^Toocki\\s+/, "").replace(/[<>&"]/g, c => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c])) +
          " \\u00b7 " + s.price + "</a>").join(" \\u00b7 ");
        blob.parentNode.insertBefore(wrap, blob.nextSibling);
      }
    }
  }
</script>
</body>
</html>
'''

out = head + TAIL
out = out.replace("\r\n", "\n").replace("\n", "\r\n")
f.write_bytes(out.encode("utf-8"))
print("product.html rewritten:", len(out), "chars; CRLF preserved")
