#!/usr/bin/env python3
"""Write SOURCES.md, the human-readable reading list, from skills/farfield/catalog.json.

  tools/sources_md.py          rewrite SOURCES.md
  tools/sources_md.py --check  exit 1 if SOURCES.md is out of date (used by the tests)

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


def render(catalog):
    shown = ["Builders and engineering", "Research", "Evaluation and adoption", "Business and strategy", "Outside AI",
             "Papers", "Podcasts"]
    groups = {title: [] for title in shown}
    for source in catalog["sources"]:
        title = next((t for t, test in SECTIONS if test(source)), "Research")
        groups[title].append(source)
    lines = [INTRO.format(n=len(catalog["sources"]))]
    for title, sources in groups.items():
        if not sources:
            continue
        lines += [f"## {title}", ""]
        lines += [f"- **[{s['name']}]({s['home']})**: {s['why']}" for s in sources]
        lines.append("")
    return "\n".join(lines) + OUTRO


def main():
    text = render(json.loads(CATALOG.read_text()))
    if "--check" in sys.argv:
        if OUT.read_text() != text:
            print("SOURCES.md is out of date; run tools/sources_md.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
