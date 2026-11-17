# Contributing to Farfield

## Working on the code

The portable product is `skills/farfield/`. It must work when copied on its own. The four files in `commands/` expose the Claude plugin commands. The website lives in `site/`.

Run `python3 -m unittest discover -s tests` and `claude plugin validate .` before submitting changes. Build the website with `sh site/build.sh`. Keep `skills/farfield/skill.json` and `.claude-plugin/plugin.json` versions in sync.

Preserve user edits when initializing or updating a workspace. Never silently enable sources, audio downloads, or schedules. Quotes must be checked against the source text; unsupported quotes are dropped or explicitly marked unchecked.

## Suggest a source

Ask `/farfield:sources suggest <name or URL>` (Codex: `$farfield sources suggest ...`) to draft a suggestion. Include the source URL, one example, and a sentence about what it adds. The private suggestions inbox is not configured in this release, so the agent gives you the draft instead of claiming it was sent.

You can open a pull request against `skills/farfield/catalog.json`. Pull requests and their contents are public: leave out private projects, notes, paths, and contact information.

Include a stable source ID, canonical URL, source kind, retrieval method, and transcript or access restrictions. Identify podcast/YouTube duplicates so they are not treated as independent evidence. Do not change an existing source ID without explaining the migration.

Catalog changes are reviewed for original information, credible evidence, and perspectives missing from the list. Popularity alone is not a reason to include a source. Local additions and mutes must survive catalog updates.
