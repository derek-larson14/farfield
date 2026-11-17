"""Offline CLI rehearsal. Exercises the real entrypoint with an isolated config."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/farfield"


class OnboardingTest(unittest.TestCase):
    def test_first_run_only_own_sources_and_repeat_setup(self):
        with tempfile.TemporaryDirectory(prefix="farfield-onboarding-") as temp:
            root = Path(temp).resolve()
            workspace = root / "briefs with spaces"
            config = root / "config"
            env = dict(os.environ, FARFIELD_CONFIG=str(config))
            env.pop("EXA_API_KEY", None)
            env.pop("OPENROUTER_API_KEY", None)

            def run(*args, code=0):
                result = subprocess.run(
                    [sys.executable, str(SKILL / "scripts/radar.py"), *map(str, args)],
                    env=env, capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                return result.stdout

            run("where", code=3)
            run("init", workspace)
            self.assertEqual(run("where").strip(), str(workspace))
            self.assertEqual((config / "workspace").read_text().strip(), str(workspace))
            self.assertFalse(any(json.loads(run("keys")).values()))
            run("source-mode", workspace, "only-mine")
            run("add", workspace, "https://example.org/feed", "--name", "My Journal")
            sources = json.loads(run("sources", workspace, "--json"))["sources"]
            self.assertEqual([s["id"] for s in sources if s.get("enabled")], ["local:my-journal"])

            profile = workspace / "me.md"
            profile.write_text("# Me\n\n## Working on\nCommunity newsletter\n")
            feedback = workspace / "feedback.md"
            feedback.write_text("My feedback must survive setup.\n")
            run("init", workspace)
            self.assertIn("Community newsletter", profile.read_text())
            self.assertEqual(feedback.read_text(), "My feedback must survive setup.\n")
            sources = json.loads(run("sources", workspace, "--json"))["sources"]
            self.assertEqual([s["id"] for s in sources if s.get("enabled")], ["local:my-journal"])
            self.assertFalse((config / "env").exists())
            self.assertFalse((workspace / "audio.json").exists())
            self.assertFalse((workspace / "state/schedule.md").exists())


if __name__ == "__main__":
    unittest.main()
