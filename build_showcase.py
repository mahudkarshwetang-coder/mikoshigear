#!/usr/bin/env python3
"""Mikoshi Gear showcase rebuild — 2026-09-18 session products + live catalog media.
Generates cases/cables/adapters.html (cards → product.html?id=SLUG, live thumbnails via
catalog_media table with static fallback), product.html gallery data in products.js.
Run from repo root: python3 build_showcase.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
IMG = "mikoshi-img/showcase/"
DETAIL = "https://mikoshigear.ca/mikoshi-img/detail/"
PH = ("<div class='ph'><b>ARRIVING</b><span>with shipment</span></div>")

# ---- product dataset: slug, cat, name, price, notes, img (None = placeholder) ----
P = []
def add(slug, cat, name, price, notes, img):
    P.append(dict(slug=slug, cat=cat, name=name, price=price, notes=notes, img=img))

add("ins-style", "case", "Ins Style Aesthetic Case (Korean / Japanese)", "Wholesale $3.50 · MOQ 20 — samples available",
    "iPhone 11–17 · TPU+PC soft-hard hybrid · full coverage · raised camera bezel · anti-dirt · pink shown", "p01-ins-style.jpg")
add("candy-double-mag", "case", "Candy Double-Layer Magnetic Case", "Wholesale $3.50 · MOQ 20 — samples available",
    "iPhone 11–17 · shockproof TPU+PC · transparent matte · MagSafe · 6 colours: pink·sage·grey·sky·mint·cream", "p03-double-layer-mag.jpg")
add("ultra-thin-contrast", "case", "Ultra-Thin Contrast Magnetic Case", "Wholesale $4.00 · MOQ 20 — samples available",
    "iPhone 13–18 (Pro/Pro Max/17 Air) · ultra-thin matte · orange accent ring · MagSafe · 3 colours", "p04-ultra-thin-contrast.jpg")
add("slim-heat", "case", "Slim Solid-Color Heat-Dissipating Case", "Wholesale $4.40 · MOQ 20 — samples available",
    "iPhone 13–17 · ultra-slim matte hard-shell · heat-dissipation ring · scratch-resistant · cream shown", "p05-slim-heat.jpg")
add("charming-eye", "case", "Skin-Feel 'Charming Eye' Case", "Wholesale $4.10 · MOQ 20 — samples available",
    "iPhone 11–17 + XR/XS/XS Max · matte skin-feel · eye graphic · metallic accent ring · 3 colours", "p06-charming-eye.jpg")
add("shockproof-matte-luxury", "case", "Shockproof Matte Luxury Case", "Wholesale $3.50 · MOQ 20 — samples available",
    "iPhone 17/16/15/14/13/12/11 Pro Max/XS/7/8 Plus/SE · PC shockproof + waterproof · electroplate colour frame · translucent matte back · 5 colours", "p18-shockproof.jpg")
add("xframe-aluminum", "case", "Aluminum X-Frame Bare Case", "Wholesale $20.00 · MOQ 20 — samples available",
    "iPhone 13–17 Pro Max · aluminium alloy exoskeleton · X-back structural frame · bezel-less bare design · open back for air cooling · 5 colours: gold·silver·orange·grey·blue", "p19-xframe.jpg")

add("2in1-wireless", "cable", "2-in-1 100W + Wireless Cable", "Wholesale $12.50 · MOQ 20 — samples available",
    "USB-C 100W + 2.5W wireless puck (watch/earbuds) · E-Marker · braided · ships by Oct 14", "p15-2in1-wireless.jpg")
add("240w-display", "cable", "240W Display Cable (live wattage)", "Wholesale $4.00–8.00 · MOQ 20 — samples available",
    "USB-C · real-time W readout · braided + metal housing · 480Mbps · 1/2m · ships by Oct 14", "p09-240w-display.jpg")
add("240w-elbow", "cable", "240W Elbow 90° Cable", "Wholesale $7.00 · MOQ 20 — samples available",
    "USB-C · L-shaped elbow · zinc-alloy shell · braided nylon · 1.5m", "p08-240w-elbow.jpg")
add("240w-straight", "cable", "240W Max Cable", "Wholesale $7.00 · MOQ 20 — samples available",
    "USB-C · zinc-alloy shell · reinforced strain relief · braided · 1.5m", "p07-240w-straight.jpg")
add("100w-realcore", "cable", "100W Real-Core Cable", "Wholesale $3.00–5.50 · MOQ 20 — samples available",
    "USB-C · six-strand core · anti-interference · gold-plated · 4 colours", "p10-100w-realcore.jpg")
add("6a-multilength", "cable", "6A Multi-Length Cable", "Wholesale $3.00–4.50 · MOQ 20 — samples available",
    "USB-C · TPE jacket · 6A fast charge · 0.25–3m lengths", None)
add("spring-cable", "cable", "Spring 6A Digital Cable", "Wholesale $5.50 · MOQ 20 — samples available",
    "USB-C · 1.8m stretchable coil · braided+TPE · pure copper · ships by Oct 14 · 2 colours", "p16-spring.jpg")
add("3in1", "cable", "3-in-1 Multi-Interface Cable", "Wholesale $2.50 · MOQ 20 — samples available",
    "USB-C → Lightning + USB-C + Micro · braided nylon · legacy coverage · 0.6–1.5m", "p13-3in1.jpg")
add("a2c-braided", "cable", "Braided A→C Cable", "Wholesale $3.00–5.00 · MOQ 20 — samples available",
    "USB-A → USB-C · knurled metal housing · cable tie · 4 colours · 1–3m", "p12-a2c-braided.jpg")

add("otg-adapter", "adapter", "Smart Visual PD Adapter", "Wholesale $3.50 · MOQ 20 — samples available",
    "USB-C passthrough + live wattage display · 100W PD · 480Mbps · car/travel · ships by Oct 14", "p14-otg-adapter.jpg")
add("arc-lighter", "novelty", "USB-C Arc Lighter (XG01)", "Wholesale $6.50 · MOQ 20 — samples available",
    "Windproof plasma arc · aluminium alloy · 8g · long-press safety · ships by Oct 17", "p17-arc-lighter.jpg")

DETAIL_DIRS = {  # staged per-product gallery dirs (images resolved at seed time)
    "ins-style": "ins-style", "candy-double-mag": "candy-double-mag",
    "ultra-thin-contrast": "ultra-thin-contrast", "slim-heat": "slim-heat", "charming-eye": "charming-eye",
    "shockproof-matte-luxury": "shockproof-matte-luxury",
    "xframe-aluminum": "xframe-aluminum",
    "2in1-wireless": "2in1-wireless", "240w-display": "240w-display", "240w-elbow": "240w-elbow",
    "240w-straight": "240w-straight", "100w-realcore": "100w-realcore", "spring-cable": "spring-cable",
    "3in1": "3in1", "a2c-braided": "a2c-braided", "otg-adapter": "otg-adapter", "arc-lighter": "arc-lighter",
}

def gallery_fallback(slug):
    """Static fallback order = staged img-01..n under mikoshi-img/detail/<dir>."""
    dir_name = DETAIL_DIRS.get(slug) or slug  # slug w/o gallery falls back to its own name
    d = HERE / "mikoshi-img" / "detail" / dir_name
    if not d.exists():
        return []
    return [f"{DETAIL}{dir_name}/{f.name}" for f in sorted(d.glob("img-*.jpg"))]

# ---------- products.js ----------
def emit_products_js():
    prods = {}
    imgs = {}
    for p in P:
        prods[p["slug"]] = {k: p[k] for k in ("name", "cat", "price", "notes")}
        imgs[p["slug"]] = gallery_fallback(p["slug"])
    out = [
        "/* Mikoshi Gear — shared product catalog data (generated by build_showcase.py).",
        "   Drive: product.html galleries + card live-thumbnails via catalog_media table.",
        "   Fallback: image list here (initial/static order) when Supabase is unreachable. */",
        "window.MIKOSHI_PRODUCTS = " + json.dumps(prods, indent=1) + ";",
        "window.MIKOSHI_IMAGES = " + json.dumps(imgs, indent=1) + ";",
        "",
    ]
    (HERE / "products.js").write_text("\n".join(out))

# ---------- catalog pages ----------
NAV = """<header>
  <div class="wrap nav">
    <a class="wordmark" href="index.html"><svg width="26" height="26" viewBox="0 0 44 44" fill="none" style="vertical-align:-6px;margin-right:8px"><path d="M4 8 L40 22 L4 36 Z" fill="none" stroke="#35e0ff" stroke-width="2.5"/><path d="M12 15 L28 22 L12 29 Z" fill="#35e0ff"/><circle cx="22" cy="22" r="3" fill="#0b0d10"/></svg>MIKOSHI<b>▸</b>GEAR</a>
    <nav class="nav-links">
      {links}
      <a class="nav-cta" href="index.html#wholesale">Contact</a>
    </nav>
  </div>
</header>"""

FOOT = """<footer>
  <div class="wrap footer-grid">
    <div><p class="mono">MIKOSHI<b>▸</b>GEAR — mikoshigear.ca</p></div>
    <div class="legal">13718387 Canada Inc.<br>Toronto, Ontario · © 2026</div>
  </div>
</footer>"""

LIVE_SWAP = """<script src="products.js"></script>
<script src="catalog-media.js"></script>
<script>
  /* live card thumbnails: catalog_media order wins, static fallback otherwise */
  window.addEventListener("DOMContentLoaded", function () {
    var slugs = Array.prototype.map.call(document.querySelectorAll("[data-product]"), function (f) { return f.getAttribute("data-product"); });
    if (!slugs.length) return;
    MIKOSHI_MEDIA.load(slugs).then(function (rows) {
      rows.forEach(function (m) {
        if (!m.urls.length) return;
        var fig = document.querySelector('[data-product="' + m.pid + '"]');
        var img = fig && fig.querySelector("img");
        if (img) img.src = m.urls[Math.min(m.thumb, m.urls.length - 1)];
      });
    });
  });
</script>"""

def page(title, hero_note, items, active):
    links = "".join(
        f'<a class="{"active" if k == active else ""}" href="{f"{k}.html" if k in ("cases","cables","adapters") else "index.html#why"}">{n}</a>'
        for k, n in [("cases","Cases"),("cables","Cables"),("adapters","Adapters"),("why","Why Mikoshi"),("wholesale","Wholesale")]
    )
    figures = []
    for p in items:
        media = f'<a href="product.html?id={p["slug"]}"><img src="{IMG}{p["img"]}" alt="{p["name"]}" loading="lazy"></a>' if p["img"] else PH
        figures.append(
            f'      <figure class="g-item" data-product="{p["slug"]}">\n        {media}\n'
            f'        <figcaption><b>{p["name"]}</b><span>{p["notes"]}</span>'
            f'<span class="g-price">{p["price"]}</span></figcaption>\n      </figure>'
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mikoshi Gear — {title} — Toronto</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}
</head>
<body>
{NAV.format(links=links)}
<section class="section">
  <div class="wrap">
    <div class="section-head">
      <h2>{title}</h2>
      <p class="note">{hero_note}</p>
    </div>
    <div class="gallery-grid">
{chr(10).join(figures)}
    </div>
  </div>
</section>
{FOOT}
{LIVE_SWAP}
</body>
</html>"""

CSS = """<style>
  :root{--bg:#0b0d10;--surface:#12151a;--surface2:#171b21;--ink:#e9e7e2;--muted:#8b9099;--line:#232830;--accent:#35e0ff;--accent2:#ff3d81;--mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;--sans:"Space Grotesk",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased;}
  ::selection{background:var(--accent);color:#0b0d10;}
  a{color:inherit;}
  .mono{font-family:var(--mono);}
  .wrap{max-width:1160px;margin:0 auto;padding:0 32px;}
  .overline{font-family:var(--mono);font-size:12px;letter-spacing:0.22em;text-transform:uppercase;color:var(--accent);}
  header{position:sticky;top:0;z-index:50;background:rgba(11,13,16,0.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);}
  .nav{display:flex;align-items:center;justify-content:space-between;height:64px;}
  .wordmark{font-family:var(--mono);font-weight:500;font-size:15px;letter-spacing:0.08em;text-decoration:none;}
  .wordmark b{color:var(--accent);font-weight:500;}
  .nav-links{display:flex;gap:32px;align-items:center;}
  .nav-links a{font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .15s;}
  .nav-links a:hover{color:var(--ink);}
  .nav-links a.active{color:var(--accent);}
  .nav-cta{border:1px solid var(--accent);color:var(--accent);padding:8px 16px;border-radius:4px;font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;text-decoration:none;transition:background .15s;}
  .nav-cta:hover{background:var(--accent);color:#0b0d10;}
  @media(max-width:720px){.nav-links a{display:none;}}
  .section{padding:70px 0 90px;border-top:1px solid var(--line);}
  .section-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:40px;gap:20px;flex-wrap:wrap;}
  .section-head h2{font-size:clamp(28px,4vw,44px);font-weight:700;letter-spacing:-0.01em;}
  .section-head .note{font-family:var(--mono);font-size:12px;color:var(--muted);}
  .gallery-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
  @media(max-width:900px){.gallery-grid{grid-template-columns:repeat(2,1fr);}}
  @media(max-width:560px){.gallery-grid{grid-template-columns:1fr;}}
  .g-item{border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--surface);}
  .g-item img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;filter:saturate(1.08) contrast(1.04) brightness(0.96);transition:filter .2s,transform .2s;}
  .g-item:hover img{filter:saturate(1.12) contrast(1.06) brightness(1);transform:scale(1.02);}
  .g-item .ph{width:100%;aspect-ratio:1/1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--surface2);border-bottom:1px solid var(--line);}
  .g-item .ph b{font-family:var(--mono);font-size:13px;letter-spacing:0.18em;color:var(--accent);}
  .g-item .ph span{font-family:var(--mono);font-size:11px;color:var(--muted);}
  .g-item figcaption{padding:14px 16px 16px;border-top:1px solid var(--line);}
  .g-item figcaption b{display:block;font-size:15px;font-weight:500;margin-bottom:4px;}
  .g-item figcaption span{display:block;font-size:12px;color:var(--muted);line-height:1.5;}
  .g-item figcaption .g-price{display:block;margin-top:8px;padding-top:8px;border-top:1px dashed var(--line);font-family:var(--mono);font-size:11px;color:var(--accent);}
  .footer-grid{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;}
  footer{border-top:1px solid var(--line);padding:40px 0 56px;}
  .footer-grid .mono{font-size:12px;color:var(--muted);letter-spacing:0.06em;}
  .footer-grid .legal{font-family:var(--mono);font-size:11px;color:#4d545e;text-align:right;}
</style>"""

cases = [p for p in P if p["cat"] == "case"]
cables = [p for p in P if p["cat"] == "cable"]
adapters = [p for p in P if p["cat"] in ("adapter", "novelty")]

(HERE / "cases.html").write_text(page("Cases", "7 case families — every finish priced wholesale", cases, "cases"))
(HERE / "cables.html").write_text(page("Cables", "9 cable lines — full ladder, samples available", cables, "cables"))
(HERE / "adapters.html").write_text(page("Adapters + More", "PD adapter + USB-C lighter — counter pieces", adapters, "adapters"))
emit_products_js()

print(f"cases: {len(cases)} | cables: {len(cables)} | adapters: {len(adapters)} | total: {len(P)}")
print("products.js:", len((HERE / 'products.js').read_text()), "bytes")
