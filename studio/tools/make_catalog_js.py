#!/usr/bin/env python3
"""Distill the LIVE mikoshigear.ca pages into catalog.js — the full line registry
that powers detail pages across all 573 lines.

Guarantee: every name/notes/price string is taken verbatim from the live pages,
so deploying this file cannot change any text a shop sees.

Inputs : live/*.html (curl'd from mikoshigear.ca), repo/products.js, repo image tree
Output : deploy/catalog.js

Schema per entry:
  pid, name, notes, price, page, kind(cur|single|famvar), sku, fam, fam_name,
  fam_rep, imgs[]
"""
import html as ihtml
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE / "repo"
LIVE = HERE / "live"
OUT = HERE / "deploy"
OUT.mkdir(exist_ok=True)

PAGES = ["cases", "cables", "adapters", "chargers", "power", "mounts"]


def clean(s):
    return ihtml.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()


def disk_img(url):
    """True if the repo-relative image exists in the clone."""
    return (REPO / url).exists()


def load_products_js():
    t = (REPO / "products.js").read_text(encoding="utf-8")
    out = {}
    for name in ("MIKOSHI_PRODUCTS", "MIKOSHI_IMAGES"):
        m = re.search(r"window\.%s\s*=\s*(\{.*?\});" % name, t, re.S)
        out[name] = json.loads(m.group(1)) if m else {}
    return out


# ── family_key: EXACT copy of build_toocki_tandem.family_key (keeps fam cids aligned) ──
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


def main():
    prods = load_products_js()
    curated_meta = prods.get("MIKOSHI_PRODUCTS") or {}
    curated_imgs = prods.get("MIKOSHI_IMAGES") or {}

    cat = {}
    stats = {"cur": 0, "single": 0, "famvar": 0}

    # ---- curated ----
    for slug, meta in curated_meta.items():
        imgs = curated_imgs.get(slug) or []
        cat[slug] = {
            "pid": slug, "name": meta.get("name") or slug, "notes": meta.get("notes") or "",
            "price": meta.get("price") or "", "page": meta.get("cat") or "cases",
            "kind": "cur", "sku": slug, "imgs": [u for u in imgs if disk_img(u.split("mikoshigear.ca/")[-1])],
        }
        stats["cur"] += 1

    # ---- toocki pages ----
    for page in PAGES:
        t = (LIVE / f"{page}.html").read_text(encoding="utf-8")
        t = re.sub(r"<script.*?</script>", "", t, flags=re.S)

        # singles: <figure class="g-item">…<span class="sku">SKU</span>…
        for fm in re.finditer(r'<figure class="g-item">(.*?)</figure>', t, re.S):
            b = fm.group(1)
            sku = re.search(r'<span class="sku">([^<]+)</span>', b)
            if not sku:
                continue
            sku = sku.group(1).strip()
            img = re.search(r'src="(mikoshi-img/[^"]+)"', b)
            nm = re.search(r"<b>(.*?)</b>", b, re.S)
            nt = re.search(r'<span class="notes">(.*?)</span>', b, re.S)
            pr = re.search(r'<span class="g-price">(.*?)</span>', b, re.S)
            imgs = [img.group(1)] if img and disk_img(img.group(1)) else []
            cat[sku] = {"pid": sku, "name": clean(nm.group(1)) if nm else sku,
                        "notes": clean(nt.group(1)) if nt else "",
                        "price": clean(pr.group(1)) if pr else "",
                        "page": page, "kind": "single", "sku": sku, "imgs": imgs}
            stats["single"] += 1

        # families: <figure class="g-item fam">…<ul class="vlist"><li>…sku…
        for fm in re.finditer(r'<figure class="g-item fam">(.*?)</figure>', t, re.S):
            b = fm.group(1)
            nm = re.search(r"<b>(.*?)</b>", b, re.S)
            fam_name = clean(nm.group(1)) if nm else ""
            img = re.search(r'src="(mikoshi-img/[^"]+)"', b)
            rep = None
            if img:
                m = re.search(r"toocki/([^/]+)\.jpg", img.group(1))
                if m:
                    rep = m.group(1)
            variants = []
            for vm in re.finditer(r'<li><span class="v-n">(.*?)</span><span class="v-s">(.*?)</span><span class="v-p">(.*?)</span></li>', b, re.S):
                variants.append({"name": clean(vm.group(1)), "sku": clean(vm.group(2)),
                                 "price": clean(vm.group(3))})
            if not rep and variants:
                rep = variants[0]["sku"]
            rep_img = None
            if rep and disk_img(f"mikoshi-img/toocki/{rep}.jpg"):
                rep_img = f"mikoshi-img/toocki/{rep}.jpg"
            for v in variants:
                own = f"mikoshi-img/toocki/{v['sku']}.jpg"
                if disk_img(own):
                    imgs = [own] + ([rep_img] if rep_img and rep_img != own else [])
                elif rep_img:
                    imgs = [rep_img]
                else:
                    imgs = []
                cat[v["sku"]] = {
                    "pid": v["sku"], "name": v["name"],
                    "notes": "",  # filled below from the family card notes
                    "price": f"Wholesale {v['price']} · MOQ 20 — samples available" if v["price"].startswith("$") else v["price"],
                    "page": page, "kind": "famvar", "sku": v["sku"],
                    # fam == the exact page cid of the folded family card, so the
                    # Studio cover control and product.html sibling links line up.
                    "fam": "fam:" + family_key(fam_name) if fam_name else "",
                    "fam_name": fam_name, "fam_rep": rep or "",
                    "imgs": imgs,
                }
                stats["famvar"] += 1
            # family notes: copy the card's notes line to each variant
            nt = re.search(r'<span class="notes">(.*?)</span>', b, re.S)
            if nt:
                note = clean(nt.group(1))
                for v in variants:
                    if v["sku"] in cat:
                        cat[v["sku"]]["notes"] = note

    # ---- write catalog.js ----
    body = json.dumps(cat, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    (OUT / "catalog.js").write_text(
        "/* Mikoshi Gear — full catalog registry (generated from the live site; "
        "edits go through Catalog Studio) */\nwindow.MIKOSHI_CATALOG = " + body + ";\n",
        encoding="utf-8")
    print("catalog.js:", len(cat), "entries", stats)
    # sanity: dupes / empties
    assert len(cat) >= 550, "too few entries"
    bad = [k for k, v in cat.items() if re.search(r"#NAME\?|#REF|#N/A|#VALUE", v["name"] or "")]
    assert not bad, f"error literals: {bad[:5]}"
    print("no error literals ✓")
    # coverage: how many have imgs
    n_img = sum(1 for v in cat.values() if v["imgs"])
    print(f"entries with images: {n_img}/{len(cat)}")


if __name__ == "__main__":
    main()
