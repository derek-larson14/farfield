#!/usr/bin/env python3
"""Workspace helper. Local setup; fetch/search/version checks use the network. No model calls.

  radar.py init <workspace>            create the folder, remember where it is
  radar.py where                       print the remembered workspace (exit 3 if none)
  radar.py sources <workspace>         rewrite sources.md (the readable list) and print it
  radar.py source-mode <workspace> only-mine|curated   choose whether future curated defaults are enabled
  radar.py add <workspace> <url> --name NAME [--kind feed|podcast|channel|site|search]
  radar.py mute|unmute <workspace> <source-id>
  radar.py items <workspace> [--since YYYY-MM-DD] [--source ID ...]
                                       list dated items from every enabled RSS/Atom source, in parallel,
                                       with per-source coverage; saves state/reading/items-<date>.json
  radar.py fetch <workspace> <url>     save a page's raw text under evidence/raw/ and print the file path
  radar.py search <workspace> <query>  Exa search (only if EXA_API_KEY is in the keys file)
  radar.py check <pack.json>           structural and exact-quote checks, one verdict per quote; quotes
                                       with a "raw" file are checked against the page text itself
  radar.py keys [--open]               which optional keys are set (names only); --open edits the file
  radar.py version [--check]           bundled version; --check compares with the published one
"""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
CATALOG = SKILL / "catalog.json"
CONFIG = Path(os.environ.get("FARFIELD_CONFIG", Path.home() / ".config" / "farfield"))
POINTER = CONFIG / "workspace"
KEYFILE = CONFIG / "env"
KEYS = {"EXA_API_KEY": "optional: better search and page text (exa.ai)",
        "OPENROUTER_API_KEY": "optional: X search and cloud transcription, each separately enabled (openrouter.ai)"}
UA = "Mozilla/5.0 (compatible; farfield; personal research reader)"
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
    for name in ("briefs", "evidence", "state"):
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


QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
                        "\u00a0": " ", "\u2026": "..."})


def squash(text):
    """Compare quotes and pages on words, not on curly quotes, dashes, line breaks, or the space that
    stripping a tag leaves before punctuation ("failure mode ." from "failure <a>mode</a>.")."""
    text = " ".join(unicodedata.normalize("NFKC", text).translate(QUOTES).split())
    text = re.sub(r" ([.,;:!?)\]'\"])", r"\1", text)
    return re.sub(r"([(\[]) ", r"\1", text)


def to_text(body):
    body = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return squash(html.unescape(body))


def download(url, data=None, headers=None, limit=MAX_PAGE):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=25) as response:
        return (response.headers.get("Content-Type") or "").lower(), response.read(limit)


def http(url, data=None, headers=None, limit=MAX_PAGE):
    return download(url, data, headers, limit)[1].decode("utf-8", "replace")


PDF_JXA = """ObjC.import('PDFKit');
function run(argv) {
  const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  return (!doc || doc.isNil()) ? '' : ObjC.unwrap(doc.string);
}"""


def pdf_text(body):
    """Text of a PDF with no Python packages: pdftotext if installed, else macOS's own PDFKit."""
    with tempfile.TemporaryDirectory(prefix="farfield-pdf-") as tmp:
        path = Path(tmp) / "doc.pdf"
        path.write_bytes(body)
        if shutil.which("pdftotext"):
            commands = [["pdftotext", "-enc", "UTF-8", str(path), "-"]]
        elif sys.platform == "darwin" and shutil.which("osascript"):
            script = Path(tmp) / "pdf.js"
            script.write_text(PDF_JXA)
            commands = [["osascript", "-l", "JavaScript", str(script), str(path)]]
        else:
            raise ValueError("this is a PDF and no PDF reader is available (install poppler's pdftotext)")
        for command in commands:
            done = subprocess.run(command, capture_output=True, timeout=120)
            text = done.stdout.decode("utf-8", "replace")
            if done.returncode == 0 and text.strip():
                # Rejoin words hyphenated across line breaks: "evalu-\nation" -> "evaluation".
                return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    raise ValueError("this PDF has no extractable text (it may be scanned images)")


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
        kind, body = download(url, limit=32 * 1024 * 1024)
        if "pdf" in kind or body[:5] == b"%PDF-":
            text, via = squash(pdf_text(body)), "pdf"
        elif kind and not any(t in kind for t in ("text", "html", "xml", "json")):
            raise ValueError(f"{url} is {kind.split(';')[0]}, not a text page")
        else:
            text = to_text(body.decode("utf-8", "replace"))
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
    # Wrapped so file viewers show all of it; quote checks ignore line breaks.
    path.write_text(f"{url}\n" + "\n".join(textwrap.wrap(text, 160, break_long_words=False, break_on_hyphens=False)) + "\n")
    return {"raw": str(path), "chars": len(text), "via": via}


def check_evidence(pack):
    """Structural and quote-substring checks, not truth or origin verification.

    The pack's shape must be right (raises ValueError otherwise). Each quote then gets its own verdict,
    so one bad quote is dropped without throwing away the rest. Returns (warnings, failures)."""
    if not isinstance(pack, dict):
        raise ValueError("pack must be an object")
    date.fromisoformat(pack["as_of"])
    ideas = pack["ideas"]
    if not isinstance(ideas, list):
        raise ValueError("ideas must be a list")
    warnings, failures = [], []
    ids = set()
    for idea in ideas:
        ident = idea["id"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("idea IDs must be nonempty unique strings")
        ids.add(ident)
        if not idea.get("quotes"):
            raise ValueError(f"{ident}: no quotes")
        for n, quote in enumerate(idea["quotes"], 1):
            where = f"{ident} quote {n}"
            text = quote.get("quote")
            if not isinstance(text, str) or not text.strip():
                failures.append(f"{where}: empty quote")
                continue
            url = urlparse(quote.get("url") or "")
            if url.scheme not in ("http", "https") or not url.netloc:
                failures.append(f"{where}: invalid source URL")
                continue
            if quote.get("date"):
                try:
                    date.fromisoformat(quote["date"][:10])
                except ValueError:
                    failures.append(f"{where}: date is not YYYY-MM-DD")
                    continue
            else:
                warnings.append(f"{where}: unknown publication date")
            excerpt = quote.get("excerpt")
            if excerpt is None:
                warnings.append(f"{where}: no source excerpt")
            elif not isinstance(excerpt, str) or squash(text) not in squash(excerpt):
                failures.append(f"{where}: quote is not verbatim in its excerpt")
                continue
            raw = quote.get("raw")
            if raw:
                path = Path(raw).expanduser()
                if not path.is_file():
                    failures.append(f"{where}: raw file {raw} does not exist")
                elif squash(text) not in squash(path.read_text(errors="replace")):
                    failures.append(f"{where}: quote is not in the fetched page ({raw})")
            else:
                warnings.append(f"{where}: not checked against the page itself (no raw file); "
                                "the brief must mark it \"not checked against the page\"")
            if not quote.get("origin_id"):
                warnings.append(f"{where}: no origin_id; independence unverified")
    if pack.get("sample"):
        warnings.append("SAMPLE: demonstration only, not current evidence")
    return sorted(set(warnings)), failures


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
    """The workspace's readable list: what is on, grouped, each with its homepage, reason and ID."""
    def line(s):
        link = s.get("home") or s.get("url", "")
        why = f": {s['why']}" if s.get("why") else ""
        note = f" ({s['note']})" if s.get("note") else ""
        return f"- [{s.get('name', s['id'])}]({link}){why}{note} `{s['id']}`"

    def grouped(items):
        out = []
        for label, test in (("Writing", lambda s: s.get("kind") not in ("podcast", "search") and s["id"] != "hfpapers"),
                            ("Papers", lambda s: s.get("kind") == "search" or s["id"] == "hfpapers"),
                            ("Podcasts", lambda s: s.get("kind") == "podcast")):
            chosen = [s for s in items if test(s)]
            if chosen:
                out += [f"**{label}**", ""] + [line(s) for s in chosen] + [""]
        return out or ["None.", ""]

    on = [s for s in resolved["sources"] if s.get("enabled", True)]
    yours = [s for s in on if s["id"].startswith("local:")]
    curated = [s for s in on if not s["id"].startswith("local:")]
    muted = [s for s in resolved["sources"] if not s.get("enabled", True)]
    catalog_label = "From the curated list" if resolved.get("include_curated", True) else "Picked from the curated list"
    lines = ["# Sources", "",
             f"A brief reads these {len(on)} sources. To change them, ask your agent (`/farfield:sources` in Claude Code,",
             "`$farfield sources` in Codex): add, mute or suggest one. This file is rewritten when sources change.", "",
             f"## {catalog_label} ({len(curated)})", ""]
    lines += grouped(curated)
    lines += [f"## Yours ({len(yours)})", ""]
    lines += [line(s) for s in yours] + [""] if yours else ["None yet. Ask to add a blog, newsletter, podcast or search.", ""]
    lines += [f"## Muted ({len(muted)})", ""]
    lines += [line(s) for s in muted] if muted else ["None."]
    lines += ["", f"Curated list `{resolved['pack']}` version {resolved['version']}. The ID after each source is what "
              "mute and unmute use."]
    return "\n".join(lines) + "\n"


def write_sources_md(root):
    root = Path(root).expanduser()
    text = render_sources(resolve_sources(read_json(CATALOG), load_local(root)))
    (root / "sources.md").write_text(text)
    return text


def site(url):
    """Host without www, for spotting the same publication under a different URL."""
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_url(a, b):
    def norm(u):
        p = urlparse(u)
        return site(u), p.path.rstrip("/"), p.query
    return norm(a) == norm(b)


def add_source(root, url, name, kind="feed", force=False):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("source URL must be http(s)")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    local = load_local(root)
    known = resolve_sources(read_json(CATALOG), local)["sources"]
    for source in known:
        if same_url(source.get("url", ""), url):
            raise ValueError(f"already listed as {source['id']}; unmute it instead of adding a duplicate")
    if not force:
        for source in known:
            if source.get("url") and site(source["url"]) == site(url):
                raise ValueError(f"{site(url)} is already listed as {source['id']} ({source['url']}). "
                                 "If that is the same publication, unmute it instead; if this is a different "
                                 "feed on the same site, run add again with --force")
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


FEED_DISCOVERY = (None, "rss-or-atom")
ATOM = "{http://www.w3.org/2005/Atom}"
PODCAST_NS = "{https://podcastindex.org/namespace/1.0}"


def when(value):
    if not value:
        return None
    value = value.strip()
    try:
        moment = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def parse_feed(body):
    """(title, link, published datetime or None, has_transcript, has_audio) for each RSS item or Atom entry."""
    body = re.sub(r"^\s*<\?xml[^>]*\?>", "", body.lstrip("\ufeff"))
    try:
        tree = ET.fromstring(body)
    except ET.ParseError:
        # Feeds bigger than the download cap are cut mid-item. Items are newest first, so keep the whole ones.
        for close, tail in (("</item>", "</channel></rss>"), ("</entry>", "</feed>")):
            end = body.rfind(close)
            if end >= 0:
                tree = ET.fromstring(body[:end + len(close)] + tail)
                break
        else:
            raise
    out = []
    for item in tree.iter("item"):
        enclosure = item.find("enclosure")
        out.append({"title": (item.findtext("title") or "").strip(), "url": (item.findtext("link") or "").strip(),
                    "date": when(item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date")),
                    "transcript": item.find(PODCAST_NS + "transcript") is not None,
                    "audio": enclosure is not None and "audio" in (enclosure.get("type") or "audio")})
    for entry in tree.iter(ATOM + "entry"):
        link = next((l.get("href") for l in entry.findall(ATOM + "link") if l.get("rel", "alternate") == "alternate"), "")
        out.append({"title": (entry.findtext(ATOM + "title") or "").strip(), "url": link or "",
                    "date": when(entry.findtext(ATOM + "published") or entry.findtext(ATOM + "updated")),
                    "transcript": False, "audio": False})
    return out


def list_source(source, since):
    """One source's dated items in the window, and whether the feed reaches back to the window's start."""
    base = {"id": source["id"], "name": source.get("name"), "url": source.get("url")}
    if source.get("discovery") not in FEED_DISCOVERY or source.get("kind") == "search":
        return {**base, "status": "not-a-feed", "how": source.get("discovery") or source.get("kind"),
                "note": "discover through its archive or API as references/reading.md describes"}
    try:
        entries = parse_feed(http(source["url"], limit=16 * 1024 * 1024))
    except Exception as error:  # one broken feed must not stop the others
        return {**base, "status": "failed", "note": str(error)[:200]}
    dated = [e for e in entries if e["date"]]
    items = sorted((e for e in dated if e["date"] >= since), key=lambda e: e["date"], reverse=True)
    oldest = min((e["date"] for e in dated), default=None)
    if not entries:
        status, note = "failed", "feed parsed but has no items"
    elif oldest and oldest > since:
        status = "partial"
        note = (f"feed only goes back to {oldest.date().isoformat()}; check the site's dated archive for "
                f"{since.date().isoformat()} to {oldest.date().isoformat()}")
    else:
        status, note = "complete", "feed reaches back past the window start"
    undated = len(entries) - len(dated)
    if undated:
        note += f"; {undated} undated item(s) ignored"
    return {**base, "status": status, "note": note, "count": len(items),
            "items": [{"title": e["title"], "url": e["url"], "date": e["date"].date().isoformat(),
                       **({"transcript": True} if e["transcript"] else {}),
                       **({"audio": True} if e["audio"] and source.get("kind") == "podcast" else {})} for e in items]}


def list_items(root, since=None, only=()):
    root = Path(root).expanduser()
    since = since or (date.today() - timedelta(days=30))
    start = datetime(since.year, since.month, since.day, tzinfo=timezone.utc)
    sources = [s for s in resolve_sources(read_json(CATALOG), load_local(root))["sources"]
               if s.get("enabled", True) and (not only or s["id"] in only)]
    if only and len(sources) < len(set(only)):
        missing = sorted(set(only) - {s["id"] for s in sources})
        raise ValueError(f"not enabled or unknown: {', '.join(missing)}")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda s: list_source(s, start), sources))
    out = {"since": since.isoformat(), "until": date.today().isoformat(), "sources": results}
    folder = root / "state" / "reading"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"items-{date.today().isoformat()}.json"
    n = 2
    while path.exists():
        path, n = folder / f"items-{date.today().isoformat()}-{n}.json", n + 1
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    listing = path.with_suffix(".md")
    lines = [f"# Items since {out['since']}", ""]
    for r in results:
        lines.append(f"## {r['id']} ({r['status']}{', ' + str(r.get('count')) + ' items' if r.get('count') is not None else ''})")
        lines += [f"- {i['date']} [{i['title']}]({i['url']})" + (" (transcript)" if i.get("transcript") else "")
                  for i in r.get("items", [])]
        lines.append("")
    listing.write_text("\n".join(lines))
    summary = [{k: r.get(k) for k in ("id", "status", "count", "note")} for r in results]
    return {"saved": str(path), "list": str(listing), "since": out["since"], "sources": summary}


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
            out["update_available"] = None
            out["error"] = "could not check (not the same as up to date): " + str(error)[:200]
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
    add.add_argument("--force", action="store_true", help="add a second feed from a site already listed")
    items = commands.add_parser("items")
    items.add_argument("workspace")
    items.add_argument("--since", type=date.fromisoformat, help="YYYY-MM-DD; default 30 days ago")
    items.add_argument("--source", action="append", default=[], help="limit to this source ID (repeatable)")
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
            warnings, failures = check_evidence(read_json(args.pack))
            for failure in failures:
                print(f"DROP: {failure}")
            for warning in warnings:
                print(f"WARNING: {warning}")
            if failures:
                print(f"FAILED: {len(failures)} quote(s) must be removed from the pack and the brief, then run check again")
                return 1
            print("PASS: every quote is in its excerpt and page (structure only, not factual verification)")
        elif args.command == "sources":
            if args.json:
                print(json.dumps(resolve_sources(read_json(CATALOG), load_local(args.workspace)), indent=2))
            else:
                print(write_sources_md(args.workspace), end="")
        elif args.command == "source-mode":
            set_source_mode(args.workspace, args.mode)
            print(f"Source mode: {args.mode}")
        elif args.command == "add":
            print(f"Added {add_source(args.workspace, args.url, args.name, args.kind, args.force)}")
        elif args.command in ("mute", "unmute"):
            set_enabled(args.workspace, args.id, args.command == "unmute")
            print(f"{args.command}d {args.id}")
        elif args.command == "keys":
            if args.open:
                print(f"Opened {open_keys()} in your editor. Paste the key after the =, save, close.")
            print(json.dumps({name: name in keys() for name in KEYS}))
        elif args.command == "items":
            print(json.dumps(list_items(args.workspace, args.since, args.source), indent=1))
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
