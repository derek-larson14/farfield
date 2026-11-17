# Changes

## 0.2.0 (unreleased)

- Expand the starting catalog to 37 sources, including Martin Alderson, Every, independent evaluations, targeted paper discovery and five additional podcasts with published-transcript retrieval. Remove Derek Thompson.
- Define one dated discovery process for feeds and site archives, with pagination, deduplication and explicit incomplete coverage. Restore arXiv and dated Hugging Face paper instructions; these use the host's tools, not a new standalone collector.
- Maintain a bounded, dated working picture in the user's workspace to connect findings to actual projects and decisions.
- Shorten README and separate the detailed reading list. Clarify skill updates and private-repository limitations.
- Offer optional X discovery with cost estimates and a capped-key adapter; separate opt-in for cloud transcription with Whisper, Microsoft or ElevenLabs. No paid end-to-end run verified yet.
- Keep item-level reading history and cached transcripts; revisit promising ideas only when evidence changes.
- Link preview: a photo of the Very Large Array radio telescopes (CGP Grey, CC BY 2.0; credit in site/CREDITS.md).
- `radar.py items` lists dated items from every RSS/Atom source in parallel and flags feeds that stop inside the window. Briefs read in parallel batches through subagents where the host has them.
- `radar.py fetch` reads PDFs (pdftotext, or macOS's built-in PDFKit) so paper quotes can be checked; other binary content is refused.
- Quote checks give one verdict per quote, ignore curly-vs-straight quotes and the gap a link leaves before punctuation, and apply the same rules to excerpts and pages.
- Briefs have hard length limits (at most 3 findings, about 120 words each) and an edit pass that cuts what a reader doesn't need.
- Scheduled runs: the prompt says "unattended" so they end with a SUMMARY line, and the allowed tools cover every helper and subagents. Helpers are always run directly as single commands.
- Adding a source that is already listed (same URL or same site) points to the existing one. The reading ledger treats www. and trailing-slash variants as one item.
- Cloud transcription has a per-run budget in `audio.json` and refuses before sending anything over it. Test clips stream only the seconds they need. Parakeet is pinned.
- Source suggestions open a pre-filled GitHub issue. Setup questions mark a recommended option; the first brief's 10 to 30 minutes is stated up front.
- Every catalog source has a reason and access note.
- SOURCES.md is generated from the catalog and grouped into sections.
- Optional "Rhymes with your work": with permission, a local digest of what the user typed in recent Claude Code and Codex conversations (`threads.py`) lets a brief point to outside work that rhymes with how they work, framed as observations rather than advice. Replaces "from another field".

Validation before publishing: helper tests, plugin validation, site build, and a fresh-install/brief rehearsal. Installed versions do not update themselves.
