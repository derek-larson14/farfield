# For agents: install and start

Someone asked you to set up Farfield. Install it for them, then run setup in the same conversation. Don't hand back a list of steps.

If you are here to change this repository rather than install it, read [CONTRIBUTING.md](CONTRIBUTING.md) instead.

## 1. Install (pick the first that matches)

Use the install route for your app below. None requires a GitHub account or a manual clone. If a command fails, tell the user what failed.

**Claude Code, with a shell.** Run:

```sh
claude plugin marketplace add https://farfield.newyorkai.org/marketplace.json
claude plugin install farfield@farfield
```

If it was already installed, update it instead: `claude plugin marketplace update farfield && claude plugin update farfield@farfield` (`install` alone keeps the old version).

If the first command says a marketplace named `farfield` already exists from somewhere else, run `claude plugin marketplace remove farfield` and both commands again.

The plugin's commands load in new sessions. Don't make them restart: read `skills/farfield/SKILL.md` from the installed plugin (`claude plugin list` shows where it is; or `find ~/.claude/plugins/cache -path '*farfield*' -name SKILL.md | sort | tail -1`) and continue to step 2. Tell them that next time it's `/farfield:brief`.

**Claude desktop app or Cowork, without a terminal tool.** Install through the plugin screens:

1. Open **Customize → Plugins → + Add → Add marketplace → Add from a repository**.
2. Click **Select a repository**, enter `derek-larson14/farfield`, choose **Use “derek-larson14/farfield”**, then click **Sync**. The public repo works without connecting GitHub. **Grant access** is for automatic syncing. The hosted `marketplace.json` URL is only for Claude Code's terminal install.
3. Under **Discover**, open **Farfield** and click **Add**.

Alternatively, download [farfield.zip](https://farfield.newyorkai.org/farfield.zip). In **Customize → Plugins → + Add → Upload plugin**, browse for the ZIP, click **Open**, then **Upload**.

To start, open a new session in the **Code** tab, type `/farfield`, and select **farfield:start**. In other Claude chats the command may appear as **start**, but setup requires the structured question tool and local file access. The plugin added through **Customize** is saved to your Claude account. A terminal install with `claude plugin install` is separate from this account install.

**claude.ai chat, or any sandbox that can't reach farfield.newyorkai.org or ordinary websites.** Farfield can't run there: a brief reads dozens of sites, and these sandboxes only reach an allowlist. Don't offer to set it up by hand from pasted files. Tell the user in two sentences that Farfield runs in Claude Code (terminal or the desktop app's Code tab), Cowork, or Codex, and give the matching step above or below.

**Codex, or any agent with a shell.** Download the skill folder into the user's skills directory:

```sh
mkdir -p ~/.agents/skills && rm -rf ~/.agents/skills/farfield \
  && curl -fsSL https://farfield.newyorkai.org/farfield-skill.tar.gz | tar -xz -C ~/.agents/skills
```

Then read `~/.agents/skills/farfield/SKILL.md` and continue to step 2. In Codex, next time it's `$farfield brief`. For another agent, put the folder wherever it keeps skills; it needs to read and write files, run `python3` (3.9+, standard library only) and fetch web pages.

Running the install again updates it (for Claude Code, with the update command above). It never touches the user's workspace.

## 2. Start

Follow `SKILL.md` in **start** mode. Use the structured question tool throughout. Ask where to look, with the option to describe the work and name multiple local folders or specific places in connected apps in one answer. Read only the approved locations, save those scopes in `me.md`, and confirm the working picture before writing the first brief (about 10 to 30 minutes of reading). Offer scheduling afterward. The standard brief needs no API key or sign-up. The optional Twitter/X offer can connect OpenRouter; explain estimated costs and keep it off unless chosen. Never request a key in chat.

## What gets written where

- The skill: the plugin cache (Claude) or `~/.agents/skills/farfield` (Codex).
- The user's workspace: the folder they pick in setup, default `~/farfield`.
- A one-line pointer to that folder: `~/.config/farfield/workspace`.
- Only if the user agrees to it during setup: a short digest of what they typed in recent Claude Code and Codex conversations, in `<workspace>/state/threads/`. It reads `~/.claude/projects` and `~/.codex/sessions` and never writes there.
- Only if the user adds an optional key: `~/.config/farfield/env`, owner-readable only.
- Only if the user turns on local podcast transcription: a private Parakeet environment in `~/.local/share/farfield/parakeet`, its model in `~/.cache/huggingface/hub`, and ffmpeg through Homebrew if it was missing.

Nothing else. To remove everything: uninstall the plugin or delete the skill folder, delete the workspace, delete `~/.config/farfield` and `~/.local/share/farfield`, delete `~/.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v3` if present, and remove any schedule listed in `<workspace>/state/schedule.md`.
