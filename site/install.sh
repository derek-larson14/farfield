#!/bin/sh
# Farfield installer. Mac and Linux. Installs the skill for Claude Code and/or Codex, whichever is here.
# It writes only: the Claude plugin cache (through the claude CLI) and ~/.agents/skills/farfield.
# This is the same file as site/install.sh in the repository; nothing is filled in at build time.
# It asks for nothing, needs no key, and does not touch your workspace. Run it again to update.
set -eu
REPO="${FARFIELD_REPO:-derek-larson14/farfield}"
found=0

case "$(uname -s)" in Darwin|Linux) ;; *) echo "Mac and Linux only."; exit 1 ;; esac

if command -v claude >/dev/null 2>&1; then
  found=1
  echo "Claude Code: installing the plugin"
  claude plugin marketplace add "$REPO" >/dev/null 2>&1 || claude plugin marketplace update farfield >/dev/null
  claude plugin install farfield@farfield >/dev/null 2>&1 || claude plugin update farfield@farfield >/dev/null
  echo "  done. In Claude Code, type:  /farfield:start"
fi

if command -v codex >/dev/null 2>&1 || [ -d "$HOME/.codex" ]; then
  found=1
  command -v git >/dev/null 2>&1 || { echo "Codex: git is needed to fetch the skill."; exit 1; }
  echo "Codex: copying the skill to ~/.agents/skills/farfield"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  git clone --quiet --depth 1 "https://github.com/$REPO" "$tmp/repo"
  [ -f "$tmp/repo/skills/farfield/SKILL.md" ] || { echo "  the download does not look right; nothing changed."; exit 1; }
  mkdir -p "$HOME/.agents/skills"
  rm -rf "$HOME/.agents/skills/farfield"
  cp -R "$tmp/repo/skills/farfield" "$HOME/.agents/skills/farfield"
  echo "  done. In Codex, type:  \$farfield start"
fi

if [ "$found" = 0 ]; then
  echo "Neither Claude Code nor Codex was found on this machine."
  echo "Install one, or paste this into any agent that can read the web:"
  echo "  Set up Farfield for me. Read https://github.com/$REPO/blob/main/AGENTS.md and follow it: install the skill, ask me the setup questions, then write my first brief."
  exit 1
fi
