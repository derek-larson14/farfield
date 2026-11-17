#!/usr/bin/env python3
"""Write SOURCES.md, the human-readable reading list, from skills/farfield/catalog.json.

  tools/sources_md.py          rewrite SOURCES.md
  tools/sources_md.py --check  exit 1 if SOURCES.md is out of date (used by the tests)
  tools/sources_md.py --html PATH   also write the web page the site serves at /sources

The catalog is what the agent reads. SOURCES.md is for people, so it shows each source's homepage and why it is
on the list, grouped by section, and leaves feed URLs and retrieval notes in the catalog.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "skills" / "farfield" / "catalog.json"
OUT = REPO / "SOURCES.md"

SECTIONS = [  # (title, test on a source), first match wins
    ("Podcasts", lambda s: s.get("kind") == "podcast"),
    ("Papers", lambda s: s["id"] in ("arxiv", "hfpapers")),
    ("Builders and engineering", lambda s: {"engineering", "applied-ai"} & set(s.get("topics", []))),
    ("Research", lambda s: "research" in s.get("topics", [])),
    ("Evaluation and adoption", lambda s: "evaluation-and-adoption" in s.get("topics", [])),
    ("Business and strategy", lambda s: "business" in s.get("topics", [])),
    ("Outside AI", lambda s: "adjacent-fields" in s.get("topics", [])),
]

INTRO = """# Farfield sources

The default sources. During setup, and any time after, you can add your own or mute any of these. [Suggest a source](https://github.com/derek-larson14/farfield/issues/new?template=source.yml)
"""

OUTRO = """
## Not on the list yet

Worth trying, not switched on:

- [smol.ai AI News](https://news.smol.ai/): broad AI and developer chatter; good for finding originals. Overlaps Latent Space.
- [Last Week in AI](https://lastweekin.ai/): weekly roundup, useful for discovery.
- [The Batch](https://www.deeplearning.ai/the-batch): an editor's weekly shortlist across applied AI and research.
- [SemiAnalysis](https://newsletter.semianalysis.com/): compute and chips; mostly paywalled.
- [Learning the Machine](https://davisblalock.substack.com/): selective technical reading; check how often it still publishes.
- TWiML, Software Engineering Daily and The Data Exchange: podcasts with patchier transcripts.

Every machine-readable detail (feed URLs, how each is read, access limits) is in [catalog.json](skills/farfield/catalog.json).
"""


SHOWN = ["Builders and engineering", "Research", "Evaluation and adoption", "Business and strategy", "Outside AI",
         "Papers", "Podcasts"]


def grouped(catalog):
    groups = {title: [] for title in SHOWN}
    for source in catalog["sources"]:
        title = next((t for t, test in SECTIONS if test(source)), "Research")
        groups[title].append(source)
    return [(title, sources) for title, sources in groups.items() if sources]


def render(catalog):
    lines = [INTRO.format(n=len(catalog["sources"]))]
    for title, sources in grouped(catalog):
        lines += [f"## {title}", ""]
        lines += [f"- **[{s['name']}]({s['home']})**: {s['why']}" for s in sources]
        lines.append("")
    return "\n".join(lines) + OUTRO


SUGGEST = "https://github.com/derek-larson14/farfield/issues/new?template=source.yml"


def render_html(catalog):
    from html import escape
    sections = []
    for title, sources in grouped(catalog):
        items = "".join(f'<li><a href="{escape(s["home"])}">{escape(s["name"])}</a> <span>{escape(s["why"])}</span></li>'
                        for s in sources)
        sections.append(f"<h2>{escape(title)}</h2><ul>{items}</ul>")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Farfield sources</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="The {len(catalog['sources'])} sources Farfield starts from. What are we missing?">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap">
<style>
:root{{color-scheme:light;--paper:#fcfaf5;--ink:#1b1a18;--muted:#7d7a71;--line:#e4e0d6;--glow:#d9641f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:18px/1.55 Newsreader,Georgia,serif;-webkit-font-smoothing:antialiased}}
main{{max-width:680px;margin:0 auto;padding:56px 16px 72px}}
.top{{font:12.5px/1.4 "IBM Plex Mono",ui-monospace,Menlo,monospace;color:var(--muted);text-decoration:none}}
.top:hover{{color:var(--ink)}}
h1{{font-size:clamp(32px,6vw,42px);font-weight:400;letter-spacing:-.7px;line-height:1.15;margin:24px 0 10px}}
.lede{{color:#3d3b36;margin:0 0 6px}}
.suggest{{color:var(--glow);text-underline-offset:3px}}
h2{{font-size:24px;font-weight:500;letter-spacing:-.3px;margin:34px 0 2px}}
ul{{list-style:none;margin:0;padding:0}}
li{{padding:6px 0;border-top:1px solid var(--line);line-height:1.4}}
li:first-child{{border-top:0}}
li a{{color:var(--ink);font-weight:500;text-decoration-color:var(--line);text-underline-offset:3px}}
li a:hover{{text-decoration-color:var(--glow)}}
li span{{display:block;color:#55524b;font-size:16px;margin-top:1px}}
</style></head>
<body><main>
<a class="top" href="/">← Farfield</a>
<h1>Farfield sources</h1>
<p class="lede">The default sources. During setup, and any time after, you can add your own or mute any of these. <a class="suggest" href="{SUGGEST}" target="_blank" rel="noopener">Suggest a source</a></p>
{''.join(sections)}
</main></body></html>
"""


def main():
    catalog = json.loads(CATALOG.read_text())
    text = render(catalog)
    if "--html" in sys.argv:
        Path(sys.argv[sys.argv.index("--html") + 1]).write_text(render_html(catalog))
    if "--check" in sys.argv:
        if OUT.read_text() != text:
            print("SOURCES.md is out of date; run tools/sources_md.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
