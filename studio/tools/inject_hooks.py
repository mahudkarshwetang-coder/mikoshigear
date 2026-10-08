#!/usr/bin/env python3
"""Inject admin hooks into the LIVE page HTML — attributes + one script tag only.

Guarantee: NO text node is ever modified. The transform adds
  * data-cid="<ident>" to every <figure class="g-item…">
  * <script src="catalog-admin.js"></script> before </body>
and nothing else. Byte-compare the visible text before/after to prove parity.

Family-card cids are computed with a local copy of the builder's family_key(),
verified against the builder's own output for the same cards.
"""
import html as ihtml
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
LIVE = HERE / "live"
OUT = HERE / "deploy"

PAGES = ["cases", "cables", "adapters", "chargers", "power", "mounts"]

# ── mirror of build_toocki_tandem.family_key (keep in sync) ──
COLOURS = r"\b(Black|White|Grey|Gray|Blue|Green|Pink|Purple|Red|Yellow|Silver|Clear|Gunmetal|Titanium|Gold|Orange|Deep Space Grey|Space Grey)\b"
LENGTHS = r"(\d+(?:\.\d+)?\s*(?:m\b|meters?\b|M\b|Meter\b|Meters\b))"
PLUGS = r"\b(US Standard|EU Standard|UK Standard|Korean Standard|Australian Standard|American Standard|European Standard|British Standard|US Version|EU Version|UK Version|Korean Version|US Spec(?:ification)?|EU Spec(?:ification)?|UK Spec(?:ification)?|Korean Spec(?:ification)?)\b"
PACK = r"(\((?:English|Korean)?\s*(?:Color|Colour)?\s*Box\)|\(English Bagged\)|\(English Packed\)|\(Bagged\)|\(Color Box\)|English Bagged|English Packed|2\s*Pack)"


def family_key(name):
    s = name
    s = re.sub(r"\s*\u2014\s*[A-Z0-9\-]{4,}\s*$", "", s)
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


def visible_text(doc):
    t = re.sub(r"<script.*?</script>", "", doc, flags=re.S)
    t = re.sub(r"<[^>]+>", "\x00", t)
    return re.sub(r"\s+", " ", ihtml.unescape(t)).strip()


def inject_page(page):
    src = (LIVE / f"{page}.html").read_text(encoding="utf-8")
    before_txt = visible_text(src)
    out = []
    last = 0
    stats = {"cur": 0, "single": 0, "fam": 0}

    fig_re = re.compile(r'<figure class="g-item([^"]*)"([^>]*)>(.*?)</figure>', re.S)
    for m in fig_re.finditer(src):
        klass, attrs, body = m.group(1), m.group(2), m.group(3)
        if "data-cid=" in attrs:
            continue  # already hooked
        cid = None
        if "cur" in klass:
            dp = re.search(r'data-product="([^"]+)"', attrs)
            cid = dp.group(1) if dp else None
            stats["cur"] += 1
        elif "fam" in klass:
            nm = re.search(r"<b>(.*?)</b>", body, re.S)
            if nm:
                fam_name = ihtml.unescape(re.sub(r"<[^>]+>", " ", nm.group(1))).strip()
                cid = "fam:" + family_key(fam_name)
            stats["fam"] += 1
        else:
            sk = re.search(r'<span class="sku">([^<]+)</span>', body)
            cid = sk.group(1).strip() if sk else None
            stats["single"] += 1
        if not cid:
            continue
        out.append(src[last:m.start()])
        out.append(f'<figure class="g-item{klass}" data-cid="{cid}"{attrs}>')
        out.append(body)
        out.append("</figure>")
        last = m.end()
    out.append(src[last:])
    res = "".join(out)

    # script tag
    if "catalog-admin.js" not in res:
        res = res.replace("</body>", '<script src="catalog-admin.js"></script>\n</body>', 1)

    after_txt = visible_text(res)
    if before_txt != after_txt:
        print(f"  !! TEXT CHANGED on {page} — aborting")
        # show first difference for debugging
        for i, (a, b) in enumerate(zip(before_txt, after_txt)):
            if a != b:
                print("   at", i, repr(before_txt[i-60:i+60]), "->", repr(after_txt[i-60:i+60]))
                break
        sys.exit(1)
    (OUT / f"{page}.html").write_text(res, encoding="utf-8")
    print(f"  {page}: cur={stats['cur']} single={stats['single']} fam={stats['fam']} "
          f"| text parity ✓ | +script={'catalog-admin.js' in res}")


def main():
    OUT.mkdir(exist_ok=True)
    print("injecting hooks into live pages (text-parity guarded):")
    for p in PAGES:
        inject_page(p)


if __name__ == "__main__":
    main()
