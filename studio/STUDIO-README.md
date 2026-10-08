# Mikoshi Gear — Catalog Studio

**What it is:** your own local admin for mikoshigear.ca — reorder the product cards on
every category page, manage photos for **all 573 lines**, pick any photo as a card's face,
and publish. It runs on your machine; nothing extra to pay for, no external service.

---

## Run it

### On the Windows PC (Optimus)
1. Open the folder `OneDrive/Desktop/mikoshigear/site-catalog-admin/`
2. Double-click **`studio/start-studio.bat`**
3. Your browser opens `http://127.0.0.1:8770` — that's the Studio.

### On the Mac (Bumblebee)
1. Open Terminal in `~/Desktop/Mikoshi/site/`
2. Run: `python3 studio/server.py`
3. Open the address it prints (`http://127.0.0.1:8770`)

> First run on the Mac: if `catalog.js` is missing, the Studio still works
> (it lists cards from the built pages). Photos and ordering work everywhere.

---

## The three tabs

| Tab | What you do |
|---|---|
| **Cards** | Pick a category page → drag any card to move it. The order is saved and applied on the live site at load. |
| **Photos** | Search any of the 573 lines by name or SKU → open it → drag photos to reorder, **★ set cover** (card + hero image), **add** new photos (drop or click), **delete** uploads. |
| **Publish** | **Publish edits (fast)** — stages ordering/cover/photo changes and pushes a small data commit. **Rebuild + publish** — also regenerates the pages from the product data (use only when product names/prices change in `SITE_GROUPS2.json`, and prefer running it on the Mac — the full source lives there). |

**Go live happens on Publish** — about a minute after the push, the changes appear on
mikoshigear.ca. Edits before that are staged locally only.

---

## How it works (the important part)

* The live site reads **`catalog_admin.json`** at page load
  (via `catalog-admin.js`) and applies: card order, card covers, and per-line galleries.
  That's why edits need **no page rebuild** and go live in ~60 seconds.
* New photos you add live in **`mikoshi-img/admin/<SKU>/…`** inside the repo, so they ship
  with the site. Deleting only ever touches files in that folder — the 550 catalog photos
  and every other repo file are untouchable from the Studio.
* `catalog.js` is the registry of all 573 lines (names, prices, photos). It powers the
  per-line detail pages (`product.html?id=SKU`) — every card links through to one.

## Publishing

Publish pushes straight to GitHub from whichever machine runs the Studio — the Windows
PC and the Mac each have their own working credentials. Only when a copy can't push
(a fresh clone with no credentials), Publish **hands the files to the Mac over SSH**
and the Mac pushes instead; if the Mac is asleep it says so — press Publish again later.

## If you ever need to rebuild the pages

```
python3 build_toocki_tandem.py     # run in the repo root
```

This regenerates the six category pages and `catalog.js` from `SITE_GROUPS2.json` +
`curated_products.json`. The Studio's **Rebuild + publish** button does the same from
the UI — and refuses if this copy only has the stand-in file (rebuilds belong on the
Mac, where the exact source the live build used lives). Regular Studio edits never need this.

## Files

```
studio/server.py             the local server (stdlib only — no installs)
studio/index.html            the UI
studio/start-studio.bat      Windows launcher
studio/start-studio.command  Mac launcher
studio/deploy-from-bumblebee.sh  one-command deploy on the Mac (backup → checks → push → verify)
studio/tools/                hook injector + registry distiller (maintenance)
catalog-admin.js             the runtime layer the live pages load
catalog.js                   the 573-line registry (generated)
catalog_admin.json           your edits (order/covers/galleries)
```

*Retired: the old `admin.html` + Supabase browser admin — its backend no longer exists.
This Studio replaces it and covers the whole catalog.*
