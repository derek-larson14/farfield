#!/usr/bin/env python3
"""Package Farfield for installing straight from the website, with no git and no GitHub.

  python3 package.py <repo root> <dist folder> <https://domain>

Writes into <dist>:
  farfield.zip             the Claude Code plugin (.claude-plugin/, commands/, skills/)
  marketplace.json         a Claude Code marketplace whose one plugin is that zip, pinned by sha256
  farfield-skill.tar.gz    just skills/farfield, for Codex and other agents (extracts to farfield/)
  skill.json               the version file the installed skill checks for updates

Python, not shell, because the Vercel build image has no zip command. Standard library only.
"""
import hashlib
import io
import json
import sys
import tarfile
import zipfile
from pathlib import Path

SKIP = {"__pycache__", ".DS_Store"}


def files(root, *parts):
    for part in parts:
        base = root / part
        paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in paths:
            if not SKIP & set(path.relative_to(root).parts):
                yield path


def main(repo, dist, origin):
    repo, dist = Path(repo).resolve(), Path(dist).resolve()
    dist.mkdir(parents=True, exist_ok=True)

    plugin = repo / ".claude-plugin" / "plugin.json"
    zip_path = dist / "farfield.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files(repo, ".claude-plugin/plugin.json", "commands", "skills"):
            info = zipfile.ZipInfo(str(path.relative_to(repo)), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (path.stat().st_mode & 0o777 | 0o100000) << 16   # keep scripts executable
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()

    source = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    entry = dict(source["plugins"][0])
    entry["source"] = {"source": "archive", "url": f"{origin}/farfield.zip", "sha256": digest}
    entry["version"] = json.loads(plugin.read_text())["version"]
    hosted = {k: v for k, v in source.items() if k != "plugins"}
    hosted["plugins"] = [entry]
    (dist / "marketplace.json").write_text(json.dumps(hosted, indent=2) + "\n")

    with tarfile.open(dist / "farfield-skill.tar.gz", "w:gz") as archive:
        skill = repo / "skills" / "farfield"
        for path in files(repo, "skills/farfield"):
            info = archive.gettarinfo(str(path), arcname=str(Path("farfield") / path.relative_to(skill)))
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 1767225600
            with path.open("rb") as handle:
                archive.addfile(info, handle)

    meta = json.loads((repo / "skills" / "farfield" / "skill.json").read_text())
    (dist / "skill.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"packaged {entry['version']}: farfield.zip ({digest[:12]}), marketplace.json, farfield-skill.tar.gz, skill.json")


if __name__ == "__main__":
    main(*sys.argv[1:4])
