import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "farfield" / "scripts"))
import threads  # noqa: E402


def write(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in events))


class ThreadsTest(unittest.TestCase):
    def test_digest_keeps_only_what_the_person_typed(self):
        now = datetime.now(timezone.utc)
        recent, old = now.isoformat(), (now - timedelta(days=60)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            claude, codex, ws = tmp / "claude", tmp / "codex", tmp / "ws"
            write(claude / "-proj" / "aaaaaaaa-1.jsonl", [
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": recent,
                 "message": {"content": "Set up the eval harness again, key sk-abcdefghijklmnopqrstuv, mail me at a@b.co"}},
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": recent,
                 "message": {"content": [{"type": "tool_result", "is_error": True, "content": "SECRET TOOL OUTPUT"}]}},
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": recent,
                 "message": {"content": "<system-reminder>injected</system-reminder>"}},
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": recent, "isSidechain": True,
                 "message": {"content": "subagent prompt"}},
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": recent,
                 "message": {"content": "<pasted_content id=x>dictated thought about evals</pasted_content id=x>"}},
                {"type": "user", "cwd": str(tmp / "proj"), "timestamp": old, "message": {"content": "ancient history"}},
            ])
            write(codex / "2026" / "11" / "rollout-zzzzzzzz.jsonl", [
                {"type": "session_meta", "payload": {"cwd": str(tmp / "other")}},
                {"type": "response_item", "timestamp": recent,
                 "payload": {"role": "user", "content": [{"type": "input_text", "text": "Draft the onboarding copy"}]}},
                {"type": "response_item", "timestamp": recent,
                 "payload": {"role": "user", "content": [{"type": "input_text", "text": "# AGENTS.md instructions for x"}]}},
            ])
            with patch.object(threads, "CLAUDE", claude), patch.object(threads, "CODEX", codex):
                out = threads.digest(ws, days=30)
            text = Path(out["digest"]).read_text()
            self.assertEqual((out["claude_conversations"], out["codex_conversations"]), (1, 1))
            self.assertIn("Set up the eval harness again", text)
            self.assertIn("dictated thought about evals", text)
            self.assertIn("Draft the onboarding copy", text)
            self.assertIn("1 tool error(s)", text)
            self.assertIn("partial view", text)
            for absent in ("sk-abcdef", "a@b.co", "SECRET TOOL OUTPUT", "injected", "subagent prompt",
                           "ancient history", "AGENTS.md instructions"):
                self.assertNotIn(absent, text)

    def test_no_history_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with patch.object(threads, "CLAUDE", tmp / "none"), patch.object(threads, "CODEX", tmp / "none2"):
                out = threads.digest(tmp / "ws")
            self.assertEqual(out["projects"], 0)
            self.assertTrue(Path(out["digest"]).is_file())
