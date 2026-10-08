/* Mikoshi Gear — runtime catalog admin layer.
   Applies catalog_admin.json (written by the local Catalog Studio) to category
   pages and product.html AT LOAD: card order per section, card covers, and
   per-product image galleries. Pure static host — no backend, no keys.
   Fails soft: any error logs a warning and the page keeps its built-in order. */
(function () {
  var ADMIN_URL = "catalog_admin.json";

  function fetchAdmin() {
    // cache-bust so a fresh publish is picked up as soon as Pages serves it
    return fetch(ADMIN_URL + "?v=" + Date.now(), { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function (e) { console.warn("catalog_admin.json unavailable:", e.message || e); return null; });
  }

  /* ---------- category pages ---------- */
  function applyCategory(admin, page) {
    /* detail-page links: make every card clickable (built pages only link curated
       cards). Pure DOM — no markup is modified, so text parity is preserved. */
    document.querySelectorAll("figure.g-item").forEach(function (card) {
      var cid = card.getAttribute("data-cid");
      if (!cid) return;
      var pid = cid.indexOf("fam:") === 0 ? null : cid;
      if (pid === null) {
        // family card: link to its representative variant, whose detail page
        // lists every sibling ("Also in this family")
        var v = card.querySelector(".vlist .v-s");
        pid = v ? v.textContent.trim() : null;
      }
      if (!pid) return;
      var img = card.querySelector("img");
      if (img && img.parentNode.tagName !== "A") {
        var a = document.createElement("a");
        a.href = "product.html?id=" + encodeURIComponent(pid);
        img.parentNode.insertBefore(a, img);
        a.appendChild(img);
      }
      var ph = card.querySelector(".ph");
      if (ph && ph.parentNode.tagName !== "A") {
        var a2 = document.createElement("a");
        a2.href = "product.html?id=" + encodeURIComponent(pid);
        ph.parentNode.insertBefore(a2, ph);
        a2.appendChild(ph);
      }
    });

    if (!admin) return;
    var order = (admin.order || {})[page] || null;
    if (order) {
      Object.keys(order).forEach(function (secId) {
        var sec = document.getElementById(secId);
        if (!sec) return;
        var grid = sec.querySelector(".grid");
        if (!grid) return;
        var list = order[secId] || [];
        if (!list.length) return;
        var idx = {};
        list.forEach(function (cid, i) { idx[cid] = i; });
        var cards = Array.prototype.slice.call(grid.querySelectorAll("figure.g-item"));
        var listed = [], rest = [];
        cards.forEach(function (c) {
          var cid = c.getAttribute("data-cid");
          if (cid && cid in idx) listed.push(c); else rest.push(c);
        });
        listed.sort(function (a, b) { return idx[a.getAttribute("data-cid")] - idx[b.getAttribute("data-cid")]; });
        listed.concat(rest).forEach(function (c) { grid.appendChild(c); });
      });
    }
    var covers = admin.covers || {};
    Object.keys(covers).forEach(function (cid) {
      var url = covers[cid];
      if (!url) return;
      var card = document.querySelector('figure.g-item[data-cid="' + cid.replace(/"/g, '\\"') + '"]');
      if (!card) return;
      var img = card.querySelector("img");
      if (img) { img.src = url; }
      else {
        // replace an ARRIVING placeholder with the admin photo
        var ph = card.querySelector(".ph");
        if (ph) {
          var a = document.createElement("img");
          a.src = url; a.alt = ""; a.loading = "lazy";
          ph.parentNode.replaceChild(a, ph);
        }
      }
    });
  }

  function currentPage() {
    return (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "");
  }

  if (document.querySelector("figure.g-item")) {
    var page = currentPage();
    fetchAdmin().then(function (admin) { applyCategory(admin, page); });
  }
})();
