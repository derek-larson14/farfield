# For agents: install and start

Someone asked you to set up Farfield. Install it for them, then run setup in the same conversation. Don't hand back a list of steps.

If you are here to change this repository rather than install it, read [CONTRIBUTING.md](CONTRIBUTING.md) instead.

## 1. Install (pick the first that matches)

Everything installs from https://farfield.newyorkai.org. No git, no GitHub account, no clone. Don't look for the source repository or use anyone's credentials; if a command below fails, tell the user what failed.

**Claude Code, with a shell.** Run:

```sh
claude plugin marketplace add https://farfield.newyorkai.org/marketplace.json
claude plugin install farfield@farfield
```

If the first command says a marketplace named `farfield` already exists from somewhere else, run `claude plugin marketplace remove farfield` and both commands again.

The plugin's commands load in new sessions. Don't make them restart: read `skills/farfield/SKILL.md` from the installed plugin (`claude plugin list` shows where it is; or `find ~/.claude/plugins/cache -path '*farfield*' -name SKILL.md | sort | tail -1`) and continue to step 2. Tell them that next time it's `/farfield:brief`.

**Claude desktop app or Cowork, without a terminal tool.** You can't install a plugin from inside a chat. Tell them: Customize → Browse plugins → Personal → Add marketplace, paste `https://farfield.newyorkai.org/marketplace.json`, Install, then type `/farfield:start`.

**Codex, or any agent with a shell.** Download the skill folder into the user's skills directory:

```sh
mkdir -p ~/.agents/skills && rm -rf ~/.agents/skills/farfield \
  && curl -fsSL https://farfield.newyorkai.org/farfield-skill.tar.gz | tar -xz -C ~/.agents/skills
```

Then read `~/.agents/skills/farfield/SKILL.md` and continue to step 2. In Codex, next time it's `$farfield brief`. For another agent, put the folder wherever it keeps skills; it needs to read and write files, run `python3` (3.9+, standard library only) and fetch web pages.

Running the same install again is how it updates. It never touches the user's workspace.

## 2. Start

Follow `SKILL.md` in **start** mode: one open question, four choices, two optional questions about how they work, a five-line summary to correct, then the first brief (about 10 to 30 minutes of reading; say so), then an offer to schedule it. The standard brief needs no API key or sign-up. The optional Twitter/X offer can connect OpenRouter; explain estimated costs and keep it off unless chosen. Never request a key in chat.

## What gets written where

- The skill: the plugin cache (Claude) or `~/.agents/skills/farfield` (Codex).
- The user's workspace: the folder they pick in setup, default `~/farfield`.
- A one-line pointer to that folder: `~/.config/farfield/workspace`.
- Only if the user agrees to it during setup: a short digest of what they typed in recent Claude Code and Codex conversations, in `<workspace>/state/threads/`. It reads `~/.claude/projects` and `~/.codex/sessions` and never writes there.
- Only if the user adds an optional key: `~/.config/farfield/env`, owner-readable only.
- Only if the user turns on local podcast transcription: a private Parakeet environment in `~/.local/share/farfield/parakeet`, its model in `~/.cache/huggingface/hub`, and ffmpeg through Homebrew if it was missing.

Nothing else. To remove everything: uninstall the plugin or delete the skill folder, delete the workspace, delete `~/.config/farfield` and `~/.local/share/farfield`, delete `~/.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v3` if present, and remove any schedule listed in `<workspace>/state/schedule.md`.
