# Sources: see, add, mute, suggest

`sources.md` in the workspace is the readable list: curated sources, the user's own, and muted ones, each with a link and an ID. It is rewritten from `catalog.json` (ships with the skill) plus `sources.local.json` (the user's changes). The user's changes survive every update of the curated list.

## See

`HELPER sources <workspace>` rewrites and prints the list. Show it as is and link the file. If asked "why did the brief say X", open `evidence/<date>.json`: it has the quote, link and date behind each finding.

## Add (for this user only)

1. Resolve the name or URL to the thing you can actually fetch: an RSS/Atom feed, a podcast feed, a YouTube channel, a site, or a standing search. Fetch it once to prove it works and show one recent item with its date. If the name is ambiguous, use the question picker to show the plausible matches with their URLs and allow a custom answer. Never invent a feed URL.
2. `HELPER add <workspace> <url> --name "<name>" --kind feed|podcast|channel|site|search`. If it says the URL or site is already listed, that publication is already a source: unmute that ID if it's muted, and tell the user it's included. Use `--force` only for a genuinely different feed on the same site.
3. Say plainly what the next brief can use from it: full text, show notes only, or transcript if one is published. No audio transcription and no paid access happen on their own.

Other regular inputs work too: a standing search they want re-run each time (`--kind search`, with the search URL), or one person's blog. A local folder they drop papers into is context, not a source: list it under "Read for context" in `me.md`.

## Mute / unmute

"Only my own" uses `HELPER source-mode <workspace> only-mine` before adding or unmuting the requested sources. New catalog entries then stay off unless explicitly selected. To include curated defaults again, use `HELPER source-mode <workspace> curated`; individual overrides are preserved. Setting `only-mine` again clears previous catalog selections, so do it only when the user asks to reset their selection, not during a brief.

`HELPER mute <workspace> <id>` or `unmute`. IDs are the last column of `sources.md`. A muted source is not read at all, and a finding that depended on it is dropped rather than shown without its citation.

## Suggest (for everyone)

Adding for yourself and suggesting for the shared list are separate. After a standalone add, offer **Draft a suggestion** and **Keep it private** in the picker once. Skip this offer during setup. If the user explicitly asks to suggest a source, go straight to the draft.

On yes, draft two things and show them: the source's link, and one sentence on what it adds that the list lacks. Leave out the user's projects, notes and file paths; the suggestion is public.

Then give them a pre-filled GitHub link that opens a "Suggest a source" issue. They review it and press Create, so nothing is sent without them seeing it. URL-encode each value:

```
https://github.com/derek-larson14/farfield/issues/new?template=source.yml&title=Source%3A%20<name>&source=<url>&why=<one sentence>
```

It needs a GitHub account. If they don't have one, give them the draft text to send however they like. Never claim a suggestion was sent. A pull request adding the source to `catalog.json` is the other route (see CONTRIBUTING.md in the repository).

## Unattended

Never add, mute or suggest during a scheduled run.
