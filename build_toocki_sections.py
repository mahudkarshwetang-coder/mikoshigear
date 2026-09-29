#!/usr/bin/env python3
"""Mikoshi Gear - full catalog with sub-family sections + sticky jump nav (Option A).
Generates all 6 category pages from SITE_GROUPS2.json + curated_products.json.
Run from repo root: python3 build_toocki_sections.py
"""
import json, re, html
from pathlib import Path

HERE = Path(__file__).parent
IMG = "mikoshi-img/toocki/"
GROUPS = json.load(open(HERE / "SITE_GROUPS2.json", encoding="utf-8"))
CURATED = json.load(open(HERE / "curated_products.json", encoding="utf-8"))
CURATED_IMG = {
 "2in1-wireless":"mikoshi-img/detail/2in1-wireless/img-01.jpg","240w-display":"mikoshi-img/detail/240w-display/img-01.jpg",
 "240w-elbow":"mikoshi-img/detail/240w-elbow/img-01.jpg","240w-straight":"mikoshi-img/detail/240w-straight/img-01.jpg",
 "100w-realcore":"mikoshi-img/detail/100w-realcore/img-01.jpg","spring-cable":"mikoshi-img/detail/spring-cable/img-01.jpg",
 "3in1":"mikoshi-img/detail/3in1/img-01.jpg","a2c-braided":"mikoshi-img/detail/a2c-braided/img-01.jpg",
 "6a-multilength":None,
 "ins-style":"mikoshi-img/detail/ins-style/img-01.jpg","candy-double-mag":"mikoshi-img/detail/candy-double-mag/img-06.jpg",
 "ultra-thin-contrast":"mikoshi-img/detail/ultra-thin-contrast/img-02.jpg","slim-heat":"mikoshi-img/detail/slim-heat/img-02.jpg",
 "charming-eye":"mikoshi-img/detail/charming-eye/img-06.jpg","shockproof-matte-luxury":"mikoshi-img/detail/shockproof-matte-luxury/img-01.jpg",
 "xframe-aluminum":"mikoshi-img/detail/xframe-aluminum/img-01.jpg","ringstand-magnetic":"mikoshi-img/detail/ringstand-magnetic/img-01.jpg",
 "alloy-bumper-luxe":"mikoshi-img/detail/alloy-bumper-luxe/img-01.jpg",
 "otg-adapter":"mikoshi-img/detail/otg-adapter/img-01.jpg","arc-lighter":"mikoshi-img/detail/arc-lighter/img-01.jpg",
}

def esc(s): return html.escape(str(s or ""), quote=True)

def trim_note(s, limit=132):
    """Cut at a clause/word boundary - never mid-word."""
    s = re.sub(r"\s+", " ", str(s or "")).strip(" \u00b7,;:")
    if len(s) <= limit: return s
    parts = [p.strip() for p in s.split("\u00b7")]
    acc = ""
    for p in parts:
        cand = (acc + " \u00b7 " + p).strip(" \u00b7") if acc else p
        if len(cand) > limit: break
        acc = cand
    if len(acc) >= 30: return acc
    return s[:limit].rsplit(" ", 1)[0].rstrip(" \u00b7,;:-")

def blob(p): return (p["name"] + " " + p.get("feat_clean", "")).lower()

def watt(p):
    out = []
    for src in (p["name"], p.get("feat_clean", "")):
        for m in re.finditer(r"(\d{2,3})\s*W(?![a-z])", src, re.I):
            out.append(int(m.group(1)))
    return max(out) if out else None

def amps(p):
    m = re.search(r"(\d+(?:\.\d+)?)\s*A(?![a-z])", p["name"] + " " + p.get("feat_clean", ""))
    return m.group(1) if m else None

def has(p, *pats):
    b = blob(p)
    return any(re.search(x, b) for x in pats)

# ───────── section plans (order matters; each takes what's left) ─────────
PLANS = {
 "cables": [
   ("240W \u2014 flagship", "E-Marked 240W with display readouts and 8K data lines.", lambda p: watt(p) == 240),
   ("120W / 100W \u2014 fast charge", "The workhorse tier \u2014 laptops, tablets, fast-charge phones.", lambda p: watt(p) in (100, 120)),
   ("60W \u2014 charge and sync", "Fast charge for phones and small laptops.", lambda p: watt(p) == 60),
   ("3A\u20136A everyday charge", "Current-rated lines for phone and accessory charging.", lambda p: amps(p) and not watt(p)),
   ("Lightning \u2014 iPhone charging", "A-to-Lightning and C-to-Lightning, every length.", lambda p: has(p, r"lightning")),
   ("Spring, coil and retractable", "Stretch and tidy-away formats for travel and desks.", lambda p: has(p, r"spring|coil|retractable")),
   ("Magnetic and multi-tip", "MagSnap formats, 2-in-1 and 3-in-1 splitters.", lambda p: has(p, r"magnetic|multi-tip|3-in-1|2-in-1")),
   ("Micro-USB", "Legacy devices and budget lines.", lambda p: has(p, r"micro-usb")),
   ("Everything else", "Power banks, audio and accessories \u2014 ask for a quote on any line.", lambda p: True),
 ],
 "chargers": [
   ("140W \u2014 desktop and travel", "Multi-port desktop bricks for desks and counters.", lambda p: watt(p) and watt(p) >= 140),
   ("100W \u2014 high power wall", "Laptop-class wall charging.", lambda p: watt(p) == 100),
   ("67W / 65W \u2014 GaN wall", "The GaN sweet spot for phones and tablets.", lambda p: watt(p) in (65, 67)),
   ("45W and under \u2014 everyday wall", "Single and multi-port chargers for daily use.", lambda p: watt(p) and watt(p) <= 45),
   ("Car chargers", "12-24V lines for the vehicle.", lambda p: has(p, r"car charger|\bcar\b")),
   ("Wireless charging", "Pads, stands and magnetic mounts.", lambda p: has(p, r"wireless")),
   ("Bluetooth and audio", "Receivers, transmitters and adapters.", lambda p: has(p, r"bluetooth")),
   ("Everything else", "The rest of the power range \u2014 ask for a quote on any line.", lambda p: True),
 ],
 "cases": [
   ("iPhone cases", "Fitted and checked before they go on the sheet.", lambda p: has(p, r"iphone")),
   ("Samsung cases", "A-series, S-series and Z Flip.", lambda p: has(p, r"samsung")),
   ("Screen protectors", "Tempered glass, 2-packs.", lambda p: has(p, r"tempered glass|screen protector")),
   ("Everything else", "The rest of the range.", lambda p: True),
 ],
 "mounts": [
   ("Desk and tablet stands", "Counter and desk display.", lambda p: has(p, r"stand|tablet")),
   ("Car mounts and holders", "Vent and dash mounting.", lambda p: has(p, r"car|holder|mount")),
   ("Everything else", "The rest of the range.", lambda p: True),
 ],
 "power": [
   ("Power banks", "Portable battery with built-in cable options.", lambda p: has(p, r"power bank")),
   ("Audio", "Wired earphones and audio.", lambda p: has(p, r"earphone|audio|hifi")),
   ("Lanyard adapters", "240W 8K lanyard-format adapters.", lambda p: has(p, r"lanyard")),
   ("Lighters and accessories", "Electronic ignition and misc.", lambda p: True),
 ],
 "adapters": [
   ("Travel and socket adapters", "Universal sockets, plug conversion.", lambda p: has(p, r"universal|adapter.*(eu|us|uk|de)|socket")),
   ("AV, RCA and audio adapters", "3.5mm, RCA, AUX lines.", lambda p: has(p, r"3\.5mm|rca|aux")),
   ("HDMI", "8K and 4K video lines.", lambda p: has(p, r"hdmi")),
   ("OTG and converters", "Type-C and Lightning converters.", lambda p: has(p, r"otg|type-c|micro")),
   ("Network cards", "Wi-Fi and Ethernet adapters.", lambda p: has(p, r"network|wi-fi|wifi|ethernet|rj45")),
   ("Everything else", "The rest of the range \u2014 ask for a quote on any line.", lambda p: True),
 ],
}

def build_sections(key, items):
    used, secs = set(), []
    for title, desc, pred in PLANS[key]:
        got = [p for p in items if id(p) not in used and pred(p)]
        for p in got: used.add(id(p))
        if got: secs.append({"t": title, "d": desc, "i": got})
    return secs

CSS = """<style>
  :root{--bg:#0b0d10;--surface:#12151a;--surface2:#171b21;--ink:#e9e7e2;--muted:#8b9099;--line:#232830;--accent:#35e0ff;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--sans:"Space Grotesk",-apple-system,"Segoe UI",sans-serif;}
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;}
  ::selection{background:var(--accent);color:#0b0d10;}
  a{color:inherit;}
  .wrap{max-width:1160px;margin:0 auto;padding:0 32px;}
  header{position:sticky;top:0;z-index:50;background:rgba(11,13,16,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);}
  .nav{display:flex;align-items:center;justify-content:space-between;height:64px;}
  .wordmark{font-family:var(--mono);font-size:15px;letter-spacing:.08em;text-decoration:none;color:var(--ink);}
  .wordmark b{color:var(--accent);font-weight:500;}
  .nav-links{display:flex;gap:24px;align-items:center;}
  .nav-links a{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .15s;}
  .nav-links a:hover{color:var(--ink);}
  .nav-links a.on{color:var(--accent);}
  .nav-cta{border:1px solid var(--accent);color:var(--accent);padding:8px 16px;border-radius:4px;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;}
  .nav-cta:hover{background:var(--accent);color:#0b0d10;}
  @media(max-width:900px){.nav-links a:not(.nav-cta){display:none;}}
  .jump{position:sticky;top:64px;z-index:40;background:rgba(11,13,16,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);}
  .jump-in{display:flex;gap:8px;overflow-x:auto;padding:11px 0;scrollbar-width:none;}
  .jump-in::-webkit-scrollbar{display:none;}
  .jump a{flex:0 0 auto;font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:7px 13px;text-decoration:none;white-space:nowrap;transition:.15s;}
  .jump a:hover{color:var(--ink);border-color:var(--ink);}
  .jump a b{color:var(--accent);font-weight:500;margin-left:6px;}
  .hero{padding:50px 0 24px;}
  .hero h1{font-size:clamp(30px,4.4vw,48px);font-weight:700;letter-spacing:-.01em;margin-bottom:14px;}
  .hero p{color:var(--muted);max-width:680px;font-size:16px;}
  .sec{padding:34px 0 40px;border-top:1px solid var(--line);scroll-margin-top:130px;}
  .sec-head{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:8px;}
  .sec-head h2{font-size:clamp(20px,2.5vw,28px);font-weight:700;letter-spacing:-.01em;}
  .sec-head .n{font-family:var(--mono);font-size:12px;color:var(--accent);border:1px solid var(--line);border-radius:999px;padding:4px 11px;}
  .sec-desc{color:var(--muted);font-size:14px;margin-bottom:24px;max-width:620px;}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
  @media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr);}}
  @media(max-width:560px){.grid{grid-template-columns:1fr;}}
  .g-item{border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--surface);display:flex;flex-direction:column;}
  .g-item img{width:100%;aspect-ratio:1/1;object-fit:contain;background:#fff;display:block;transition:transform .2s;}
  .g-item:hover img{transform:scale(1.03);}
  .g-item .ph{width:100%;aspect-ratio:1/1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--surface2);border-bottom:1px solid var(--line);}
  .g-item .ph b{font-family:var(--mono);font-size:13px;letter-spacing:.18em;color:var(--accent);}
  .g-item .ph span{font-family:var(--mono);font-size:11px;color:var(--muted);}
  .g-item figcaption{padding:12px 14px 14px;border-top:1px solid var(--line);flex:1;display:flex;flex-direction:column;}
  .g-item figcaption b{display:block;font-size:13.5px;font-weight:500;line-height:1.35;margin-bottom:4px;}
  .g-item figcaption .sku{display:block;font-family:var(--mono);font-size:10px;color:#5a6270;letter-spacing:.06em;margin-bottom:6px;}
  .g-item figcaption .notes{display:block;font-size:12px;color:var(--muted);line-height:1.45;}
  .g-item figcaption .g-price{display:block;margin-top:auto;padding-top:8px;border-top:1px dashed var(--line);font-family:var(--mono);font-size:11px;color:var(--accent);}
  .badge{display:inline-block;font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;padding:2px 6px;border-radius:3px;margin-bottom:6px;}
  .badge.cur{background:#0e2a33;color:var(--accent);border:1px solid #1d4d5c;}
  .badge.neutral{background:#1a2f24;color:#5ddc9a;border:1px solid #2b5c44;}
  .badge.desc{background:#2a2419;color:#d9b45a;border:1px solid #4d4127;}
  .g-item.cur{border-color:#1d4d5c;}
  .count-note{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:22px;padding-top:16px;border-top:1px solid var(--line);}
  footer{border-top:1px solid var(--line);padding:40px 0 56px;}
  .fg{display:flex;justify-content:space-between;flex-wrap:wrap;gap:16px;}
  footer .mono{font-family:var(--mono);font-size:12px;color:var(--muted);letter-spacing:.06em;}
  footer .legal{font-family:var(--mono);font-size:11px;color:#4d545e;text-align:right;}
  footer b{color:var(--accent);font-weight:500;}
</style>"""

NAVITEMS = [("cables","Cables"),("chargers","Chargers"),("cases","Cases"),
            ("mounts","Mounts"),("power","Power"),("adapters","Adapters")]

def nav(active):
    links = "".join(f'<a class="{"on" if k==active else ""}" href="{k}.html">{n}</a>' for k,n in NAVITEMS)
    return f"""<header>
  <div class="wrap nav">
    <a class="wordmark" href="index.html">MIKOSHI<b>\u25b8</b>GEAR</a>
    <nav class="nav-links">{links}<a class="nav-cta" href="index.html#wholesale">Contact</a></nav>
  </div>
</header>"""

FOOT = """<footer><div class="wrap fg">
  <p class="mono">MIKOSHI<b>\u25b8</b>GEAR \u2014 mikoshigear.ca</p>
  <p class="legal">13718387 Canada Inc. o/a Mikoshi Gear<br>HST 752199703RT0001 \u00b7 Toronto, Ontario \u00b7 \u00a9 2026</p>
</div></footer>"""

def card(p):
    name, sku = esc(p["name"]), esc(p["sku"])
    notes = esc(trim_note(p.get("feat_clean") or p.get("feat") or ""))
    media = (f'<img src="{IMG}{esc(p["img"])}" alt="{name}" loading="lazy">' if p.get("img")
             else "<div class='ph'><b>ARRIVING</b><span>photo pending</span></div>")
    badges = '<span class="badge neutral">unbranded</span>' if p.get("neutral") else ""
    return (f'      <figure class="g-item">\n        {media}\n        <figcaption>{badges}<b>{name}</b>'
            f'<span class="sku">{sku}</span><span class="notes">{notes}</span>'
            f'<span class="g-price">{esc(p["price_line"])}</span></figcaption>\n      </figure>')

def curated_card(p):
    img = CURATED_IMG.get(p["slug"])
    inner = (f'<img src="{img}" alt="{esc(p["name"])}" loading="lazy">' if img
             else "<div class='ph'><b>ARRIVING</b><span>with shipment</span></div>")
    media = f'<a href="product.html?id={p["slug"]}">{inner}</a>'
    badge = ('<span class="badge cur">in stock</span>' if img
             else '<span class="badge desc">arriving</span>')
    return (f'      <figure class="g-item cur" data-product="{p["slug"]}">\n        {media}\n'
            f'        <figcaption>{badge}<b>{esc(p["name"])}</b>'
            f'<span class="sku">view details \u2192</span>'
            f'<span class="notes">{esc(trim_note(p["notes"]))}</span>'
            f'<span class="g-price">{esc(p["price"])}</span></figcaption>\n      </figure>')

PAGES = {
 "cables":   ("Cables", "Every cable line Toocki makes, grouped by power tier so you can jump straight to your bracket instead of scrolling one long wall."),
 "chargers": ("Chargers", "Wall, car and wireless charging \u2014 grouped by power so you can find the bracket you stock."),
 "cases":    ("Cases", "iPhone and Samsung cases, including the fully unbranded line \u2014 no logo anywhere on the product or the packaging."),
 "mounts":   ("Mounts & Stands", "Stands, holders and car mounts \u2014 the small-ticket add-ons that sell with every phone."),
 "power":    ("Power & Audio", "Power banks, audio and the 240W lanyard adapter line."),
 "adapters": ("Adapters", "Travel adapters, AV and audio adapters, HDMI, OTG converters and network cards."),
}

for key, (title, lede) in PAGES.items():
    items = GROUPS.get(key, [])
    secs = build_sections(key, items)
    cur = [p for p in CURATED.values() if p.get("page") == key]
    tot = sum(len(s["i"]) for s in secs)

    jump = ""
    if cur:
        jump += f'<a href="#s-cur">In stock<b>{len(cur)}</b></a>'
    jump += "".join(f'<a href="#s{i}">{esc(s["t"])}<b>{len(s["i"])}</b></a>' for i, s in enumerate(secs))

    body = []
    if cur:
        body.append('<section class="sec" id="s-cur" style="border-top:0">\n'
            f'  <div class="sec-head"><h2>In stock in Toronto</h2><span class="n">{len(cur)} lines</span></div>\n'
            '  <p class="sec-desc">On the shelf now \u2014 fitted, checked, and shipping same week across the GTA.</p>\n'
            '  <div class="grid">\n' + "\n".join(curated_card(p) for p in cur) + '\n  </div>\n</section>')
    for i, s in enumerate(secs):
        body.append(f'<section class="sec" id="s{i}"{" style=\"border-top:0\"" if not cur and i==0 else ""}>\n'
            f'  <div class="sec-head"><h2>{esc(s["t"])}</h2><span class="n">{len(s["i"])} lines</span></div>\n'
            f'  <p class="sec-desc">{esc(s["d"])}</p>\n'
            '  <div class="grid">\n' + "\n".join(card(p) for p in s["i"]) + '\n  </div>\n</section>')

    withimg = sum(1 for p in items if p.get("img")) + len(cur)
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mikoshi Gear \u2014 {title} \u2014 Toronto</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}
</head>
<body>
{nav(key)}
<div class="jump"><div class="wrap jump-in">{jump}</div></div>
<div class="wrap hero">
  <h1>{title}</h1>
  <p>{lede} {tot + len(cur)} lines across {len(secs) + (1 if cur else 0)} families.</p>
</div>
{chr(10).join(body)}
<div class="wrap"><p class="count-note">{tot + len(cur)} lines on this page \u00b7 {withimg} shown with photography \u00b7 USD pricing converted at delivery; landed cost varies with freight \u2014 ask for a quote on any line.</p></div>
{FOOT}
</body>
</html>"""
    (HERE / f"{key}.html").write_text(doc, encoding="utf-8")
    print(f"{key:9s} {tot+len(cur):3d} lines | {len(secs)+(1 if cur else 0)} sections | " +
          " ".join(f"{len(s['i'])}" for s in secs) + f" (+{len(cur)} curated)")

print("\ndone - 6 pages written")
