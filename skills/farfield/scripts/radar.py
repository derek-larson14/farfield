#!/usr/bin/env python3
"""Workspace helper. Local setup; fetch/search/version checks use the network. No model calls.

  radar.py init <workspace>            create the folder, remember where it is
  radar.py where                       print the remembered workspace (exit 3 if none)
  radar.py sources <workspace>         rewrite sources.md (the readable list) and print it
  radar.py source-mode <workspace> only-mine|curated   choose whether future curated defaults are enabled
  radar.py add <workspace> <url> --name NAME [--kind feed|podcast|channel|site|search]
  radar.py mute|unmute <workspace> <source-id>
  radar.py fetch <workspace> <url>     save a page's raw text under evidence/raw/ and print the file path
  radar.py search <workspace> <query>  Exa search (only if EXA_API_KEY is in the keys file)
  radar.py check <pack.json>           structural and exact-quote checks; quotes with a "raw" file are
                                       checked against the page text itself
  radar.py keys [--open]               which optional keys are set (names only); --open edits the file
  radar.py version [--check]           bundled version; --check compares with the published one
"""
import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
CATALOG = SKILL / "catalog.json"
CONFIG = Path(os.environ.get("FARFIELD_CONFIG", Path.home() / ".config" / "farfield"))
POINTER = CONFIG / "workspace"
KEYFILE = CONFIG / "env"
KEYS = {"EXA_API_KEY": "optional: better search and page text (exa.ai)",
        "OPENROUTER_API_KEY": "optional: cloud transcription of podcasts that publish no transcript (openrouter.ai)"}
UA = "Mozilla/5.0 (compatible; farfield/0.1; personal research reader)"
MAX_PAGE = 4 * 1024 * 1024
KINDS = ("feed", "podcast", "channel", "site", "search")


def read_json(path):
    return json.loads(Path(path).expanduser().read_text())


def write_new(path, content):
    """Exclusive creation: setup run twice must never replace the user's edits."""
    try:
        with path.open("x") as handle:
            handle.write(content)
    except FileExistsError:
        pass


def init_workspace(path, remember=True):
    root = Path(path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name in ("me.md", "sources.local.json", "feed.json"):
        write_new(root / name, (TEMPLATES / name).read_text())
    for name in ("context", "briefs", "evidence", "state"):
        (root / name).mkdir(exist_ok=True)
    write_new(root / "feedback.md", "# Feedback\n\nDate | Finding ID | Useful / known / irrelevant | Why\n")
    write_new(root / ".gitignore", "# Private by default. Delete this file if you want this folder in version control.\n*\n")
    write_new(root / "state" / "version", read_json(SKILL / "skill.json")["version"] + "\n")
    write_sources_md(root)
    if remember:
        POINTER.parent.mkdir(parents=True, exist_ok=True)
        POINTER.write_text(str(root) + "\n")
    return root


def where():
    if not POINTER.exists():
        return None
    root = Path(POINTER.read_text().strip())
    return root if (root / "me.md").exists() else None


def keys():
    """Optional keys from the process env, then the keys file. Values never leave this process."""
    found = {name: os.environ[name] for name in KEYS if os.environ.get(name)}
    if KEYFILE.exists():
        for line in KEYFILE.read_text().splitlines():
            name, _, value = line.strip().partition("=")
            value = value.strip().strip('"').strip("'")
            if name in KEYS and value and name not in found:
                found[name] = value
    return found


def open_keys():
    """Create the keys file (owner-only) and open it in an editor. The user pastes; chat never sees it."""
    CONFIG.mkdir(parents=True, exist_ok=True)
    if not KEYFILE.exists():
        KEYFILE.touch(mode=0o600)
        KEYFILE.write_text("# Optional. Farfield works without any of these.\n# Paste a key after the = and save. "
                           "Never paste keys into a chat.\n" + "".join(f"# {why}\n{name}=\n" for name, why in KEYS.items()))
    os.chmod(KEYFILE, 0o600)
    opener = ["open", "-t"] if sys.platform == "darwin" else [os.environ.get("EDITOR") or "xdg-open"]
    try:
        subprocess.Popen(opener + [str(KEYFILE)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
    return KEYFILE


def squash(text):
    """Compare quotes and pages on words, not on curly quotes, dashes or line breaks."""
    table = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u00a0": " "})
    return " ".join(text.translate(table).split())


def to_text(body):
    body = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return squash(html.unescape(body))


def http(url, data=None, headers=None, limit=MAX_PAGE):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read(limit).decode("utf-8", "replace")


def exa(path, payload):
    key = keys().get("EXA_API_KEY")
    if not key:
        raise ValueError("no EXA_API_KEY; run `radar.py keys --open` to add one, or go without")
    return json.loads(http("https://api.exa.ai" + path, json.dumps(payload).encode(),
                           {"x-api-key": key, "Content-Type": "application/json"}))


def fetch(root, url):
    """Raw page text on disk, so a quote can be checked against the page and not against a summary of it."""
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("only http(s) URLs")
    via = "direct"
    try:
        text = to_text(http(url))
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        if not keys().get("EXA_API_KEY"):
            raise ValueError(f"could not fetch {url}: {error}")
        results = exa("/contents", {"urls": [url], "text": True}).get("results") or []
        if not results or not results[0].get("text"):
            raise ValueError(f"could not fetch {url} directly or through Exa")
        text, via = squash(results[0]["text"]), "exa"
    folder = Path(root).expanduser() / "evidence" / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".txt")
    path.write_text(f"{url}\n{text}\n")
    return {"raw": str(path), "chars": len(text), "via": via}


def check_evidence(pack):
    """Structural and quote-substring checks, not truth or origin verification."""
    if not isinstance(pack, dict):
        raise ValueError("pack must be an object")
    date.fromisoformat(pack["as_of"])
    ideas = pack["ideas"]
    if not isinstance(ideas, list):
        raise ValueError("ideas must be a list")
    warnings = []
    ids = set()
    for idea in ideas:
        ident = idea["id"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("idea IDs must be nonempty unique strings")
        ids.add(ident)
        if not idea.get("quotes"):
            raise ValueError(f"{ident}: no quotes")
        for quote in idea["quotes"]:
            text = quote["quote"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{ident}: empty quote")
            url = urlparse(quote["url"])
            if url.scheme not in ("http", "https") or not url.netloc:
                raise ValueError(f"{ident}: invalid source URL")
            if quote.get("date"):
                date.fromisoformat(quote["date"][:10])
            else:
                warnings.append(f"{ident}: unknown publication date")
            excerpt = quote.get("excerpt")
            if excerpt is None:
                warnings.append(f"{ident}: no source excerpt; original quote unverified")
            elif not isinstance(excerpt, str) or text not in excerpt:
                raise ValueError(f"{ident}: quote is not verbatim in excerpt")
            raw = quote.get("raw")
            if raw:
                if squash(text) not in squash(Path(raw).expanduser().read_text()):
                    raise ValueError(f"{ident}: quote is not in the fetched page ({raw})")
            else:
                warnings.append(f"{ident}: quote not checked against the page itself (no raw file)")
            if not quote.get("origin_id"):
                warnings.append(f"{ident}: no origin ID; independence unverified")
    if pack.get("sample"):
        warnings.append("SAMPLE: demonstration only, not current evidence")
    return sorted(set(warnings))


def indexed(sources):
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
    result = {}
    for source in sources:
        ident = source["id"]
        if not isinstance(ident, str) or not ident or ident in result:
            raise ValueError("source IDs must be nonempty unique strings")
        result[ident] = dict(source)
    return result


def resolve_sources(pack, local):
    """Curated defaults plus the user's durable overrides; never mutates either input."""
    sources = indexed(pack["sources"])
    include_curated = local.get("include_curated", True)
    if not isinstance(include_curated, bool):
        raise ValueError("include_curated must be true or false")
    if not include_curated:
        for source in sources.values():
            source["enabled"] = False
    extra = indexed(local.get("add", []))
    if sources.keys() & extra.keys():
        raise ValueError("local additions collide with shared IDs; use a local: prefix")
    if any(not ident.startswith("local:") for ident in extra):
        raise ValueError("local additions must use local: IDs")
    sources.update(extra)
    overrides = local.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("overrides must be an object keyed by source ID")
    unknown = []
    for ident, values in overrides.items():
        if not isinstance(values, dict) or set(values) - {"enabled", "note"}:
            raise ValueError("overrides allow only enabled and note; add a local source to replace a URL")
        if "enabled" in values and not isinstance(values["enabled"], bool):
            raise ValueError("enabled must be true or false")
        if ident not in sources:
            # A mute stays in the user's file even if the curated list drops and re-adds the source.
            unknown.append(ident)
            continue
        sources[ident].update(values)
    return {
        "pack": pack["id"], "version": pack["version"],
        "include_curated": include_curated,
        "sources": list(sources.values()),
        "inactive_override_ids": sorted(unknown),
    }


def local_path(root):
    return Path(root).expanduser() / "sources.local.json"


def load_local(root):
    path = local_path(root)
    local = read_json(path) if path.exists() else {}
    local.setdefault("overrides", {})
    local.setdefault("add", [])
    return local


def save_local(root, local):
    path = local_path(root)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(local, indent=2) + "\n")
    tmp.replace(path)
    write_sources_md(root)


def set_source_mode(root, mode):
    local = load_local(root)
    local["include_curated"] = mode == "curated"
    if mode == "only-mine":
        # Start with no catalog selections; subsequent explicit unmute calls opt in.
        for values in local["overrides"].values():
            values.pop("enabled", None)
    save_local(root, local)


def render_sources(resolved):
    def rows(items):
        out = ["| Source | Kind | Link | ID |", "|---|---|---|---|"]
        for s in items:
            note = f" ({s['note']})" if s.get("note") else ""
            out.append(f"| {s.get('name', s['id'])}{note} | {s.get('kind', '')} | {s.get('url', '')} | `{s['id']}` |")
        return out

    on = [s for s in resolved["sources"] if s.get("enabled", True)]
    yours = [s for s in on if s["id"].startswith("local:")]
    curated = [s for s in on if not s["id"].startswith("local:")]
    muted = [s for s in resolved["sources"] if not s.get("enabled", True)]
    catalog_label = "Curated" if resolved.get("include_curated", True) else "Selected from catalog"
    lines = ["# Sources", "",
             "This is what a brief reads. The file is rewritten whenever sources change, so don't edit it by hand:",
             "ask your agent to add, mute or suggest a source (`/farfield:sources`), or edit `sources.local.json`.",
             "", f"## {catalog_label} ({len(curated)}) · list `{resolved['pack']}` {resolved['version']}", ""]
    lines += rows(curated) if curated else ["None."]
    lines += ["", f"## Yours ({len(yours)})", ""]
    lines += rows(yours) if yours else ["None yet. Example: `/farfield:sources add <name or URL>`."]
    lines += ["", f"## Muted ({len(muted)})", ""]
    lines += rows(muted) if muted else ["None."]
    return "\n".join(lines) + "\n"


def write_sources_md(root):
    root = Path(root).expanduser()
    text = render_sources(resolve_sources(read_json(CATALOG), load_local(root)))
    (root / "sources.md").write_text(text)
    return text


def add_source(root, url, name, kind="feed"):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("source URL must be http(s)")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    local = load_local(root)
    known = resolve_sources(read_json(CATALOG), local)["sources"]
    for source in known:
        if source.get("url", "").rstrip("/") == url.rstrip("/"):
            raise ValueError(f"already listed as {source['id']}; unmute it instead of adding a duplicate")
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or parsed.netloc
    ident, n = f"local:{slug}", 2
    while any(s["id"] == ident for s in known):
        ident, n = f"local:{slug}-{n}", n + 1
    local["add"].append({"id": ident, "name": name, "url": url, "kind": kind, "enabled": True,
                         "added": date.today().isoformat()})
    save_local(root, local)
    return ident


def set_enabled(root, ident, enabled):
    local = load_local(root)
    known = {s["id"] for s in resolve_sources(read_json(CATALOG), local)["sources"]}
    if ident not in known and ident not in local["overrides"]:
        raise ValueError(f"no source with ID {ident}; IDs are in the last column of sources.md")
    for source in local["add"]:
        if source["id"] == ident:
            source["enabled"] = enabled
            break
    else:
        local["overrides"].setdefault(ident, {})["enabled"] = enabled
    save_local(root, local)


def version(check=False):
    meta = read_json(SKILL / "skill.json")
    out = {"version": meta["version"], "latest": None, "update_available": False}
    if check and meta.get("version_url"):
        try:
            with urllib.request.urlopen(meta["version_url"], timeout=10) as response:
                latest = json.loads(response.read(65536))["version"]
            out["latest"] = latest
            out["update_available"] = tuple(map(int, latest.split("."))) > tuple(map(int, meta["version"].split(".")))
        except Exception as error:  # an update check must never fail a brief
            out["error"] = str(error)[:200]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init").add_argument("workspace")
    commands.add_parser("where")
    commands.add_parser("check").add_argument("pack")
    sources = commands.add_parser("sources")
    sources.add_argument("workspace")
    sources.add_argument("--json", action="store_true")
    mode = commands.add_parser("source-mode")
    mode.add_argument("workspace")
    mode.add_argument("mode", choices=("only-mine", "curated"))
    add = commands.add_parser("add")
    add.add_argument("workspace")
    add.add_argument("url")
    add.add_argument("--name", required=True)
    add.add_argument("--kind", default="feed", choices=KINDS)
    for name in ("mute", "unmute"):
        sub = commands.add_parser(name)
        sub.add_argument("workspace")
        sub.add_argument("id")
    commands.add_parser("version").add_argument("--check", action="store_true")
    commands.add_parser("keys").add_argument("--open", action="store_true")
    for name, arg in (("fetch", "url"), ("search", "query")):
        sub = commands.add_parser(name)
        sub.add_argument("workspace")
        sub.add_argument(arg)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            print(f"Workspace ready: {init_workspace(args.workspace)}")
        elif args.command == "where":
            root = where()
            if root is None:
                print("No workspace yet. Run start.", file=sys.stderr)
                return 3
            print(root)
        elif args.command == "check":
            warnings = check_evidence(read_json(args.pack))
            print("PASS: basic evidence structure (not factual verification)")
            for warning in warnings:
                print(f"WARNING: {warning}")
        elif args.command == "sources":
            if args.json:
                print(json.dumps(resolve_sources(read_json(CATALOG), load_local(args.workspace)), indent=2))
            else:
                print(write_sources_md(args.workspace), end="")
        elif args.command == "source-mode":
            set_source_mode(args.workspace, args.mode)
            print(f"Source mode: {args.mode}")
        elif args.command == "add":
            print(f"Added {add_source(args.workspace, args.url, args.name, args.kind)}")
        elif args.command in ("mute", "unmute"):
            set_enabled(args.workspace, args.id, args.command == "unmute")
            print(f"{args.command}d {args.id}")
        elif args.command == "keys":
            if args.open:
                print(f"Opened {open_keys()} in your editor. Paste the key after the =, save, close.")
            print(json.dumps({name: name in keys() for name in KEYS}))
        elif args.command == "fetch":
            print(json.dumps(fetch(args.workspace, args.url)))
        elif args.command == "search":
            found = exa("/search", {"query": args.query, "numResults": 10}).get("results") or []
            print(json.dumps([{"title": r.get("title"), "url": r.get("url"), "date": (r.get("publishedDate") or "")[:10]}
                              for r in found], indent=1))
        else:
            print(json.dumps(version(args.check)))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, urllib.error.URLError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
