import hashlib
import json
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class PackageTest(unittest.TestCase):
    def test_site_packages_install_without_git(self):
        with tempfile.TemporaryDirectory() as dist:
            dist = Path(dist)
            subprocess.run([sys.executable, str(REPO / "site" / "package.py"), str(REPO), str(dist),
                            "https://example.org"], check=True, capture_output=True)
            market = json.loads((dist / "marketplace.json").read_text())
            source = market["plugins"][0]["source"]
            self.assertEqual(source["source"], "archive")
            self.assertEqual(source["url"], "https://example.org/farfield.zip")
            self.assertEqual(source["sha256"], hashlib.sha256((dist / "farfield.zip").read_bytes()).hexdigest())
            version = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())["version"]
            self.assertEqual(market["plugins"][0]["version"], version)
            with zipfile.ZipFile(dist / "farfield.zip") as archive:
                names = archive.namelist()
                self.assertIn(".claude-plugin/plugin.json", names)
                self.assertIn("skills/farfield/SKILL.md", names)
                self.assertFalse([n for n in names if "__pycache__" in n or n.startswith(("site/", "tests/"))])
                mode = archive.getinfo("skills/farfield/scripts/radar.py").external_attr >> 16
                self.assertTrue(mode & stat.S_IXUSR)
            with tarfile.open(dist / "farfield-skill.tar.gz") as archive:
                members = {m.name: m for m in archive.getmembers()}
            self.assertIn("farfield/SKILL.md", members)
            self.assertTrue(members["farfield/scripts/radar.py"].mode & stat.S_IXUSR)
            self.assertEqual(json.loads((dist / "skill.json").read_text())["version"], version)
