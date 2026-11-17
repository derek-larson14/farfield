#!/usr/bin/env python3
"""Local reading history. JSONL is authoritative; reading-history.md is its view."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

STATUSES = ('discovered', 'read', 'shown', 'failed', 'skipped')

def canonical(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('use a public http(s) article URL')
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in ('fbclid', 'gclid')]
    if any(k.lower() in ('token', 'key', 'api_key', 'signature', 'auth') for k, v in query):
        raise ValueError('record the public article URL, not a private feed or signed URL')
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', urlencode(query), ''))

def events(root):
    path = Path(root) / 'state' / 'reading-history.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []

def lookup(root, url, revision=None):
    url = canonical(url)
    found = [x for x in events(root) if x['url'] == url]
    read = [x for x in found if x['status'] in ('read', 'shown')]
    last = read[-1] if read else None
    same = bool(last and (revision is None or last.get('revision') == revision))
    raw = last.get('raw') if last else None
    return {'url': url, 'already_read': same, 'last_read': last,
            'cached_raw': raw if same and raw and Path(raw).is_file() else None,
            'previously_shown': any(x['status'] == 'shown' for x in found)}

def record(root, url, source, title, status, revision=None, raw=None, note='', brief=None):
    if status not in STATUSES:
        raise ValueError('unknown reading status')
    url = canonical(url)
    if raw and not Path(raw).expanduser().is_file():
        raise ValueError('raw evidence file does not exist')
    item = {'id': hashlib.sha256(url.encode()).hexdigest()[:16], 'url': url,
            'source_id': source, 'title': title, 'status': status,
            'at': datetime.now(timezone.utc).isoformat(), 'revision': revision,
            'raw': str(Path(raw).expanduser().resolve()) if raw else None,
            'note': note, 'brief': brief}
    folder = Path(root) / 'state'; folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'reading-history.jsonl').open('a') as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + '\n')
    render(root)
    return item

def render(root):
    latest = {}
    for x in events(root): latest[x['url']] = x
    lines = ['# Reading history', '', 'Generated from state/reading-history.jsonl. Sources are publications; these are individual items.', '',
             '| Last checked | Item | Status | Note |', '|---|---|---|---|']
    def clean(value): return str(value or '').replace('|', '\\|').replace('\n', ' ').replace('[', '(').replace(']', ')')
    for x in reversed(list(latest.values())):
        lines.append(f"| {x['at'][:10]} | [{clean(x['title'])}]({x['url']}) | {x['status']} | {clean(x['note'])} |")
    path = Path(root) / 'reading-history.md'; path.write_text('\n'.join(lines) + '\n')
    return str(path)

def main():
    p = argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    for command in ('lookup','record'):
        a=sub.add_parser(command); a.add_argument('workspace'); a.add_argument('url'); a.add_argument('--revision')
        if command=='record':
            a.add_argument('--source',required=True); a.add_argument('--title',required=True); a.add_argument('--status',choices=STATUSES,required=True)
            a.add_argument('--raw'); a.add_argument('--note',default=''); a.add_argument('--brief')
    a=sub.add_parser('render'); a.add_argument('workspace')
    args=vars(p.parse_args()); command=args.pop('command'); root=args.pop('workspace')
    try: print(json.dumps(globals()[command](root,**args),ensure_ascii=False))
    except (ValueError,OSError,json.JSONDecodeError) as error: p.exit(1,str(error)+'\n')
if __name__=='__main__': main()
