# Contributing to Farfield

## Working on the code

The portable product is `skills/farfield/`. It must work when copied on its own. The four files in `commands/` expose the Claude plugin commands. The website lives in `site/`.

Run `python3 -m unittest discover -s tests` and `claude plugin validate .` before submitting changes. After editing `catalog.json`, run `tools/sources_md.py` to regenerate SOURCES.md (a test fails if you forget). `scripts/feed.py` (the shared-feed downloader, unused until a feed is published) is tested in `tests/test_feed.py`. Build the website with `sh site/build.sh`. Keep `skills/farfield/skill.json` and `.claude-plugin/plugin.json` versions in sync.

Preserve user edits when initializing or updating a workspace. Never silently enable sources, audio downloads, or schedules. Quotes must be checked against the source text; unsupported quotes are dropped or explicitly marked unchecked.

## Suggest a source

[Open a source suggestion](https://github.com/derek-larson14/farfield/issues/new?template=source.yml): the source URL, one example, and a sentence about what it adds. Or ask `/farfield:sources suggest <name or URL>` (Codex: `$farfield sources suggest ...`), which drafts it and gives you a pre-filled link to that same form.

You can open a pull request against `skills/farfield/catalog.json`. Treat pull requests and their contents as publishable: leave out private projects, notes, paths, and contact information.

Include a stable source ID, canonical URL, source kind, retrieval method, and transcript or access restrictions. Identify podcast/YouTube duplicates so they are not treated as independent evidence. Do not change an existing source ID without explaining the migration.

Catalog changes are reviewed for original information, credible evidence, and perspectives missing from the list. Popularity alone is not a reason to include a source. Local additions and mutes must survive catalog updates.

## Release

Bump the version for every change you push to main: installed Claude Code plugins are cached by version and ignore new commits under the same number. Keep the plugin, skill and catalog versions in sync (a test checks). Run the checks above, document behavior changes in CHANGELOG.md, then tag the tested commit `v<version>` and create its GitHub release. Never include user workspaces or local credentials. Keep the repository private during iteration; a release does not change visibility. Verify installation from the tag before claiming a release is ready for public use.
