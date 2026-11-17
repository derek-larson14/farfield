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

INTRO = """# Reading list

Farfield starts from these {n} sources. During setup you can keep them, add your own, mute any of them, or use only your own. Each brief reads the last few weeks of whichever are on, then keeps only what bears on your work.

Paywalled posts are skipped. Podcasts are read from their published transcripts; audio is transcribed only if you turn that on.

Think something is missing? [Suggest a source](https://github.com/derek-larson14/farfield/issues/new?template=source.yml).
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
<title>Farfield reading list</title>
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
h1{{font-size:clamp(32px,6vw,42px);font-weight:400;letter-spacing:-.7px;line-height:1.15;margin:28px 0 14px}}
.lede{{color:#3d3b36;margin:0 0 10px}}
.ask{{margin:28px 0 8px;padding:16px 18px;border-left:2px solid var(--glow);background:#fff8}}
.ask a{{color:var(--glow)}}
h2{{font-size:13px;font-weight:400;font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:40px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
ul{{list-style:none;margin:0;padding:0}}
li{{padding:9px 0}}
li a{{color:var(--ink);font-weight:500;text-decoration-color:var(--line);text-underline-offset:3px}}
li a:hover{{text-decoration-color:var(--glow)}}
li span{{display:block;color:#55524b;font-size:16.5px}}
footer{{margin-top:48px;font:12.5px/1.6 "IBM Plex Mono",ui-monospace,Menlo,monospace;color:var(--muted)}}
</style></head>
<body><main>
<a class="top" href="/">← Farfield</a>
<h1>What Farfield reads</h1>
<p class="lede">These {len(catalog['sources'])} sources are the starting list. Each brief reads the last few weeks of them, keeps only what bears on the reader's work, and links back to the originals. Everyone can add their own or mute any of these.</p>
<p class="lede">Paywalled posts are skipped. Podcasts are read from their published transcripts.</p>
<div class="ask"><strong>What are we missing?</strong> The best additions are people doing the work and writing about it firsthand, independent evaluations, and anything outside AI that explains how technology actually spreads. <a href="{SUGGEST}">Suggest a source</a>, or just tell whoever sent you this link.</div>
{''.join(sections)}
<footer>Generated from the catalog Farfield installs with, so this page is always the real list.</footer>
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
