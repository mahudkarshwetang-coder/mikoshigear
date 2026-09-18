/* Mikoshi Gear — catalog media live layer.
   Reads ordered image lists from Supabase catalog_media (public read).
   Falls back to window.MIKOSHI_IMAGES (static order) when the project is
   unreachable, so the site never breaks offline. */
(function () {
  const URL = "https://lnfcdtmcpiagyjnnobbo.supabase.co";
  const KEY = "sb_publishable_ZUiOJTEU0DtDyC_i-8oSWA_SnUN_d9M";

  async function fetchMedia(products) {
    try {
      /* PostgREST: comma-joined eq filters are invalid and silently return [];
         use in.(...) for multi-product reads. */
      const qs = "product_id=in.(" + products.map((p) => encodeURIComponent(p)).join(",") + ")";
      const res = await fetch(
        `${URL}/rest/v1/catalog_media?select=product_id,image_urls,thumb_index&${qs}`,
        { headers: { apikey: KEY, Authorization: `Bearer ${KEY}` } }
      );
      if (!res.ok) throw new Error("rest " + res.status);
      const rows = await res.json();
      const out = {};
      for (const r of rows) out[r.product_id] = { urls: r.image_urls || [], thumb: r.thumb_index || 0 };
      return out;
    } catch (e) {
      console.warn("catalog_media unreachable, using static fallback:", e.message || e);
      return null;
    }
  }

  function ordered(pid, live) {
    const st = window.MIKOSHI_IMAGES[pid] || [];
    if (!live || !live[pid] || !live[pid].urls.length) return { urls: st, thumb: 0 };
    return { urls: live[pid].urls, thumb: live[pid].thumb };
  }

  window.MIKOSHI_MEDIA = {
    /* Returns [{pid, urls, thumb}] resolved for the requested product ids. */
    async load(products) {
      const live = await fetchMedia(products);
      return products.map((pid) => ({ pid, ...ordered(pid, live) }));
    },
  };
})();
