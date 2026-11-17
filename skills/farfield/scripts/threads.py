#!/usr/bin/env python3
"""A small, local digest of the user's recent agent conversations, so a brief can notice what they spend
their time on. Only used if the user said yes during setup. Nothing leaves this computer.

  threads.py digest <workspace> [--days 30] [--max-kb 60]
      read recent Claude Code (~/.claude/projects) and Codex (~/.codex/sessions) conversations, keep only
      what the person typed (no tool output, no file contents), redact anything that looks like a key, and
      write state/threads/<date>.md grouped by project, newest first

The digest says what was visible and what wasn't: other machines, other apps and work outside these
agents never appear in it.
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

CLAUDE = Path(os.environ.get("FARFIELD_CLAUDE_DIR", Path.home() / ".claude" / "projects"))
CODEX = Path(os.environ.get("FARFIELD_CODEX_DIR", Path.home() / ".codex" / "sessions"))
MAX_MESSAGE = 400

# Text the agent host injects into the user's turn; it isn't something the person typed.
INJECTED = ("<command-", "<local-command", "<system-reminder", "<environment_context", "<permissions",
            "<user_instructions", "<task-notification", "<teammate-message", "Base directory for this skill",
            "Caveat:", "# AGENTS.md instructions", "[Request interrupted", "This session is being continued",
            "Another Claude session sent a message", "Use the `farfield` skill", "The user sent a new message while")
SECRETS = [
    re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_-]{16,}"),            # OpenAI/Anthropic/OpenRouter/Stripe style
    re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),   # JWT
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),                    # email addresses
]


def redact(text):
    for pattern in SECRETS:
        text = pattern.sub("[redacted]", text)
    return text


def clean(text):
    # Many people paste what they mean (dictation, notes); keep the words, drop the wrapper.
    text = re.sub(r"</?pasted_content[^>]*>", " ", text)
    text = " ".join(text.split())
    if not text or text.startswith(INJECTED):
        return ""
    text = redact(text)
    return text if len(text) <= MAX_MESSAGE else text[:MAX_MESSAGE].rsplit(" ", 1)[0] + " …"


def stamp(value):
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def lines(path):
    try:
        with path.open(errors="replace") as handle:
            for raw in handle:
                try:
                    yield json.loads(raw)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def claude_threads(since):
    """(project folder, thread id, [(time, text)], tool errors) per Claude Code conversation."""
    if not CLAUDE.is_dir():
        return
    for path in CLAUDE.glob("*/*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
            continue
        cwd, said, errors = None, [], 0
        for event in lines(path):
            if event.get("type") != "user" or event.get("isSidechain") or event.get("isMeta"):
                continue
            cwd = cwd or event.get("cwd")
            when = stamp(event.get("timestamp"))
            content = (event.get("message") or {}).get("content")
            texts = []
            if isinstance(content, str):
                texts = [content]
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif part.get("type") == "tool_result" and part.get("is_error"):
                        errors += 1
            for text in texts:
                text = clean(text)
                if text and when and when >= since:
                    said.append((when, text))
        if said:
            yield cwd or path.parent.name, "claude:" + path.stem[:8], said, errors


def codex_threads(since):
    if not CODEX.is_dir():
        return
    for path in CODEX.rglob("*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
            continue
        cwd, said = None, []
        for event in lines(path):
            payload = event.get("payload") or {}
            if event.get("type") == "session_meta":
                cwd = payload.get("cwd")
                continue
            if event.get("type") != "response_item" or payload.get("role") != "user":
                continue
            when = stamp(event.get("timestamp"))
            for part in payload.get("content") or []:
                text = clean(part.get("text", "")) if part.get("type") == "input_text" else ""
                if text and when and when >= since:
                    said.append((when, text))
        if said:
            yield cwd or "unknown folder", "codex:" + path.stem[-8:], said, 0


def project_name(folder):
    home = str(Path.home())
    folder = str(folder)
    return "~" + folder[len(home):] if folder.startswith(home) else folder


def digest(root, days=30, max_kb=60):
    root = Path(root).expanduser()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    projects = {}
    counts = {"claude": 0, "codex": 0}
    for source in (claude_threads(since), codex_threads(since)):
        for folder, thread, said, errors in source:
            counts[thread.split(":")[0]] += 1
            projects.setdefault(project_name(folder), []).append((thread, sorted(said), errors))

    def latest(threads):
        return max(said[-1][0] for _, said, _ in threads)

    out = [f"# How you've been working: last {days} days", "",
           f"Generated {date.today().isoformat()} from {counts['claude']} Claude Code and {counts['codex']} Codex "
           "conversations on this computer. Only what you typed is included (shortened, keys and emails redacted); "
           "no tool output or file contents.",
           "", "This is a partial view: work on other computers, in other apps, in meetings or in your head isn't "
           "here. Treat it as a few windows into your work, not the whole of it.", ""]
    budget = max_kb * 1024
    for name, threads in sorted(projects.items(), key=lambda item: latest(item[1]), reverse=True):
        messages = sum(len(said) for _, said, _ in threads)
        errors = sum(e for _, _, e in threads)
        section = [f"## {name}", "",
                   f"{len(threads)} conversation(s), {messages} message(s)"
                   + (f", {errors} tool error(s)" if errors else "") + f", last on {latest(threads).date().isoformat()}.", ""]
        for thread, said, _ in sorted(threads, key=lambda t: t[1][-1][0], reverse=True):
            section.append(f"- {said[0][0].date().isoformat()} ({thread}): " + " / ".join(text for _, text in said[:6])
                           + (f" / … {len(said) - 6} more" if len(said) > 6 else ""))
        section.append("")
        text = "\n".join(section)
        if len(text.encode()) > budget:
            out.append(f"_{len(projects) - len([l for l in out if l.startswith('## ')])} more project(s) left out "
                       "to keep this digest small._")
            break
        out.append(text)
        budget -= len(text.encode())
    folder = root / "state" / "threads"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{date.today().isoformat()}.md"
    path.write_text("\n".join(out).rstrip() + "\n")
    return {"digest": str(path), "projects": len(projects), "claude_conversations": counts["claude"],
            "codex_conversations": counts["codex"], "days": days}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("digest")
    sub.add_argument("workspace")
    sub.add_argument("--days", type=int, default=30)
    sub.add_argument("--max-kb", type=int, default=60)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(digest(args.workspace, args.days, args.max_kb)))
    except OSError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
