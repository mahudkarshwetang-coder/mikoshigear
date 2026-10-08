#!/usr/bin/env python3
"""Mikoshi Gear catalog - TANDEM build (Option A sections + Option B variant folding).
Generates all 6 category pages from SITE_GROUPS2.json + curated_products.json.
Run from repo root: python3 build_toocki_tandem.py
"""
import json, re, html, os
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
IMG = "mikoshi-img/toocki/"
GROUPS = json.load(open(HERE / "SITE_GROUPS2.json", encoding="utf-8"))
CURATED = json.load(open(HERE / "curated_products.json", encoding="utf-8"))

# ── Catalog Studio admin data (optional; absent/empty = pure legacy behaviour) ──
# catalog_admin.json lives in the repo root and is applied AT RUNTIME on the
# live site by catalog-admin.js (no rebuild needed for order/cover/gallery edits):
#   {
#     "v": <epoch ms>,
#     "order":  { "<page>": { "<sectionId>": ["<cid>", ...] } },  # card order per page+section
#     "covers": { "<cid>": "<img path or http url>" },            # card cover override
#     "images": { "<pid>": ["<url>", ...] },                      # detail gallery override
#   }
# cid (figure data-cid) = curated slug | single SKU | "fam:<family_key>".
# The builder only guarantees the hooks (data-cid attrs + script tags + catalog.js);
# the local Catalog Studio (studio/) writes the JSON and publishes it.
def _load_admin():
    p = HERE / "catalog_admin.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception as e:
        print("catalog_admin.json unreadable, ignoring:", e)
        return {}

ADMIN = _load_admin()

def _order_cards(cards, keylist):
    """Reorder card dicts per keylist; unlisted cards keep relative order after listed ones."""
    if not keylist:
        return cards
    idx = {k: i for i, k in enumerate(keylist)}
    listed = [c for c in cards if c["_key"] in idx]
    rest = [c for c in cards if c["_key"] not in idx]
    listed.sort(key=lambda c: idx[c["_key"]])
    return listed + rest

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

def blob(p): return (p["name"] + " " + p.get("feat_clean","")).lower()

def watt(p):
    out = []
    for src in (p["name"], p.get("feat_clean","")):
        for m in re.finditer(r"(\d{2,3})\s*W(?![a-z])", src, re.I):
            out.append(int(m.group(1)))
    return max(out) if out else None

def amps(p):
    m = re.search(r"(\d+(?:\.\d+)?)\s*A(?![a-z])", p["name"] + " " + p.get("feat_clean",""))
    return m.group(1) if m else None

def has(p, *x): return any(re.search(y, blob(p)) for y in x)

# ── variant axes ──
COLOURS = r"\b(Black|White|Grey|Gray|Blue|Green|Pink|Purple|Red|Yellow|Silver|Clear|Gunmetal|Titanium|Gold|Orange|Deep Space Grey|Space Grey)\b"
LENGTHS = r"(\d+(?:\.\d+)?\s*(?:m\b|meters?\b|M\b|Meter\b|Meters\b))"
PLUGS = r"\b(US Standard|EU Standard|UK Standard|Korean Standard|Australian Standard|American Standard|European Standard|British Standard|US Version|EU Version|UK Version|Korean Version|US Spec(?:ification)?|EU Spec(?:ification)?|UK Spec(?:ification)?|Korean Spec(?:ification)?)\b"
PACK = r"(\((?:English|Korean)?\s*(?:Color|Colour)?\s*Box\)|\(English Bagged\)|\(English Packed\)|\(Bagged\)|\(Color Box\)|English Bagged|English Packed|2\s*Pack)"

PLUG_SHORT = {"us":"US plug","eu":"EU plug","uk":"UK plug","kr":"KR plug","au":"AU plug",
              "american":"US plug","european":"EU plug","british":"UK plug","korean":"KR plug","australian":"AU plug"}

def family_key(name):
    s = name
    s = re.sub(r"\s*\u2014\s*[A-Z0-9\-]{4,}\s*$", "", s)          # my disambiguator suffix
    s = re.sub(r"\s*\u2014\s*\d+W\s*\([^)]*\)\s*$", "", s)
    s = re.sub(PACK, " ", s, flags=re.I)
    s = re.sub(PLUGS, " ", s, flags=re.I)
    s = re.sub(r"\(?\b(?:US|EU|UK|KR|AU|DE|Korean|American|European|British|Australian)\s*to\s*Universal\)?", " ", s, flags=re.I)
    s = re.sub(COLOURS, " ", s, flags=re.I)
    s = re.sub(LENGTHS, " ", s, flags=re.I)
    s = re.sub(r"\b(pink|sage|sky|mint|cream|candy|colours?|\d+\s*colours?)\b", " ", s, flags=re.I)
    s = re.sub(r"[,\-\u2013\u2014\u00b7()]+\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" -\u2013\u2014\u00b7,()")
    return s.lower()

PROT = {"c-c":"C-C","c-l":"C-L","a-c":"A-C","a-l":"A-L","usb-c":"USB-C","usb-a":"USB-A",
        "gan":"GaN","tpe":"TPE","tpu":"TPU","abs":"ABS","pc":"PC","pd":"PD","oled":"OLED",
        "led":"LED","aux":"AUX","rca":"RCA","hdmi":"HDMI","otg":"OTG","rj45":"RJ45","qcy":"QCY",
        "w":"W","a":"A","m":"m","hifi":"HiFi","tws":"TWS","wifi":"WiFi",
        "3c2a":"3C2A","3c1a":"3C1A","2c1a":"2C1A","1a2c":"1A2C","2c2a":"2C2A","4c2a":"4C2A",
        "1a3c":"1A3C","1a1c":"1A1C","2c":"2C","1a":"1A","3c":"3C","4c":"4C",
        "iphone":"iPhone","ipad":"iPad","sms":"Samsung","type-c":"Type-C","type-a":"Type-A"}

# phrases that must survive capitalisation as written
FIX_PHRASES = [
    (r"\bauauto-off\b", "auto-off"), (r"\bauto-off\b", "auto-off"),
    (r"\bEustandard\b", "EU standard"), (r"\bEustandard\b", "EU standard"),
    (r"\bUsstandard\b", "US standard"), (r"\bUkstandard\b", "UK standard"),
    (r"\bEustandard\b", "EU standard"),
]

def pretty(s):
    """Turn a family key into a readable product name."""
    s = s.lower()
    # repair upstream glue before anything else (order matters: longest first)
    s = s.replace("auauto-off", "auto-off")
    s = re.sub(r"\bauto\s*-\s*off\b", "auto-off", s)     # normalise BEFORE any 'to-off' rule
    s = re.sub(r"(?<!au)\bto-off\b", "auto-off", s)         # 'to-off' only when not preceded by 'au'

    s = s.replace("eustandard", "eu standard").replace("usstandard", "us standard")
    s = s.replace("ukstandard", "uk standard").replace("koreanstandard", "kr standard")
    s = s.replace("australianstandard", "au standard").replace("americanstandard", "us standard")
    s = s.replace("europeanstandard", "eu standard").replace("britishstandard", "uk standard")
    s = s.replace("ip15", "iphone 15").replace("ip14", "iphone 14").replace("ip13", "iphone 13")
    s = re.sub(r"\bip(\d{2})\b", r"iphone \1", s)
    # unit glue: "10000ah" -> "10000mAh", "35w" stays
    s = re.sub(r"\b(\d{3,5})\s*ah\b", r"\1mAh", s)
    s = re.sub(r"\b(\d{2,5})ah\b", r"\1mAh", s)
    s = re.sub(r"\b1a1c\b", "1A1C", s)
    s = re.sub(r"\b2c1auk\b", "2C1A UK", s)
    s = re.sub(r"\b2c1a\s*uk\b", "2C1A UK", s)
    s = re.sub(r"\beustandard\b", "eu standard", s)
    s = re.sub(r"\btq-(\w+)\b", lambda m: "TQ-"+m.group(1).upper(), s)
    s = re.sub(r"\bpb0(\d)\b", r"PB0\1", s)
    s = re.sub(r"\b(\d+(?:\.\d+)?)w\b", r"\1W", s)
    s = re.sub(r"\b(\d+(?:\.\d+)?)a\b", r"\1A", s)
    words = []
    for w in s.split():
        wl = w.strip("()[],")
        if wl in PROT:
            words.append(PROT[wl])
        elif re.fullmatch(r"\d+mah", wl, re.I):
            words.append(re.match(r"(\d+)", wl).group(1) + "mAh")
        elif re.fullmatch(r"\d+", wl):
            words.append(wl)
        elif re.fullmatch(r"\d+(?:\.\d+)?[wa]m?", wl, re.I):
            words.append(wl[:-1] + wl[-1].upper())
        else:
            words.append(w.capitalize() if w.islower() else w)
    out = " ".join(words)
    out = re.sub(r"(?<!au)\bto-off\b", "auto-off", out, flags=re.I)
    out = out.replace("Auauto-off", "Auto-Off").replace("auauto-off", "auto-off")
    out = re.sub(r"\bAuto-off\b", "Auto-Off", out)
    out = re.sub(r"\b(\d{3,5})\s*[Aa]h\b", r"\1mAh", out)   # stray "Ah" -> mAh
    if not out.lower().startswith(("toocki", "neutral")): out = "Toocki " + out
    return out[:80]

def variant_axes(v):
    """What distinguishes these SKUs? -> (lengths, colours, plugs, prices, skus)"""
    lens, cols, plugs, prices = [], [], [], []
    for p in v:
        nm = p["name"]
        m = re.search(LENGTHS, nm, re.I)
        if m:
            n = re.match(r"(\d+(?:\.\d+)?)", m.group(1))
            t = (n.group(1) + "m") if n else m.group(1).replace(" ","")
            if t not in lens: lens.append(t)
        c = re.search(COLOURS, nm)
        if c and c.group(1) not in cols: cols.append(c.group(1))
        pl = re.search(PLUGS, nm)
        if pl:
            key = pl.group(1).split()[0].lower()
            short = PLUG_SHORT.get(key)
            if short and short not in plugs: plugs.append(short)
        pr = re.search(r"\$([\d.]+)", p["price_line"])
        if pr: prices.append(float(pr.group(1)))
    def sl(x):
        m = re.match(r"(\d+(?:\.\d+)?)", x); return float(m.group(1)) if m else 99
    return sorted(set(lens), key=sl), cols, plugs, prices, v

# ───────── section plans (identical to the shipped Option A build) ─────────
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
   ("Travel and socket adapters", "Universal sockets, plug conversion.", lambda p: has(p, r"universal|socket")),
   ("AV, RCA and audio adapters", "3.5mm, RCA, AUX lines.", lambda p: has(p, r"3\.5mm|rca|aux")),
   ("HDMI", "8K and 4K video lines.", lambda p: has(p, r"hdmi")),
   ("OTG and converters", "Type-C and Lightning converters.", lambda p: has(p, r"otg|type-c|micro")),
   ("Network cards", "Wi-Fi and Ethernet adapters.", lambda p: has(p, r"network|wi-fi|wifi|ethernet|rj45")),
   ("Everything else", "The rest of the range \u2014 ask for a quote on any line.", lambda p: True),
 ],
}

def sections_for(key, items):
    used, secs = set(), []
    for title, desc, pred in PLANS[key]:
        got = [p for p in items if id(p) not in used and pred(p)]
        for p in got: used.add(id(p))
        if got: secs.append({"t": title, "d": desc, "i": got})
    return secs

def fold(items):
    fams = defaultdict(list)
    for p in items:
        fams[family_key(p["name"])].append(p)
    singles = [v[0] for k, v in fams.items() if len(v) == 1]
    folds = [(k, v) for k, v in fams.items() if len(v) > 1]
    folds.sort(key=lambda x: -len(x[1]))
    singles.sort(key=lambda p: p["name"])
    return singles, folds

# ───────── markup ─────────
def _cover(cid, default):
    """Admin cover override (catalog_admin.json covers) or the default media src."""
    c = (ADMIN.get("covers") or {}).get(cid)
    return c or default

def card_single(p):
    name, sku = esc(p["name"]), esc(p["sku"])
    notes = esc(trim_note(p.get("feat_clean") or p.get("feat") or ""))
    img = _cover(sku, (IMG + esc(p["img"])) if p.get("img") else None)
    inner = (f'<img src="{img}" alt="{name}" loading="lazy">' if img
             else "<div class='ph'><b>ARRIVING</b><span>photo pending</span></div>")
    media = f'<a href="product.html?id={esc(sku)}">{inner}</a>'
    badges = '<span class="badge neutral">unbranded</span>' if p.get("neutral") else ""
    return (f'      <figure class="g-item" data-cid="{esc(sku)}">\n        {media}\n        <figcaption>{badges}<b>{name}</b>'
            f'<span class="sku">{sku}</span><span class="notes">{notes}</span>'
            f'<span class="g-price">{esc(p["price_line"])}</span></figcaption>\n      </figure>')

def card_family(key, v):
    lens, cols, plugs, prices, skus = variant_axes(v)
    rep = next((p for p in skus if p.get("img")), skus[0])
    name = esc(pretty(key))
    notes = esc(trim_note(rep.get("feat_clean") or ""))
    parts = []
    if plugs: parts.append(" / ".join(plugs))
    if len(lens) > 1: parts.append(" \u00b7 ".join(lens))
    if len(cols) > 1: parts.append(", ".join(cols[:6]))
    vline = "  |  ".join(parts)
    if prices:
        lo, hi = min(prices), max(prices)
        pr = (f"Wholesale ${lo:.2f} \u00b7 MOQ 20 \u2014 samples available" if abs(hi-lo) < 0.01
              else f"Wholesale ${lo:.2f}\u2013{hi:.2f} \u00b7 MOQ 20 \u2014 samples available")
    else:
        pr = "Ask for a quote"
    img = _cover("fam:" + str(key), (IMG + esc(rep["img"])) if rep.get("img") else None)
    media = (f'<img src="{img}" alt="{name}" loading="lazy">' if img
             else "<div class='ph'><b>ARRIVING</b><span>photo pending</span></div>")
    def _price(p):
        mm = re.search(r"\$[\d.]+", p["price_line"])
        return mm.group(0) if mm else "\u2014"
    rows = "".join(
        f'<li><a class="v-n" href="product.html?id={esc(p["sku"])}">{esc(re.sub(r"^Toocki\s+","",p["name"]))[:50]}</a>'
        f'<span class="v-s">{esc(p["sku"])}</span>'
        f'<span class="v-p">{esc(_price(p))}</span></li>'
        for p in sorted(skus, key=lambda x: x["name"]))
    return (f'      <figure class="g-item fam" data-cid="fam:{esc(key)}">\n        {media}\n'
        f'        <figcaption><span class="badge fam">{len(skus)} variants</span><b>{name}</b>'
        f'<span class="notes">{notes}</span>'
        + (f'<span class="vline">{esc(vline)}</span>' if vline else "")
        + f'<span class="g-price">{esc(pr)}</span>'
        f'<details><summary>See all {len(skus)} SKUs</summary><ul class="vlist">{rows}</ul></details>'
        f'</figcaption>\n      </figure>')

def curated_card(p):
    img = _cover(p["slug"], CURATED_IMG.get(p["slug"]))
    inner = (f'<img src="{img}" alt="{esc(p["name"])}" loading="lazy">' if img
             else "<div class='ph'><b>ARRIVING</b><span>with shipment</span></div>")
    media = f'<a href="product.html?id={p["slug"]}">{inner}</a>'
    badge = ('<span class="badge cur">in stock</span>' if img else '<span class="badge desc">arriving</span>')
    return (f'      <figure class="g-item cur" data-product="{p["slug"]}" data-cid="{p["slug"]}">\n        {media}\n'
        f'        <figcaption>{badge}<b>{esc(p["name"])}</b>'
        f'<span class="sku">view details \u2192</span>'
        f'<span class="notes">{esc(trim_note(p["notes"]))}</span>'
        f'<span class="g-price">{esc(p["price"])}</span></figcaption>\n      </figure>')

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
  .badge.fam{background:#2b1a33;color:#d78bff;border:1px solid #4d2b5c;}
  .g-item.cur{border-color:#1d4d5c;}
  .g-item.fam{border-color:#3a2a45;}
  .vline{display:block;font-family:var(--mono);font-size:10.5px;color:#b48ad0;margin-top:6px;letter-spacing:.02em;}
  details{margin-top:8px;border-top:1px solid var(--line);padding-top:7px;}
  summary{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);cursor:pointer;list-style:none;}
  summary::-webkit-details-marker{display:none;}
  summary:before{content:"+ ";color:var(--accent);}
  details[open] summary:before{content:"\u2212 ";}
  .vlist{list-style:none;margin-top:7px;display:flex;flex-direction:column;gap:3px;}
  .vlist li{display:flex;align-items:baseline;gap:8px;font-family:var(--mono);font-size:10px;color:var(--muted);}
  .v-n{flex:1 1 auto;}
  .v-n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1 1 auto;}
  .v-p{color:var(--accent);flex:0 0 auto;}
  .v-s{font-family:var(--mono);font-size:9px;color:#5a6270;flex:0 0 auto;}
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

PAGES = {
 "cables":   ("Cables", "Every cable line Toocki makes, grouped by power tier and folded so repeat lengths and colours sit on one card."),
 "chargers": ("Chargers", "Wall, car and wireless charging, grouped by power and folded by plug standard."),
 "cases":    ("Cases", "iPhone and Samsung cases, including the fully unbranded line \u2014 no logo anywhere on the product or the packaging."),
 "mounts":   ("Mounts & Stands", "Stands, holders and car mounts \u2014 the small-ticket add-ons that sell with every phone."),
 "power":    ("Power & Audio", "Power banks, audio and the 240W lanyard adapter line."),
 "adapters": ("Adapters", "Travel adapters, AV and audio adapters, HDMI, OTG converters and network cards."),
}

SUMMARY = []
for key, (title, lede) in PAGES.items():
    items = GROUPS.get(key, [])
    secs = sections_for(key, items)
    cur = [p for p in CURATED.values() if p.get("page") == key]
    tot_lines = sum(len(s["i"]) for s in secs)
    tot_cards = 0

    jump = f'<a href="#s-cur">In stock<b>{len(cur)}</b></a>' if cur else ""
    body = []
    if cur:
        body.append('<section class="sec" id="s-cur" style="border-top:0">\n'
            f'  <div class="sec-head"><h2>In stock in Toronto</h2><span class="n">{len(cur)} lines</span></div>\n'
            '  <p class="sec-desc">On the shelf now \u2014 fitted, checked, and shipping same week across the GTA.</p>\n'
            '  <div class="grid">\n' + "\n".join(curated_card(p) for p in cur) + '\n  </div>\n</section>')
    for i, s in enumerate(secs):
        singles, folds = fold(s["i"])
        ncards = len(singles) + len(folds)
        tot_cards += ncards
        count = (f'{len(s["i"])} lines' if ncards == len(s["i"])
                 else f'{len(s["i"])} lines \u00b7 {ncards} cards')
        jump += f'<a href="#s{i}">{esc(s["t"])}<b>{len(s["i"])}</b></a>'
        cards = [card_family(k, v) for k, v in folds] + [card_single(p) for p in singles]
        body.append(f'<section class="sec" id="s{i}" data-page="{key}"{" style=\"border-top:0\"" if not cur and i==0 else ""}>\n'
            f'  <div class="sec-head"><h2>{esc(s["t"])}</h2><span class="n">{count}</span></div>\n'
            f'  <p class="sec-desc">{esc(s["d"])}</p>\n'
            '  <div class="grid">\n' + "\n".join(cards) + '\n  </div>\n</section>')

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
  <p>{lede} {tot_lines + len(cur)} lines across {len(secs) + (1 if cur else 0)} families, shown as {tot_cards + len(cur)} cards.</p>
</div>
{chr(10).join(body)}
<div class="wrap"><p class="count-note">{tot_lines + len(cur)} lines on this page \u00b7 {withimg} shown with photography \u00b7 fold any multi-SKU card to see every variant and price \u00b7 ask for a quote on any line.</p></div>
{FOOT}
<script src="catalog-admin.js"></script>
</body>
</html>"""
    (HERE / f"{key}.html").write_text(doc, encoding="utf-8")
    SUMMARY.append((key, tot_lines + len(cur), tot_cards + len(cur), len(secs) + (1 if cur else 0)))

# ── catalog.js — the full line registry that powers detail pages + the Studio ──
# One object per marketable line: curated slugs, single-SKU cards, and every
# variant inside a folded family card. Keyed by pid (slug or SKU).
def _catalog_js():
    cat = {}
    for p in CURATED.values():
        slug = p["slug"]
        img = CURATED_IMG.get(slug)
        imgs = [img] if img else []
        cat[slug] = {"pid": slug, "name": p["name"], "notes": trim_note(p.get("notes") or ""),
                     "price": p["price"], "page": p.get("page") or "cases", "kind": "cur",
                     "sku": slug, "imgs": imgs}
    for key, items in GROUPS.items():
        for p in items:
            imgs = [(IMG + p["img"])] if p.get("img") else []
            cat[p["sku"]] = {"pid": p["sku"], "name": p["name"],
                             "notes": trim_note(p.get("feat_clean") or p.get("feat") or ""),
                             "price": p["price_line"], "page": key, "kind": "single",
                             "sku": p["sku"], "imgs": imgs}
    # folded-family membership: every variant pid -> family key (for detail pages)
    fams = {}
    for key, items in GROUPS.items():
        fams.setdefault(str(key), {})
        by_fam = defaultdict(list)
        for p in items:
            by_fam[family_key(p["name"])].append(p)
        for fk, v in by_fam.items():
            if len(v) > 1:
                rep = next((q for q in v if q.get("img")), v[0])
                for q in v:
                    if q["sku"] in cat:
                        cat[q["sku"]]["fam"] = fk
                        cat[q["sku"]]["fam_name"] = pretty(fk)
                        cat[q["sku"]]["fam_rep"] = rep["sku"]
    out = "/* generated by build_toocki_tandem.py — full catalog registry */\n"
    out += "window.MIKOSHI_CATALOG = " + json.dumps(cat, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + ";\n"
    (HERE / "catalog.js").write_text(out, encoding="utf-8")
    return len(cat)

N_CAT = _catalog_js()
print("catalog.js lines:", N_CAT)

print(f"{'page':10s} {'lines':>6s} {'cards':>6s} {'cut':>6s} {'sections':>9s}")
print("-" * 46)
TL = TC = 0
for k, lines, cards, secs_n in SUMMARY:
    TL += lines; TC += cards
    print(f"{k:10s} {lines:6d} {cards:6d} {(1-cards/lines)*100:5.0f}% {secs_n:9d}")
print("-" * 46)
print(f"{'TOTAL':10s} {TL:6d} {TC:6d} {(1-TC/TL)*100:5.0f}%")
