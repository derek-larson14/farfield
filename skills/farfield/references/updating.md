# Updating

Three things change at different speeds. Keep them apart.

| What | Where it lives | How it updates |
|---|---|---|
| The user's files (`me.md`, `sources.local.json`, briefs, feedback) | their workspace | Never touched by an update |
| The curated source list and, later, the shared evidence feed | data: `catalog.json`, `feed.json` → GitHub | Data only. New curated sources appear in `sources.md` after an update; anything the user muted stays muted |
| The skill itself (these instructions and two scripts) | the installed plugin or skill folder | Only when the user asks |

## When `HELPER version --check` says an update is available

Say one line: "A newer Farfield is available (`<current>` → `<latest>`)." Then, if they want it:

- **Claude Code / desktop:** `/plugin marketplace update farfield`, then `/plugin update farfield@farfield`, then restart the session. From a shell: `claude plugin marketplace update farfield && claude plugin update farfield@farfield`.
- **Codex or a copied skill folder:** follow the install steps in the repository's AGENTS.md again; it replaces `~/.agents/skills/farfield` and nothing else.
- **Cloud schedule (workspace is a repo):** the skill copy in `.claude/skills/farfield/` is theirs to refresh; replace that folder and commit.

After updating, run `HELPER sources <workspace>` so `sources.md` reflects the new curated list, and tell the user what was added or removed.

## Rules

- Never download and run new code during a brief. A scheduled run that notices an update finishes the brief with the version it has and mentions the update in its summary.
- If the workspace was created by a newer version than the installed skill (`state/version`), stop and say so rather than guessing at the format.
