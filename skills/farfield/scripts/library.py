#!/usr/bin/env python3
"""Local reading history. The JSONL file is authoritative; reading-history.md is a readable view of it.

  library.py lookup <workspace> <url> [--revision R]     was this item already read (and is its text cached)?
  library.py record <workspace> <url> --source ID --title T --status S [--note N] [--revision R] [--raw PATH] [--brief PATH]
  library.py render <workspace>                          rewrite reading-history.md
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

STATUSES = ("discovered", "read", "shown", "failed", "skipped")
TRACKING = ("fbclid", "gclid", "ref", "ref_src", "mc_cid", "mc_eid")
SECRETS = ("token", "key", "api_key", "signature", "auth", "access_token")


def canonical(url):
    """One spelling per article: no tracking parameters, no www., no trailing slash, no fragment."""
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError("use a public http(s) article URL")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING]
    if any(k.lower() in SECRETS for k, _ in query):
        raise ValueError("record the public article URL, not a private feed or signed URL")
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, host, path, urlencode(sorted(query)), ""))


def events(root):
    path = Path(root).expanduser() / "state" / "reading-history.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def same_item(event_url, url):
    # Events written before canonical() dropped www. and trailing slashes still match.
    try:
        return canonical(event_url) == url
    except ValueError:
        return False


def lookup(root, url, revision=None):
    url = canonical(url)
    found = [e for e in events(root) if same_item(e["url"], url)]
    reads = [e for e in found if e["status"] in ("read", "shown")]
    last = reads[-1] if reads else None
    unchanged = bool(last and (revision is None or last.get("revision") == revision))
    raw = last.get("raw") if last else None
    return {"url": url, "already_read": unchanged, "last_read": last,
            "cached_raw": raw if unchanged and raw and Path(raw).is_file() else None,
            "previously_shown": any(e["status"] == "shown" for e in found)}


def record(root, url, source, title, status, revision=None, raw=None, note="", brief=None):
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    url = canonical(url)
    root = Path(root).expanduser()
    if raw:
        raw_path = Path(raw).expanduser()
        if not raw_path.is_absolute():
            raw_path = root / raw_path   # paths relative to the workspace are fine
        if not raw_path.is_file():
            raise ValueError(f"raw evidence file does not exist: {raw}")
        raw = str(raw_path.resolve())
    item = {"id": hashlib.sha256(url.encode()).hexdigest()[:16], "url": url, "source_id": source,
            "title": title, "status": status, "at": datetime.now(timezone.utc).isoformat(),
            "revision": revision, "raw": raw, "note": note, "brief": brief}
    folder = root / "state"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "reading-history.jsonl").open("a") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    render(root)
    return item


def render(root):
    root = Path(root).expanduser()
    latest = {}
    for event in events(root):
        try:
            latest[canonical(event["url"])] = event
        except ValueError:
            continue

    def clean(value):
        return str(value or "").replace("|", "\\|").replace("\n", " ").replace("[", "(").replace("]", ")")

    lines = ["# Reading history", "",
             "Generated from state/reading-history.jsonl. Sources are publications; these are individual items.", "",
             "| Last checked | Item | Status | Note |", "|---|---|---|---|"]
    for event in reversed(list(latest.values())):
        lines.append(f"| {event['at'][:10]} | [{clean(event['title'])}]({event['url']}) | {event['status']} | "
                     f"{clean(event['note'])} |")
    path = root / "reading-history.md"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("lookup", "record"):
        sub = commands.add_parser(name)
        sub.add_argument("workspace")
        sub.add_argument("url")
        sub.add_argument("--revision")
        if name == "record":
            sub.add_argument("--source", required=True)
            sub.add_argument("--title", required=True)
            sub.add_argument("--status", choices=STATUSES, required=True)
            sub.add_argument("--raw")
            sub.add_argument("--note", default="")
            sub.add_argument("--brief")
    commands.add_parser("render").add_argument("workspace")
    args = vars(parser.parse_args(argv))
    command, root = args.pop("command"), args.pop("workspace")
    try:
        out = {"lookup": lookup, "record": record, "render": render}[command](root, **args)
        print(json.dumps(out, ensure_ascii=False))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"FAILED: {error}", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
