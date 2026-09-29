#!/usr/bin/env python3
"""Mikoshi Gear — Toocki full-catalog build (432 SKUs).
Generates: cables.html, chargers.html, cases.html, mounts.html, power.html, adapters.html
from SITE_GROUPS.json. Images staged at mikoshi-img/toocki/<sku>.jpg
Run from repo root: python3 build_toocki.py
"""
import json, re, html
from pathlib import Path

HERE = Path(__file__).parent
IMG = "mikoshi-img/toocki/"
GROUPS = json.load(open(HERE / "SITE_GROUPS.json", encoding="utf-8"))

def esc(s): return html.escape(str(s or ""), quote=True)
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:60]

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
  .nav-links{display:flex;gap:26px;align-items:center;}
  .nav-links a{font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .15s;}
  .nav-links a:hover{color:var(--ink);}
  .nav-links a.active{color:var(--accent);}
  .nav-cta{border:1px solid var(--accent);color:var(--accent);padding:8px 16px;border-radius:4px;font-family:var(--mono);font-size:12px;letter-spacing:0.12em;text-transform:uppercase;text-decoration:none;transition:background .15s;}
  .nav-cta:hover{background:var(--accent);color:#0b0d10;}
  @media(max-width:820px){.nav-links a{display:none;}}
  .section{padding:64px 0 90px;border-top:1px solid var(--line);}
  .section-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;gap:20px;flex-wrap:wrap;}
  .section-head h2{font-size:clamp(28px,4vw,44px);font-weight:700;letter-spacing:-0.01em;}
  .section-head .note{font-family:var(--mono);font-size:12px;color:var(--muted);}
  .lede{font-size:16px;color:var(--muted);max-width:640px;margin-bottom:36px;}
  .filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:28px;}
  .filters button{font-family:var(--mono);font-size:11px;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);background:transparent;border:1px solid var(--line);border-radius:4px;padding:8px 14px;cursor:pointer;transition:all .15s;}
  .filters button:hover{color:var(--ink);border-color:var(--ink);}
  .filters button.on{background:var(--accent);color:#0b0d10;border-color:var(--accent);}
  .gallery-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
  @media(max-width:900px){.gallery-grid{grid-template-columns:repeat(2,1fr);}}
  @media(max-width:560px){.gallery-grid{grid-template-columns:1fr;}}
  .g-item{border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--surface);display:flex;flex-direction:column;}
  .g-item img{width:100%;aspect-ratio:1/1;object-fit:contain;display:block;background:#fff;transition:transform .2s;}
  .g-item:hover img{transform:scale(1.03);}
  .g-item .ph{width:100%;aspect-ratio:1/1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--surface2);border-bottom:1px solid var(--line);}
  .g-item .ph b{font-family:var(--mono);font-size:13px;letter-spacing:0.18em;color:var(--accent);}
  .g-item .ph span{font-family:var(--mono);font-size:11px;color:var(--muted);}
  .g-item figcaption{padding:12px 14px 14px;border-top:1px solid var(--line);flex:1;display:flex;flex-direction:column;}
  .g-item figcaption b{display:block;font-size:14px;font-weight:500;margin-bottom:4px;line-height:1.35;}
  .g-item figcaption .sku{display:block;font-family:var(--mono);font-size:10px;color:#5a6270;letter-spacing:0.06em;margin-bottom:6px;}
  .g-item figcaption span.notes{display:block;font-size:12px;color:var(--muted);line-height:1.45;}
  .g-item figcaption .g-price{display:block;margin-top:auto;padding-top:8px;border-top:1px dashed var(--line);font-family:var(--mono);font-size:11px;color:var(--accent);}
  .badge{display:inline-block;font-family:var(--mono);font-size:9px;letter-spacing:0.08em;text-transform:uppercase;padding:2px 6px;border-radius:3px;margin-bottom:6px;}
  .badge.neutral{background:#1a2f24;color:#5ddc9a;border:1px solid #2b5c44;}
  .badge.desc{background:#2a2419;color:#d9b45a;border:1px solid #4d4127;}
  .count-note{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:22px;padding-top:16px;border-top:1px solid var(--line);}
  .footer-grid{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;}
  footer{border-top:1px solid var(--line);padding:40px 0 56px;}
  .footer-grid .mono{font-size:12px;color:var(--muted);letter-spacing:0.06em;}
  .footer-grid .legal{font-family:var(--mono);font-size:11px;color:#4d545e;text-align:right;}
  .footer-grid b{color:var(--accent);font-weight:500;}
</style>"""

NAVITEMS = [("cables","Cables"),("chargers","Chargers"),("cases","Cases"),
            ("mounts","Mounts"),("power","Power"),("adapters","Adapters")]

def nav(active):
    links = "".join(
        f'<a class="{"active" if k==active else ""}" href="{k}.html">{n}</a>' for k,n in NAVITEMS
    )
    return f"""<header>
  <div class="wrap nav">
    <a class="wordmark" href="index.html"><svg width="26" height="26" viewBox="0 0 44 44" fill="none" style="vertical-align:-6px;margin-right:8px"><path d="M4 8 L40 22 L4 36 Z" fill="none" stroke="#35e0ff" stroke-width="2.5"/><path d="M12 15 L28 22 L12 29 Z" fill="#35e0ff"/><circle cx="22" cy="22" r="3" fill="#0b0d10"/></svg>MIKOSHI<b>\u25b8</b>GEAR</a>
    <nav class="nav-links">
      {links}
      <a class="nav-cta" href="index.html#wholesale">Contact</a>
    </nav>
  </div>
</header>"""

FOOT = """<footer>
  <div class="wrap footer-grid">
    <div><p class="mono">MIKOSHI<b>\u25b8</b>GEAR \u2014 mikoshigear.ca</p></div>
    <div class="legal">13718387 Canada Inc. o/a Mikoshi Gear<br>HST 752199703RT0001 \u00b7 Toronto, Ontario \u00b7 \u00a9 2026</div>
  </div>
</footer>"""

def card(p):
    name = esc(p["name"])
    sku = esc(p["sku"])
    notes = esc(p.get("feat") or "")
    notes = re.sub(r"^\d+\.\s*", "", notes)[:150]
    price = esc(p["price_line"])
    if p.get("img"):
        media = f'<img src="{IMG}{esc(p["img"])}" alt="{name}" loading="lazy">'
    else:
        media = "<div class='ph'><b>ARRIVING</b><span>photo pending</span></div>"
    badges = ""
    if p.get("neutral"): badges += '<span class="badge neutral">unbranded</span>'
    if p.get("named") == "descriptive": badges += '<span class="badge desc">spec-listed</span>'
    return (f'      <figure class="g-item">\n        {media}\n'
            f'        <figcaption>{badges}<b>{name}</b><span class="sku">{sku}</span>'
            f'<span class="notes">{notes}</span><span class="g-price">{price}</span></figcaption>\n      </figure>')

def page(key, title, hero_note, lede):
    items = GROUPS.get(key, [])
    figures = "\n".join(card(p) for p in items)
    withimg = sum(1 for p in items if p.get("img"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mikoshi Gear \u2014 {title} \u2014 Toronto</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}
</head>
<body>
{nav(key)}
<section class="section">
  <div class="wrap">
    <div class="section-head">
      <h2>{title}</h2>
      <p class="note">{hero_note}</p>
    </div>
    <p class="lede">{lede}</p>
    <div class="gallery-grid">
{figures}
    </div>
    <p class="count-note">{len(items)} lines in this category \u00b7 {withimg} shown with photography \u00b7 USD pricing converted at delivery; landed cost varies with freight \u2014 ask for a quote on any line.</p>
  </div>
</section>
{FOOT}
</body>
</html>"""

PAGES = {
 "cables":   ("Cables", "the full power ladder",
   "Every cable line Toocki makes \u2014 sorted from 240W flagship down to 20W workhorse. Power tier, connector, and feature are in each card."),
 "chargers": ("Chargers", "wall, GaN, wireless, car",
   "The power shelf. GaN wall chargers from 20W to 140W, plus wireless and car charging."),
 "cases":    ("Cases", "clean and unbranded",
   "iPhone and Samsung cases \u2014 including the fully unbranded line, no logo anywhere on the product or the packaging."),
 "mounts":   ("Mounts & Stands", "desk and car",
   "Stands, holders and car mounts. The small-ticket add-ons that shops sell with every phone."),
 "power":    ("Power & Audio", "banks, strips, sound",
   "Power banks, charging strips, and the audio line \u2014 headphones and TWS."),
 "adapters": ("Adapters", "OTG, AV, travel",
   "OTG adapters, HDMI/AV cables, and travel socket adapters."),
}

for key,(title,note,lede) in PAGES.items():
    out = page(key, title, note, lede)
    (HERE/f"{key}.html").write_text(out, encoding="utf-8")
    print(f"wrote {key}.html ({len(GROUPS.get(key,[]))} items, {len(out):,} bytes)")

print("done")
