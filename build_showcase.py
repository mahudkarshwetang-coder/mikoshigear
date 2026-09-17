#!/usr/bin/env python3
"""Mikoshi Gear showcase — 2026-09-18 session products, per-product detail pages.
Each product gets product/<slug>.html with a full image gallery from
mikoshi-img/products/<slug>/img-NN.jpg (originals from ~/Desktop product folders).
Grid cards link to the detail pages. Run: python3 build_showcase.py
"""
from pathlib import Path
import re, sys

HERE = Path(__file__).parent
PROD = "mikoshi-img/products/"
PH = "<div class='ph'><b>ARRIVING</b><span>with shipment</span></div>"

# name, cat, price, notes, slug, gallery (None => placeholder card)
P = []
def add(cat, name, price, notes, slug, gallery=True):
    P.append(dict(cat=cat, name=name, price=price, notes=notes, slug=slug, gallery=gallery))

add("case", "Ins Style Aesthetic Case (Korean / Japanese)", "Wholesale $4.50 · MOQ 20 — samples available",
    "iPhone 11–17 · TPU+PC soft-hard hybrid · full coverage · raised camera bezel · anti-dirt · pink shown", "p01-ins-style")
add("case", "Candy Pop-It Suction Case", "Wholesale $3.70 · MOQ 20 — samples available",
    "iPhone 18/17 Air–11 · matte soft-touch · pop-it fidget grid · flat-surface grip · pastel yellow shown", "p02-popit")
add("case", "Candy Double-Layer Magnetic Case", "Wholesale $3.00 · MOQ 20 — samples available",
    "iPhone 11–17 · shockproof TPU+PC · transparent matte · MagSafe · 6 colours: pink·sage·grey·sky·mint·cream", "p03-double-layer-mag")
add("case", "Ultra-Thin Contrast Magnetic Case", "Wholesale $5.00 · MOQ 20 — samples available",
    "iPhone 13–18 (Pro/Pro Max/17 Air) · ultra-thin matte · orange accent ring · MagSafe · 3 colours", "p04-ultra-thin")
add("case", "Slim Solid-Color Heat-Dissipating Case", "Wholesale $4.00 · MOQ 20 — samples available",
    "iPhone 13–17 · ultra-slim matte hard-shell · heat-dissipation ring · scratch-resistant · cream shown", "p05-slim-heat")
add("case", "Skin-Feel 'Charming Eye' Case", "Wholesale $4.10 · MOQ 20 — samples available",
    "iPhone 11–17 + XR/XS/XS Max · matte skin-feel · eye graphic · metallic accent ring · 3 colours", "p06-charming-eye")

add("cable", "Toocki 2-in-1 100W + Wireless Cable", "Wholesale $12.50 · MOQ 20 — samples available",
    "USB-C 100W + 2.5W wireless puck (watch/earbuds) · E-Marker · braided · ships by Oct 14", "p15-2in1-wireless")
add("cable", "Toocki 240W Display Cable (live wattage)", "Wholesale $4.00–8.00 · MOQ 20 — samples available",
    "USB-C · real-time W readout · braided + metal housing · 480Mbps · 1/2m · ships by Oct 14", "p09-240w-display")
add("cable", "Toocki 240W Elbow 90° Cable", "Wholesale $7.00 · MOQ 20 — samples available",
    "USB-C · L-shaped elbow · zinc-alloy shell · braided nylon · 1.5m", "p08-240w-elbow")
add("cable", "Toocki 240W Max Cable", "Wholesale $7.00 · MOQ 20 — samples available",
    "USB-C · zinc-alloy shell · reinforced strain relief · braided · 1.5m", "p07-240w-straight")
add("cable", "Toocki 100W Real-Core Cable", "Wholesale $3.00–5.50 · MOQ 20 — samples available",
    "USB-C · six-strand core · anti-interference · gold-plated · 4 colours", "p10-100w-realcore")
add("cable", "Toocki 6A Multi-Length Cable", "Wholesale $3.00–4.50 · MOQ 20 — samples available",
    "USB-C · TPE jacket · 6A fast charge · 0.25–3m lengths", "p11-6a-multilen", gallery=False)
add("cable", "Toocki Spring 6A Digital Cable", "Wholesale $5.50 · MOQ 20 — samples available",
    "USB-C · 1.8m stretchable coil · braided+TPE · pure copper · ships by Oct 14 · 2 colours", "p16-spring")
add("cable", "Toocki 3-in-1 Multi-Interface Cable", "Wholesale $2.50 · MOQ 20 — samples available",
    "USB-C → Lightning + USB-C + Micro · braided nylon · legacy coverage · 0.6–1.5m", "p13-3in1")
add("cable", "Toocki Braided A→C Cable", "Wholesale $3.00–5.00 · MOQ 20 — samples available",
    "USB-A → USB-C · knurled metal housing · cable tie · 4 colours · 1–3m", "p12-a2c-braided")

add("adapter", "Toocki Smart Visual PD Adapter", "Wholesale $3.50 · MOQ 20 — samples available",
    "USB-C passthrough + live wattage display · 100W PD · 480Mbps · car/travel · ships by Oct 14", "p14-otg")
add("novelty", "Toocki USB-C Arc Lighter (XG01)", "Wholesale $6.50 · MOQ 20 — samples available",
    "Windproof plasma arc · aluminium alloy · 8g · long-press safety · ships by Oct 17", "p17-lighter")

NAV = """<header>
  <div class="wrap nav">
    <a class="wordmark" href="{root}index.html"><svg width="26" height="26" viewBox="0 0 44 44" fill="none" style="vertical-align:-6px;margin-right:8px"><path d="M4 8 L40 22 L4 36 Z" fill="none" stroke="#35e0ff" stroke-width="2.5"/><path d="M12 15 L28 22 L12 29 Z" fill="#35e0ff"/><circle cx="22" cy="22" r="3" fill="#0b0d10"/></svg>MIKOSHI<b>▸</b>GEAR</a>
    <nav class="nav-links">
      <a href="{root}cases.html">Cases</a>
      <a href="{root}cables.html">Cables</a>
      <a href="{root}adapters.html">Adapters</a>
      <a href="{root}index.html#why">Why Mikoshi</a>
      <a class="nav-cta" href="{root}index.html#wholesale">Contact</a>
    </nav>
  </div>
</header>"""

FOOT = """<footer>
  <div class="wrap footer-grid">
    <div><p class="mono">MIKOSHI<b>▸</b>GEAR — mikoshigear.ca</p></div>
    <div class="legal">13718387 Canada Inc.<br>Toronto, Ontario · © 2026</div>
  </div>
</footer>"""

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
  .g-item a{display:block;}
  .g-item img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;filter:saturate(1.08) contrast(1.04) brightness(0.96);transition:filter .2s,transform .2s;}
  .g-item:hover img{filter:saturate(1.12) contrast(1.06) brightness(1);transform:scale(1.02);}
  .g-item .ph{width:100%;aspect-ratio:1/1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--surface2);border-bottom:1px solid var(--line);}
  .g-item .ph b{font-family:var(--mono);font-size:13px;letter-spacing:0.18em;color:var(--accent);}
  .g-item .ph span{font-family:var(--mono);font-size:11px;color:var(--muted);}
  .g-item figcaption{padding:14px 16px 16px;border-top:1px solid var(--line);}
  .g-item figcaption b{display:block;font-size:15px;font-weight:500;margin-bottom:4px;}
  .g-item figcaption span{display:block;font-size:12px;color:var(--muted);line-height:1.5;}
  .g-item figcaption .g-price{display:block;margin-top:8px;padding-top:8px;border-top:1px dashed var(--line);font-family:var(--mono);font-size:11px;color:var(--accent);}
  .g-item figcaption .view{display:block;margin-top:6px;font-family:var(--mono);font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--accent2);}
  .footer-grid{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;}
  footer{border-top:1px solid var(--line);padding:40px 0 56px;}
  .footer-grid .mono{font-size:12px;color:var(--muted);letter-spacing:0.06em;}
  .footer-grid .legal{font-family:var(--mono);font-size:11px;color:#4d545e;text-align:right;}
</style>"""

PROD_CSS = """<style>
  :root{--bg:#0b0d10;--surface:#12151a;--surface2:#171b21;--ink:#e9e7e2;--muted:#8b9099;--line:#232830;--accent:#35e0ff;--accent2:#ff3d81;--mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;--sans:"Space Grotesk",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
  *{margin:0;padding:0;box-sizing:border-box;}body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased;}
  a{color:inherit;}
  .wrap{max-width:1060px;margin:0 auto;padding:0 32px;}
  header{position:sticky;top:0;z-index:50;background:rgba(11,13,16,0.92);border-bottom:1px solid var(--line);}
  .nav{display:flex;align-items:center;justify-content:space-between;height:64px;}
  .wordmark{font-family:var(--mono);font-weight:500;font-size:15px;text-decoration:none;letter-spacing:0.08em;}.wordmark b{color:var(--accent);}
  .nav-links{display:flex;gap:28px;align-items:center;}.nav-links a{font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;}
  .nav-links a:hover{color:var(--ink);}
  .back{display:inline-block;margin:36px 0 0;font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;}
  .back:hover{color:var(--accent);}
  .prod{display:grid;grid-template-columns:1.1fr 1fr;gap:48px;padding:36px 0 80px;align-items:start;}
  @media(max-width:860px){.prod{grid-template-columns:1fr;}}
  .gal{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
  .gal img{width:100%;aspect-ratio:1/1;object-fit:cover;border:1px solid var(--line);border-radius:4px;display:block;}
  .gal .ph{aspect-ratio:1/1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--surface2);border:1px solid var(--line);border-radius:4px;}
  .gal .ph b{font-family:var(--mono);font-size:13px;letter-spacing:0.18em;color:var(--accent);}.gal .ph span{font-family:var(--mono);font-size:11px;color:var(--muted);}
  h1{font-size:clamp(24px,3.4vw,38px);font-weight:700;letter-spacing:-0.01em;margin:18px 0 10px;}
  .tag{display:inline-block;font-family:var(--mono);font-size:11px;letter-spacing:0.16em;text-transform:uppercase;color:var(--accent);border:1px solid var(--line);padding:4px 10px;border-radius:3px;margin-bottom:18px;}
  .desc{color:var(--muted);font-size:15px;margin-bottom:22px;}
  .price-line{font-family:var(--mono);font-size:22px;color:var(--accent);margin:20px 0 8px;}
  .note{font-family:var(--mono);font-size:12px;color:var(--muted);}
  .cta{display:inline-block;margin-top:26px;padding:14px 26px;border-radius:4px;background:var(--accent);color:#0b0d10;font-family:var(--mono);font-size:13px;letter-spacing:0.1em;text-transform:uppercase;text-decoration:none;}
  .cta:hover{background:#7deeff;}
  footer{border-top:1px solid var(--line);padding:36px 0 52px;}
  .frow{display:flex;justify-content:space-between;font-size:11px;color:#4d545e;font-family:var(--mono);}
</style>"""

def page(title, active, items):
    links = "".join(
        f'<a class="{"active" if k == active else ""}" href="{f"{k}.html" if k in ("cases","cables","adapters") else "index.html#why"}">{n}</a>'
        for k, n in [("cases","Cases"),("cables","Cables"),("adapters","Adapters"),("why","Why Mikoshi")]
    )
    cards = []
    view = '<span class="view">view gallery →</span>'
    for it in items:
        src = PROD + it["slug"] + "/img-01.jpg"
        media = (f'<a href="product/{it["slug"]}.html"><img src="{src}" alt="{it["name"]}" loading="lazy"></a>'
                 if Path(src).exists() else
                 f'<a href="product/{it["slug"]}.html">{PH}</a>')
        cards.append(
            f'      <figure class="g-item">\n        {media}\n'
            f'        <figcaption><b>{it["name"]}</b><span>{it["notes"]}</span>'
            f'<span class="g-price">{it["price"]}</span>'
            f'{view if it["gallery"] else ""}</figcaption>\n      </figure>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mikoshi Gear — {title} — Toronto</title><link rel="icon" type="image/svg+xml" href="favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}</head><body>
{NAV.format(root="", links=links)}
<section class="section"><div class="wrap">
  <div class="section-head"><h2>{title}</h2><p class="note">tap any card for full gallery</p></div>
  <div class="gallery-grid">
{chr(10).join(cards)}
  </div>
</div></section>
{FOOT}
</body></html>"""

def prod_page(it):
    gal = Path("mikoshi-img/products") / it["slug"]
    imgs = sorted(gal.glob("img-*.jpg")) if it["gallery"] else []
    cells = "".join(f'<img src="../{PROD}{it["slug"]}/{i.name}" alt="{it["name"]} — view {n}" loading="lazy">'
                    for n, i in enumerate(imgs, 1)) or PH
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{it["name"]} — Mikoshi Gear</title><link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
{PROD_CSS}</head><body>
{NAV.format(root="../")}
<div class="wrap">
  <a class="back" href="../{it["cat"] + "s" if it["cat"] in ("case","cable") else ("adapters.html" if it["cat"] in ("adapter","novelty") else "cases.html")}">← back</a>
  <div class="prod">
    <div class="gal">{cells}</div>
    <div>
      <span class="tag">{it["cat"]}</span>
      <h1>{it["name"]}</h1>
      <p class="desc">{it["notes"]}</p>
      <p class="price-line">{it["price"]}</p>
      <p class="note">samples available · MOQ 20 · wholesale in CAD</p>
      <a class="cta" href="../index.html#wholesale">Request wholesale</a>
    </div>
  </div>
</div>
<footer><div class="wrap frow"><span>MIKOSHI▸GEAR — mikoshigear.ca</span><span>13718387 Canada Inc. · Toronto · © 2026</span></div></footer>
</body></html>"""

out = Path("product"); out.mkdir(exist_ok=True)
for it in P:
    (out / f"{it['slug']}.html").write_text(prod_page(it))
cases = [p for p in P if p["cat"] == "case"]
cables = [p for p in P if p["cat"] == "cable"]
adapters = [p for p in P if p["cat"] in ("adapter", "novelty")]
Path("cases.html").write_text(page("Cases", "cases", cases))
Path("cables.html").write_text(page("Cables", "cables", cables))
Path("adapters.html").write_text(page("Adapters + More", "adapters", adapters))
print(f"cases {len(cases)} · cables {len(cables)} · adapters {len(adapters)} · detail pages {len(P)}")
