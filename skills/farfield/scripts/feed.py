#!/usr/bin/env python3
"""Stage and fetch public evidence files. Stdlib only; no models, keys or database.

Can also run as a standalone script: python3 scripts/feed.py --help.
"""
import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 8 * 1024 * 1024
IDEA_FIELDS = ("id", "name", "summary", "heat", "families", "sources", "first_seen", "months_seen")
QUOTE_FIELDS = ("quote", "url", "speaker", "date", "source", "doc_id", "pid", "excerpt")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("file exceeds feed size limit")
    return json.loads(raw)


def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("expected YYYY-MM-DD date")
    return date.fromisoformat(value)


def validate(pack):
    if not isinstance(pack, dict) or pack.get("schema_version") != 1:
        raise ValueError("unsupported evidence schema")
    as_of = iso_day(pack["as_of"])
    if not isinstance(pack.get("sample", False), bool):
        raise ValueError("sample must be a boolean")
    if not isinstance(pack["ideas"], list):
        raise ValueError("ideas must be a list")
    seen = set()
    for idea in pack["ideas"]:
        ident = idea["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("idea IDs must be unique nonempty strings")
        seen.add(ident)
        for field in ("name", "summary"):
            if not isinstance(idea[field], str) or not idea[field].strip():
                raise ValueError(f"{ident}: missing {field}")
        sources = idea["sources"]
        if not isinstance(sources, list) or not sources or any(not isinstance(s, str) or not s for s in sources):
            raise ValueError(f"{ident}: missing sources")
        if not isinstance(idea["quotes"], list) or not idea["quotes"]:
            raise ValueError(f"{ident}: no supporting quotes")
        for quote in idea["quotes"]:
            text, excerpt = quote["quote"], quote["excerpt"]
            if not isinstance(text, str) or not text.strip() or not isinstance(excerpt, str) or text not in excerpt:
                raise ValueError(f"{ident}: quote not verbatim in source excerpt")
            if quote["source"] not in sources or not quote.get("doc_id"):
                raise ValueError(f"{ident}: missing document provenance")
            url = urlparse(quote["url"])
            if url.scheme not in ("https", "http") or not url.hostname:
                raise ValueError(f"{ident}: invalid source URL")
            if iso_day(quote["date"]) > as_of:
                raise ValueError(f"{ident}: quote newer than evidence cutoff")
    return pack


def public_pack(base):
    """Allowlist only world evidence, never copy arbitrary run/profile fields."""
    pack = {"schema_version": 1, "as_of": base["as_of"][:10],
            "sample": base.get("sample", False), "ideas": []}
    for idea in base["ideas"]:
        row = {key: idea[key] for key in IDEA_FIELDS if key in idea}
        row["quotes"] = [{key: quote.get(key) for key in QUOTE_FIELDS} for quote in idea.get("quotes", [])]
        pack["ideas"].append(row)
    return validate(pack)


def atomic_write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".feed-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def manifest_for(raw, as_of):
    digest = hashlib.sha256(raw).hexdigest()
    return {"schema_version": 1, "as_of": as_of,
            "path": f"objects/{digest}.json", "sha256": digest}


def check_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("unsupported manifest schema")
    digest = manifest.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid SHA-256")
    if manifest.get("path") != f"objects/{digest}.json":
        raise ValueError("unsafe or mismatched object path")
    iso_day(manifest["as_of"])
    return manifest


def checked_object(manifest, raw):
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("feed checksum mismatch")
    pack = validate(parse(raw))
    if pack["as_of"] != manifest["as_of"]:
        raise ValueError("feed cutoff differs from manifest")
    return pack


def stage(base, out):
    pack = public_pack(base)
    raw = encoded(pack)
    if len(raw) > MAX_BYTES:
        raise ValueError("feed exceeds size limit; reduce the evidence window")
    manifest = manifest_for(raw, pack["as_of"])
    root = Path(out).expanduser()
    # Publish bytes first, pointer last. This only writes locally, never commits/pushes.
    atomic_write(root / manifest["path"], raw)
    atomic_write(root / "latest.json", encoded(manifest))
    return manifest


def read_url(url):
    parsed = urlparse(url)
    local_test = parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme != "https" and not local_test:
        raise ValueError("feed URL must use HTTPS (localhost HTTP allowed for tests)")
    if parsed.username or parsed.password:
        raise ValueError("do not put credentials in feed URLs")
    request = Request(url, headers={"User-Agent": "farfield-feed/1"})
    with urlopen(request, timeout=20) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("download exceeds size limit")
    return raw


def cached(cache, url):
    saved = parse((cache / "current.json").read_bytes())
    if saved.get("url") != url:
        raise ValueError("cached feed belongs to another URL")
    manifest = check_manifest(saved["manifest"])
    return manifest, checked_object(manifest, (cache / manifest["path"]).read_bytes())


def fetch(url, cache, *, offline=False, muted=(), today=None, stale_days=40):
    cache = Path(cache).expanduser()
    warning = None
    status = "downloaded"
    try:
        if offline:
            raise OSError("offline requested")
        manifest = check_manifest(parse(read_url(url)))
        raw = read_url(urljoin(url, manifest["path"]))
        pack = checked_object(manifest, raw)
        atomic_write(cache / manifest["path"], raw)
        atomic_write(cache / "current.json", encoded({"url": url, "manifest": manifest}))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        # Never replace the last good pointer on a failed refresh.
        manifest, pack = cached(cache, url)
        status, warning = "cached", str(error)
    age = ((today or date.today()) - iso_day(pack["as_of"])).days
    denied = set(muted)
    # A summary may mix sources: drop it whole rather than hide a citation and retain its claims.
    selected = {**pack, "ideas": [i for i in pack["ideas"] if not denied.intersection(i["sources"])]}
    return {"status": status, "warning": warning, "sha256": manifest["sha256"],
            "age_days": age, "stale": age > stale_days or age < 0,
            "excluded_ideas": len(pack["ideas"]) - len(selected["ideas"]), "evidence": selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("stage", help="prepare public files locally; never publish")
    build.add_argument("base", type=Path)
    build.add_argument("out", type=Path)
    pull = sub.add_parser("fetch", help="download individual data files without git")
    pull.add_argument("url", help="HTTPS URL to latest.json")
    pull.add_argument("cache", type=Path)
    pull.add_argument("--offline", action="store_true")
    pull.add_argument("--mute", action="append", default=[])
    args = parser.parse_args()
    try:
        result = (stage(parse(args.base.read_bytes()), args.out) if args.command == "stage" else
                  fetch(args.url, args.cache, offline=args.offline, muted=args.mute))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(2, f"FAILED: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
