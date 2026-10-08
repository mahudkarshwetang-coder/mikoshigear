#!/bin/bash
# Mikoshi Catalog Studio — deploy from Bumblebee (the machine with push rights).
# Run ON BUMBLEBEE:  bash ~/Desktop/Mikoshi/site/studio/deploy-from-bumblebee.sh
#
# Ships the Catalog Studio layer:
#   * catalog.js              — the 573-line registry (detail pages for every line)
#   * catalog-admin.js        — runtime order/cover/gallery layer (no rebuild needed)
#   * product.html            — serves every line + family cross-links
#   * admin.html              — retirement page (old Supabase admin is dead)
#   * build_toocki_tandem.py  — builder now emits hooks + catalog.js
#   * studio/                 — the local admin app
#   * six category pages      — hooks injected with TEXT PARITY (checked below)
#
# Safety: backs up first, refuses to ship if any page's visible text differs
# from what it replaced, and verifies the live site afterwards.
set -e
cd "$(dirname "$0")/.."      # repo root
STAMP=$(date +%Y%m%d-%H%M%S)
echo "== Catalog Studio deploy $STAMP =="

# ── 0. sanity: required files present ──
for f in catalog.js catalog-admin.js product.html admin.html studio/server.py studio/index.html; do
  [ -f "$f" ] || { echo "FAIL: missing $f — copy the studio kit into the repo first"; exit 1; }
done

# ── 1. backup ──
mkdir -p ".studio-backups/$STAMP"
for f in catalog_admin.json catalog.js catalog-admin.js product.html admin.html \
         build_toocki_tandem.py cases.html cables.html adapters.html chargers.html power.html mounts.html; do
  [ -f "$f" ] && cp -p "$f" ".studio-backups/$STAMP/$f"
done
echo "backed up → .studio-backups/$STAMP"

# ── 2. parity guard: page text must be unchanged vs git HEAD ──
python3 - <<'PY' || exit 1
import re, subprocess, sys, html as ihtml
def vis(s):
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", ihtml.unescape(re.sub(r"<[^>]+>", "\x00", s))).strip()
bad = 0
for p in ["cases","cables","adapters","chargers","power","mounts"]:
    new = open(f"{p}.html", encoding="utf-8").read()
    old = subprocess.run(["git","show",f"HEAD:{p}.html"], capture_output=True, text=True).stdout
    if not old:
        print(f"  {p}: no HEAD version (new page) — skipped")
        continue
    same = vis(new) == vis(old)
    print(f"  {p}: text {'identical ✓' if same else 'CHANGED ✗'}")
    bad += 0 if same else 1
    if not same:
        a, b = vis(new), vis(old)
        for i,(x,y) in enumerate(zip(a,b)):
            if x != y:
                print("    first diff:", repr(a[i-60:i+60]), "vs", repr(b[i-60:i+60])); break
sys.exit(1 if bad else 0)
PY

# ── 3. structural guards ──
for p in cases cables adapters chargers power mounts; do
  n=$(grep -oE '<figure class="g-item' $p.html | wc -l | tr -d ' ')
  c=$(grep -oE 'data-cid="' $p.html | wc -l | tr -d ' ')
  echo "  $p: cards=$n hooks=$c"
  [ "$n" -gt 0 ] && [ "$n" = "$c" ] || { echo "FAIL: $p hooks mismatch"; exit 1; }
  grep -q "catalog-admin.js" $p.html || { echo "FAIL: $p missing script tag"; exit 1; }
done
python3 - <<'PY' || exit 1
import json, re
t = open("catalog.js", encoding="utf-8").read()
d = json.loads(t[t.index("{"):t.rindex("}")+1])
assert len(d) >= 550, f"catalog.js only {len(d)} entries"
bad = [k for k,v in d.items() if re.search(r"#NAME\?|#REF|#N/A|#VALUE", v["name"] or "")]
assert not bad, f"error literals: {bad[:5]}"
print(f"  catalog.js: {len(d)} lines, clean ✓")
PY

# ── 4. commit + push (explicit paths only — repo root has debug debris) ──
git add -- catalog.js catalog-admin.js catalog_admin.json product.html admin.html \
           build_toocki_tandem.py studio .gitignore \
           cases.html cables.html adapters.html chargers.html power.html mounts.html
if git diff --cached --quiet; then
  echo "nothing new to commit — already deployed? verifying live anyway…"
else
  git commit -m "Catalog Studio: full-catalog admin (order/covers/galleries, text-parity pages) + detail pages for all 573 lines"
fi
git push
echo "pushed."

# ── 5. verify live (~60 s for Pages) ──
echo "waiting 75 s for GitHub Pages…"
sleep 75
fail=0
check() { code=$(curl -s -o /dev/null -w "%{http_code}" -m 20 "$1"); echo "  $2 → $code"; [ "$code" = "200" ] || fail=1; }
check "https://mikoshigear.ca/catalog.js" "catalog.js"
check "https://mikoshigear.ca/catalog-admin.js" "catalog-admin.js"
check "https://mikoshigear.ca/catalog_admin.json" "catalog_admin.json"
check "https://mikoshigear.ca/product.html?id=TXCTT1A-SJA03-Z" "detail page (new SKU)"
for p in cases cables adapters chargers power mounts; do
  check "https://mikoshigear.ca/$p.html" "$p.html"
done
n=$(curl -s -m 20 "https://mikoshigear.ca/cables.html" | grep -oE 'data-cid="' | wc -l | tr -d ' ')
echo "  live cables.html hooks: $n"
[ "$n" -gt 100 ] || fail=1
ct=$(curl -sI -m 20 "https://mikoshigear.ca/catalog-admin.js" | grep -i content-type || true)
echo "  catalog-admin.js content-type: $ct"
echo "$ct" | grep -qi "javascript" || fail=1
if [ $fail = 0 ]; then echo "== DEPLOY VERIFIED ✓ =="; else echo "== DEPLOY HAD FAILURES — inspect above =="; exit 1; fi
