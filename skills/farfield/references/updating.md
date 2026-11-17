# Updating

Three things change at different speeds. Keep them apart.

| What | Where it lives | How it updates |
|---|---|---|
| The user's files (`me.md`, `sources.local.json`, briefs, feedback) | their workspace | Never touched by an update |
| The curated source list | `catalog.json` inside the installed skill | Ships with a skill release. Refresh the resolved list after installation; preserve local additions, mutes and only-my-own mode |
| The skill itself (these instructions and scripts) | the installed plugin or skill folder | Only when the user asks |

## When `HELPER version --check` says an update is available

Say one line: "A newer Farfield is available (`<current>` → `<latest>`)." Then, if they want it:

- **Claude Code / desktop:** `/plugin marketplace update farfield`, then `/plugin update farfield@farfield`, then restart the session. From a shell: `claude plugin marketplace update farfield && claude plugin update farfield@farfield`.
- **Codex or a copied skill folder:** follow the install steps in the repository's AGENTS.md again; it replaces `~/.agents/skills/farfield` and nothing else.
- **Cloud schedule (workspace is a repo):** the skill copy in `.claude/skills/farfield/` is theirs to refresh; replace that folder and commit.

After updating, run `HELPER sources <workspace>` so `sources.md` reflects the new curated list, and tell the user what was added or removed.

## Rules

- Never download and run new code during a brief. A scheduled run that notices an update finishes the brief with the version it has and mentions the update in its summary.
- If the workspace was created by a newer version than the installed skill (`state/version`), stop and say so rather than guessing at the format.

## Releases and availability

Plugin and skill copies share one version and one GitHub release tag. Reinstalling a copied skill is an explicit update, not an automatic background operation. A release does not refresh already installed copies. Existing workspace files, including `state/context.md`, remain in place.

While the repository is private, anonymous install and raw-GitHub version checks cannot work. Treat authentication failures as “could not check,” not “up to date”; do not ask for credentials in chat. Existing installed copies can continue writing briefs. Use an already authenticated local checkout to test updates during private iteration.
