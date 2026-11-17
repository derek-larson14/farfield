#!/bin/sh
# Farfield installer. Mac and Linux. Installs the skill for Claude Code and/or Codex, whichever is here.
# It writes only: the Claude plugin cache (through the claude CLI) and ~/.agents/skills/farfield.
# Everything comes from the website; it needs no git and no GitHub account.
# This is the same file as site/install.sh in the repository; nothing is filled in at build time.
# It asks for nothing, needs no key, and does not touch your workspace. Run it again to update.
set -eu
SITE="${FARFIELD_SITE:-https://farfield.newyorkai.org}"
found=0

case "$(uname -s)" in Darwin|Linux) ;; *) echo "Mac and Linux only."; exit 1 ;; esac

if command -v claude >/dev/null 2>&1; then
  found=1
  echo "Claude Code: installing the plugin"
  if ! claude plugin marketplace add "$SITE/marketplace.json" >/dev/null 2>&1; then
    # An older install added the marketplace from GitHub; switch it to the website.
    claude plugin marketplace remove farfield >/dev/null 2>&1 || true
    claude plugin marketplace add "$SITE/marketplace.json" >/dev/null
  fi
  claude plugin marketplace update farfield >/dev/null
  claude plugin install farfield@farfield >/dev/null 2>&1 || claude plugin update farfield@farfield >/dev/null
  echo "  done. In Claude Code, type:  /farfield:start"
fi

if command -v codex >/dev/null 2>&1 || [ -d "$HOME/.codex" ]; then
  found=1
  echo "Codex: downloading the skill to ~/.agents/skills/farfield"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL "$SITE/farfield-skill.tar.gz" | tar -xz -C "$tmp"
  [ -f "$tmp/farfield/SKILL.md" ] || { echo "  the download does not look right; nothing changed."; exit 1; }
  mkdir -p "$HOME/.agents/skills"
  rm -rf "$HOME/.agents/skills/farfield"
  mv "$tmp/farfield" "$HOME/.agents/skills/farfield"
  echo "  done. In Codex, type:  \$farfield start"
fi

if [ "$found" = 0 ]; then
  echo "Neither Claude Code nor Codex was found on this machine."
  echo "Install one, or paste this into any agent that can read the web:"
  echo "  Set up Farfield for me. Read $SITE/install.md in full and follow it: install the skill, ask me the setup questions and wait for my answers, then write my first brief."
  exit 1
fi
