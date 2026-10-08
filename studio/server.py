#!/usr/bin/env python3
"""Mikoshi Gear — Catalog Studio server (stdlib only).

A tiny local backend + UI for managing the mikoshigear.ca catalog:
  * drag-reorder product cards on every category page
  * pick any of the 573 lines, manage its photos (reorder / set cover / add / delete)
  * publish = commit + push the tiny data files (no rebuild needed for edits)

Run from the repo root (or anywhere — it finds the repo):
    python3 studio/server.py [--port 8770] [--no-browser]

Design notes
------------
* The LIVE site applies edits at runtime via catalog-admin.js reading
  catalog_admin.json — so ordering/cover/gallery changes go live with a
  ~2 KB data commit, no page rebuild, no external service, no keys.
* Uploaded photos land in mikoshi-img/admin/<pid>/… (inside the repo, so they
  ship with the site). Deleting is restricted to that folder — repo assets
  are never touched.
* Localhost only; single admin; no auth (it binds 127.0.0.1).
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ADMIN_JSON = REPO / "catalog_admin.json"
PAGES = ["cables", "chargers", "cases", "mounts", "power", "adapters"]
UPLOAD_DIR = "mikoshi-img/admin"          # relative to repo
BUILD_SCRIPT = "build_toocki_tandem.py"

_lock = threading.Lock()


# ─────────────────────────── data helpers ───────────────────────────
def load_admin() -> dict:
    if ADMIN_JSON.exists():
        try:
            d = json.loads(ADMIN_JSON.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                d.setdefault("order", {})
                d.setdefault("covers", {})
                d.setdefault("images", {})
                return d
        except Exception as e:
            print("warn: catalog_admin.json unreadable:", e)
    return {"v": 0, "order": {}, "covers": {}, "images": {}}


def save_admin(d: dict) -> None:
    d["v"] = int(time.time() * 1000)
    tmp = ADMIN_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ADMIN_JSON)


def load_catalog_js() -> dict:
    p = REPO / "catalog.js"
    if not p.exists():
        return {}
    t = p.read_text(encoding="utf-8")
    m = re.search(r"window\.MIKOSHI_CATALOG = (\{.*\});", t, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception as e:
        print("warn: catalog.js parse failed:", e)
        return {}


def load_products_js() -> dict:
    p = REPO / "products.js"
    if not p.exists():
        return {}
    t = p.read_text(encoding="utf-8")
    out = {}
    for name in ("MIKOSHI_PRODUCTS", "MIKOSHI_IMAGES"):
        m = re.search(r"window\.%s\s*=\s*(\{.*?\});" % name, t, re.S)
        if m:
            try:
                out[name] = json.loads(m.group(1))
            except Exception:
                out[name] = {}
    return out


def load_curated() -> dict:
    p = REPO / "curated_products.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def page_structure(page: str) -> dict:
    """Parse a built category page → sections with their card cids."""
    f = REPO / f"{page}.html"
    if not f.exists():
        return {"sections": []}
    t = f.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    title = re.search(r"<title>(.*?)</title>", t, re.S)
    secs = []
    for m in re.finditer(r'<section class="sec" id="([^"]+)"[^>]*>(.*?)</section>', t, re.S):
        sid, body = m.group(1), m.group(2)
        h2 = re.search(r"<h2>(.*?)</h2>", body)
        cards = re.findall(r'<figure class="g-item[^"]*"[^>]*data-cid="([^"]+)"', body)
        kinds = re.findall(r'<figure class="g-item([^"]*)"[^>]*data-cid="[^"]+"', body)
        secs.append({
            "id": sid,
            "title": re.sub(r"<[^>]+>", "", h2.group(1)) if h2 else sid,
            "cards": [{"cid": c, "kind": ("cur" if "cur" in k else "fam" if "fam" in k else "single")}
                      for c, k in zip(cards, kinds)],
        })
    return {"title": re.sub(r"<[^>]+>", "", title.group(1)) if title else page, "sections": secs}


def full_catalog() -> dict:
    catalog = load_catalog_js()
    products = load_products_js()
    curated = load_curated()
    pages = {}
    for p in PAGES:
        if (REPO / f"{p}.html").exists():
            pages[p] = page_structure(p)
    return {
        "pages": pages,
        "lines": catalog,
        "products": products.get("MIKOSHI_PRODUCTS") or {},
        "images": products.get("MIKOSHI_IMAGES") or {},
        "curated": curated,
        "generated": time.time(),
    }


# ─────────────────────────── actions ───────────────────────────
def rebuild_inputs_ok():
    """Guard: a rebuild here must be fed the REAL product source. Refuse when the
    source is missing or is the byte-identical stand-in (= SITE_GROUPS.json)."""
    src = REPO / "SITE_GROUPS2.json"
    alt = REPO / "SITE_GROUPS.json"
    if not src.exists():
        return False, ("SITE_GROUPS2.json is not in this copy — the real product source "
                       "lives on the Mac (Bumblebee). Copy it over, or run Rebuild there.")
    if alt.exists():
        try:
            same = hashlib.sha256(src.read_bytes()).digest() == hashlib.sha256(alt.read_bytes()).digest()
        except OSError:
            same = False
        if same:
            return False, ("SITE_GROUPS2.json in this copy is only a stand-in (identical to "
                           "SITE_GROUPS.json) — rebuilding from it WOULD change catalog text. "
                           "Run Rebuild on the Mac, or copy the real SITE_GROUPS2.json over first.")
    return True, ""


def _run_build_locked() -> str:
    r = subprocess.run([sys.executable, BUILD_SCRIPT], cwd=REPO,
                       capture_output=True, text=True, timeout=300)
    return (r.stdout or "") + (r.stderr or "")


def run_build() -> str:
    ok, why = rebuild_inputs_ok()
    if not ok:
        return "REBUILD REFUSED: " + why
    with _lock:
        return _run_build_locked()


def _ssh_ok(host):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", host, "echo UP"],
        capture_output=True, text=True, timeout=25)
    return "UP" in (r.stdout or "")


def _find_bumblebee():
    for host in ("bumblebee", "bumblebee.local", "shwetangmahudkar@192.168.4.31",
                 "shwetangmahudkar@192.168.4.65", "shwetangmahudkar@192.168.4.23"):
        try:
            if _ssh_ok(host):
                return host
        except Exception:
            continue
    return None


def _rsync_to(host, targets, log):
    """scp each existing target to the Bumblebee repo copy."""
    remote = "Desktop/Mikoshi/site/"
    for t in targets:
        p = REPO / t
        if not p.exists():
            continue
        r = subprocess.run(["scp", "-r", "-q", str(p), f"{host}:{remote}"],
                           capture_output=True, text=True, timeout=600)
        log.append(f"$ scp -r {t} → {host}:{remote}  rc={r.returncode}")
        if r.returncode != 0:
            log.append((r.stderr or "").strip())


def git_publish(rebuild: bool) -> str:
    log = []
    with _lock:
        if rebuild:
            log.append("$ python3 " + BUILD_SCRIPT)
            ok, why = rebuild_inputs_ok()
            if not ok:
                log.append("REBUILD REFUSED: " + why)
                log.append("publish stopped — fix the rebuild input first (see above).")
                return "\n".join(log)
            log.append(_run_build_locked())
        add_targets = ["catalog_admin.json", UPLOAD_DIR, "catalog.js", "catalog-admin.js",
                       "product.html", "build_toocki_tandem.py", "studio", "admin.html"]
        if rebuild:
            add_targets += [f"{p}.html" for p in PAGES]

        # ---- can we push from here? try the local repo first ----
        r = subprocess.run(["git", "push"], cwd=REPO, capture_output=True, text=True, timeout=300)
        local_push = r.returncode == 0
        log.append("$ git push (local)\n" + (r.stdout or "") + (r.stderr or ""))

        if local_push:
            # commit happened? push succeeded → ensure a commit exists for new edits
            r2 = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True)
            dirty = [l for l in (r2.stdout or "").splitlines() if l.strip() and not l.strip().startswith("??")]
            if dirty:
                subprocess.run(["git", "add", "--"] + add_targets, cwd=REPO,
                               capture_output=True, text=True)
                msg = "Catalog Studio: " + ("rebuild + " if rebuild else "") + time.strftime("update %Y-%m-%d %H:%M")
                subprocess.run(["git", "commit", "-m", msg], cwd=REPO, capture_output=True, text=True)
                r3 = subprocess.run(["git", "push"], cwd=REPO, capture_output=True, text=True, timeout=300)
                log.append("$ git commit && git push\n" + (r3.stdout or "") + (r3.stderr or ""))
                local_push = r3.returncode == 0
            log.append("pushed ✓ — live on mikoshigear.ca within ~60 s" if local_push
                       else "local push failed after commit — see log")
            return "\n".join(log)

        # ---- fallback: this machine has no GitHub key → stage + ship via Bumblebee ----
        log.append("No local push rights — falling back to the Bumblebee deploy path…")
        host = _find_bumblebee()
        if not host:
            log.append("Bumblebee is not reachable (asleep?). Edits are saved locally; "
                       "wake the Mac and press Publish again, or run the Studio on Bumblebee itself.")
            return "\n".join(log)
        log.append("Bumblebee reachable at " + host)
        _rsync_to(host, add_targets, log)
        remote_cmd = (
            "cd ~/Desktop/Mikoshi/site && "
            "git add -- " + " ".join(f"'{t}'" for t in add_targets) + " && "
            "git commit -m 'Catalog Studio: update '$(date '+%Y-%m-%d %H:%M') ' (via Optimus)' || true && "
            "git push"
        )
        r = subprocess.run(["ssh", host, remote_cmd], capture_output=True, text=True, timeout=600)
        log.append("$ ssh " + host + " git add/commit/push\n" + (r.stdout or "") + (r.stderr or ""))
        if r.returncode == 0 and "main" in (r.stderr or "" + (r.stdout or "")):
            log.append("pushed via Bumblebee ✓ — live on mikoshigear.ca within ~60 s")
        elif r.returncode == 0:
            log.append("remote command finished — check the log for 'Everything up-to-date' (already live) or push output")
        else:
            log.append("remote push failed — see log")
        return "\n".join(log)


def safe_repo_path(rel: str) -> Path:
    p = (REPO / rel).resolve()
    if REPO not in p.parents and p != REPO:
        raise ValueError("path outside repo")
    return p


# ─────────────────────────── HTTP ───────────────────────────
class Handler(BaseHTTPRequestHandler):
    server_version = "CatalogStudio/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ---- helpers ----
    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw or b"{}")
        except Exception:
            return {}

    def _static(self, rel: str, cache=False):
        try:
            p = safe_repo_path(rel)
        except ValueError:
            return self._send(403, b"forbidden", "text/plain")
        if not p.exists() or not p.is_file():
            return self._send(404, b"not found", "text/plain")
        ctype = {
            ".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8", ".css": "text/css; charset=utf-8",
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp", ".svg": "image/svg+xml", ".ico": "image/x-icon",
            ".avif": "image/avif",
        }.get(p.suffix.lower(), "application/octet-stream")
        body = p.read_bytes()
        extra = None if cache else {"Cache-Control": "no-store"}
        self._send(200, body, ctype, extra)

    # ---- routes ----
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(u.path)
        if path in ("/", "/index.html"):
            return self._static("studio/index.html")
        if path.startswith("/api/"):
            return self.api_get(path, urllib.parse.parse_qs(u.query))
        if path.startswith("/site/"):
            return self._static(path[len("/site/"):])
        if path.startswith("/studio/"):
            return self._static(path[1:])
        return self._static(path[1:])

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(u.path)
        q = urllib.parse.parse_qs(u.query)
        if path == "/api/state":
            data = self._body_json()
            with _lock:
                save_admin(data)
            return self._json({"ok": True, "v": data.get("v")})
        if path == "/api/upload":
            return self.api_upload(q)
        if path == "/api/delete-file":
            return self.api_delete()
        if path == "/api/publish":
            body = self._body_json()
            log = git_publish(bool(body.get("rebuild")))
            return self._json({"ok": True, "log": log})
        if path == "/api/build":
            return self._json({"ok": True, "log": run_build()})
        return self._json({"ok": False, "error": "unknown endpoint"}, 404)

    def api_get(self, path, q):
        if path == "/api/catalog":
            return self._json(full_catalog())
        if path == "/api/state":
            return self._json(load_admin())
        if path == "/api/health":
            return self._json({"ok": True, "repo": str(REPO)})
        return self._json({"ok": False, "error": "unknown endpoint"}, 404)

    def api_upload(self, q):
        pid = (q.get("pid") or [""])[0]
        name = (q.get("name") or ["photo.jpg"])[0]
        if not pid:
            return self._json({"ok": False, "error": "pid required"}, 400)
        n = int(self.headers.get("Content-Length") or 0)
        blob = self.rfile.read(n) if n else b""
        if not blob:
            return self._json({"ok": False, "error": "empty body"}, 400)
        safe_pid = re.sub(r"[^A-Za-z0-9._-]", "_", pid)
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", name)[-80:]
        folder = REPO / UPLOAD_DIR / safe_pid
        folder.mkdir(parents=True, exist_ok=True)
        fname = "%d-%s" % (int(time.time() * 1000), safe_name)
        fp = folder / fname
        fp.write_bytes(blob)
        rel = f"{UPLOAD_DIR}/{safe_pid}/{fname}"
        return self._json({"ok": True, "url": rel, "bytes": len(blob)})

    def api_delete(self):
        data = self._body_json()
        url = (data.get("url") or "").strip()
        if not url.startswith(UPLOAD_DIR + "/"):
            return self._json({"ok": False, "error": "only files under " + UPLOAD_DIR + " can be deleted"}, 400)
        try:
            p = safe_repo_path(url)
        except ValueError:
            return self._json({"ok": False, "error": "path outside repo"}, 400)
        if p.exists() and p.is_file():
            p.unlink()
            # prune empty dir
            try:
                if p.parent.exists() and not any(p.parent.iterdir()):
                    p.parent.rmdir()
            except OSError:
                pass
            return self._json({"ok": True})
        return self._json({"ok": True, "note": "file was already absent"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print("Mikoshi Catalog Studio")
    print("  repo:", REPO)
    print("  ui:  ", url)
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
