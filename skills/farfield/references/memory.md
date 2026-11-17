# Reading memory

Store a readable history, not a growing dump of every source page. `LIBRARY` means `<skill>/scripts/library.py`, run directly like the other helpers (see SKILL.md).

- `reading-history.md`: generated list for the user, with links, status, date and a short reason.
- `state/reading-history.jsonl`: append-only item events for reliable lookup. One publication can have many items. The publication list stays in `sources.md`.
- `state/reading/<date>.json`: discovery coverage and pagination gaps, as described in reading.md.
- `evidence/raw/`: text actually read or transcribed; cached to avoid repeated work and verify quotes. Do not save podcast audio after transcription. Never copy full source text into the public repo.
- `state/seen.json`: compact finding history to avoid repeating an idea under a new URL.
- `state/watch.md`: at most 20 promising ideas waiting on something concrete. For each: original links, named question, date, and what new evidence would justify revisiting. No old brief prose or generic trends.

Before fetching an item: `LIBRARY lookup <workspace> <canonical-article-url> [--revision <publisher-update-date-or-version>]`. Already read and unchanged means reuse cached text or skip. `cached_raw: null` means the file is gone, not that reading failed; refetch only if needed for a new finding or quote check. A revised paper or materially updated article can be read again. A URL alias must be resolved to the original first; tracking parameters alone do not make a new item.

Record discovery, successful full reading, failure or deliberate skipping separately:

`LIBRARY record <workspace> <url> --source <id> --title "<title>" --status discovered|read|failed|skipped --note "<short reason>" [--revision <version>] [--raw <path>]`

To record many items at once, write them as JSON lines (`{"url", "source", "title", "status", "note", "raw", "brief"}`) to a file in the workspace's `state/` folder with the host's file tool, then run `LIBRARY record-batch <workspace> <that file>`. Don't write shell loops or scripts.

Only `read` and `shown` count as successfully consumed. Never mark an abstract or show notes as a fully read paper/interview; record the limited access in the note and keep status discovered until the original is read. When used in a brief, record `shown` with `--brief <path>` and preserve `--revision`/`--raw` from its read event. A later failed check does not erase a successful earlier read.

On each run, consider whether new evidence meets a watch item's revisit trigger. If it does, explain what changed; do not recycle the earlier finding. Remove obsolete watch items and honor “already knew” feedback. Old items can be useful background without being presented as news.

Keep metadata until the user clears it. Raw text may be deleted to reclaim space without forgetting what was read; keep excerpts supporting saved briefs unless the user asks to remove them. All of this lives in the user's workspace and survives skill updates. No shared database is needed.
