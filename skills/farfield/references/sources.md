# Sources: see, add, mute, suggest

`sources.md` in the workspace is the readable list: curated sources, the user's own, and muted ones, each with a link and an ID. It is rewritten from `catalog.json` (ships with the skill) plus `sources.local.json` (the user's changes). The user's changes survive every update of the curated list.

## See

`HELPER sources <workspace>` rewrites and prints the list. Show it as is and link the file. If asked "why did the brief say X", open `evidence/<date>.json`: it has the quote, link and date behind each finding.

## Add (for this user only)

1. Resolve the name or URL to the thing you can actually fetch: an RSS/Atom feed, a podcast feed, a YouTube channel, a site, or a standing search. Fetch it once to prove it works and show one recent item with its date. If the name is ambiguous, ask which one. Never invent a feed URL.
2. `HELPER add <workspace> <url> --name "<name>" --kind feed|podcast|channel|site|search`. If it reports the source is already listed, unmute that ID instead.
3. Say plainly what the next brief can use from it: full text, show notes only, or transcript if one is published. No audio transcription and no paid access happen on their own.

Other regular inputs work too: a standing search they want re-run each time (`--kind search`, with the search URL), or one person's blog. A local folder they drop papers into is context, not a source: list it under "Read for context" in `me.md`.

## Mute / unmute

"Only my own" uses `HELPER source-mode <workspace> only-mine` before adding or unmuting the requested sources. New catalog entries then stay off unless explicitly selected. To include curated defaults again, use `HELPER source-mode <workspace> curated`; individual overrides are preserved. Setting `only-mine` again clears previous catalog selections, so do it only when the user asks to reset their selection, not during a brief.

`HELPER mute <workspace> <id>` or `unmute`. IDs are the last column of `sources.md`. A muted source is not read at all, and a finding that depended on it is dropped rather than shown without its citation.

## Suggest (for everyone)

Adding for yourself and suggesting for the shared list are separate. After an add, ask once: "Want to suggest this for the curated list too?" No is a complete answer.

On yes, write three things and show them: the name or URL, one example item, and one sentence on what it adds that the list lacks. Leave out the user's projects and file paths. Ask if they want a reply and at which email (optional). After they say send, post it to `suggestions.url` from the workspace's `feed.json`:

```sh
curl -fsS -X POST "<suggestions.url>" -H 'Content-Type: application/json' \
  -d '{"url":"...","why":"...","email":"","via":"skill"}'
```

If `suggestions.url` is empty or the post fails, give them the draft text and explain that delivery is unavailable; don't invent a form link or claim it was sent. A pull request adding the source to `catalog.json` is the other route (see CONTRIBUTING.md in the repository).

## Unattended

Never add, mute or suggest during a scheduled run.
