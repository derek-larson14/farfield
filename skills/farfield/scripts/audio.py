#!/usr/bin/env python3
"""Podcast audio for episodes with no published transcript. Optional: a brief works without it.

  audio.py find                          what this machine already has (tools, models), as JSON
  audio.py estimate <workspace> [--days 30]
                                         hours of audio in the enabled podcast sources, and what each
                                         way of transcribing it would cost
  audio.py install                       set up Parakeet in a private folder (Apple Silicon): its own Python
                                         environment, ffmpeg if Homebrew is here, and the 2.3 GB model
  audio.py use <workspace> skip|parakeet|whisper|openrouter [--model PATH_OR_NAME] [--budget USD]
                                         remember the choice in <workspace>/audio.json; --budget caps
                                         OpenRouter spend per transcribe call (default $1)
  audio.py transcribe <workspace> <audio-url> [--max-secs N]
                                         transcribe with the remembered choice; prints the transcript path

Local backends need ffmpeg. Parakeet needs Apple Silicon and `parakeet-mlx`; Whisper needs whisper.cpp's
`whisper-cli` and a ggml model file. OpenRouter needs OPENROUTER_API_KEY in the keys file.
"""
import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402  (same folder; the skill is self-contained)

PRICES = radar.SKILL / "stt.json"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
PODCAST = "{https://podcastindex.org/namespace/1.0}"
BACKENDS = ("skip", "parakeet", "whisper", "openrouter")
CHUNK_S = 300
PARAKEET_PIN = "parakeet-mlx==0.7.0"   # bump deliberately after testing; never install whatever is newest
DEFAULT_BUDGET_USD = 1.0
MODEL_DIRS = ("~/.cache/whisper.cpp", "~/.cache/whisper", "~/Library/Application Support/MacWhisper/models",
              "~/Library/Application Support/superwhisper", "~/models", "~/.cache/huggingface/hub")


def seconds(value):
    """itunes:duration is seconds, MM:SS or HH:MM:SS."""
    if not value:
        return None
    try:
        total = 0
        for part in value.strip().split(":"):
            total = total * 60 + int(float(part))
        return total
    except ValueError:
        return None


def episodes(xml, since):
    """(published, seconds or None, has_transcript, audio_url) for items on or after `since`."""
    xml = re.sub(r"^\s*<\?xml[^>]*\?>", "", xml)
    try:
        tree = ET.fromstring(xml)
    except ET.ParseError:
        # Long-running shows have feeds bigger than the download cap. Items are newest first, so keep
        # the complete ones and close the document.
        end = xml.rfind("</item>")
        if end < 0:
            raise
        tree = ET.fromstring(xml[:end + len("</item>")] + "</channel></rss>")
    out = []
    for item in tree.iter("item"):
        enclosure, published = item.find("enclosure"), item.findtext("pubDate")
        if enclosure is None or not published:
            continue
        try:
            when = parsedate_to_datetime(published)
        except (TypeError, ValueError):
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when < since:
            continue
        out.append({"title": (item.findtext("title") or "").strip(), "published": when.date().isoformat(),
                    "seconds": seconds(item.findtext(ITUNES + "duration")),
                    "has_transcript": item.find(PODCAST + "transcript") is not None,
                    "audio": enclosure.get("url")})
    return out


DATA = Path(os.environ.get("FARFIELD_DATA", Path.home() / ".local" / "share" / "farfield"))
VENV = DATA / "parakeet"


def parakeet_bin():
    own = VENV / "bin" / "parakeet-mlx"
    return str(own) if own.exists() else shutil.which("parakeet-mlx")


def say(text):
    print(text, file=sys.stderr, flush=True)


def install():
    """Everything Parakeet needs, in one go. Touches only DATA, the Hugging Face cache, and (via brew) ffmpeg."""
    if not (sys.platform == "darwin" and platform.machine() == "arm64"):
        raise ValueError("Parakeet needs an Apple Silicon Mac; use Whisper here (see references/audio.md)")
    if not shutil.which("ffmpeg"):
        if not shutil.which("brew"):
            raise ValueError("ffmpeg is missing and Homebrew is not installed; install ffmpeg, then run this again")
        say("1/3 installing ffmpeg with Homebrew")
        subprocess.run(["brew", "install", "ffmpeg"], check=True, stdout=subprocess.DEVNULL)
    else:
        say("1/3 ffmpeg is already here")
    if not parakeet_bin():
        python = next((p for p in (shutil.which(f"python3.{v}") for v in (13, 12, 11, 10)) if p), None)
        if not python and sys.version_info[:2] >= (3, 10):
            python = sys.executable
        if not python:
            raise ValueError("Parakeet needs Python 3.10 or newer (brew install python@3.13), then run this again")
        say(f"2/3 installing parakeet-mlx into {VENV}")
        DATA.mkdir(parents=True, exist_ok=True)
        subprocess.run([python, "-m", "venv", str(VENV)], check=True)
        subprocess.run([str(VENV / "bin" / "pip"), "install", "--quiet", "--disable-pip-version-check", PARAKEET_PIN], check=True)
    else:
        say("2/3 parakeet-mlx is already here")
    say("3/3 fetching the model (2.3 GB the first time) and testing it")
    with tempfile.TemporaryDirectory(prefix="farfield-audio-") as tmp:
        wav = os.path.join(tmp, "a.wav")
        run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "2", wav])
        subprocess.run([parakeet_bin(), wav, "--output-format", "txt", "--output-dir", tmp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"ready": True, "parakeet": parakeet_bin(),
            "remove": f"rm -rf {VENV} ~/.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v3"}


def find_local():
    """Look in the usual places only. Never walks the home directory."""
    models = []
    for folder in MODEL_DIRS:
        root = Path(folder).expanduser()
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            name = path.name.lower()
            if path.suffix == ".bin" and "ggml" in name:
                models.append(str(path))
            elif ("parakeet" in name or "whisper" in name) and path.is_dir() and any(path.rglob("*.safetensors")):
                models.append(str(path))   # a Hugging Face model folder that actually holds weights
    apple_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
    tools = {name: shutil.which(name) for name in ("ffmpeg", "whisper-cli", "brew")}
    tools["parakeet-mlx"] = parakeet_bin()
    ggml = [m for m in models if m.endswith(".bin")]
    # One recommendation. On Apple Silicon Parakeet came closer to a published transcript than Whisper
    # turbo in an initial local comparison; performance varies by machine.
    suggestion = "parakeet" if apple_silicon else "whisper"
    return {"apple_silicon": apple_silicon, "tools": tools, "models": models[:20], "suggested": suggestion,
            "ready": {"whisper": bool(tools["ffmpeg"] and tools["whisper-cli"] and ggml),
                      "parakeet": bool(tools["ffmpeg"] and tools["parakeet-mlx"]),
                      "openrouter": bool(tools["ffmpeg"] and "OPENROUTER_API_KEY" in radar.keys())}}


def feed_text(url):
    return radar.http(url, limit=40 * 1024 * 1024)   # some feeds list every episode since 2015


def estimate(root, days=30, fetch=feed_text):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    sources = radar.resolve_sources(radar.read_json(radar.CATALOG), radar.load_local(root))["sources"]
    shows, total, unknown, covered = [], 0, 0, 0
    for source in sources:
        if source.get("kind") != "podcast" or not source.get("enabled", True):
            continue
        if source.get("discovery") not in (None, "rss-or-atom"):
            shows.append({"id": source["id"], "name": source.get("name"), "skipped": "no RSS feed; publishes "
                          "transcripts on its site, so it needs no transcription"})
            continue
        try:
            found = episodes(fetch(source["url"]), since)
        except Exception as error:
            shows.append({"id": source["id"], "error": str(error)[:120]})
            continue
        need = [e for e in found if not e["has_transcript"]]
        secs = sum(e["seconds"] or 0 for e in need)
        unknown += sum(1 for e in need if not e["seconds"])
        covered += len(found) - len(need)
        total += secs
        missing = sum(1 for e in need if not e["seconds"])
        shows.append({"id": source["id"], "name": source.get("name"), "episodes": len(found),
                      "need_audio": len(need),
                      "hours": round(secs / 3600, 1) if need and missing < len(need) else (0 if not need else "unknown"),
                      **({"episodes_without_length": missing} if missing else {})})
    hours = total / 3600
    prices = radar.read_json(PRICES)
    return {"days": days, "hours": round(hours, 1), "episodes_with_published_transcript": covered,
            "episodes_with_unknown_length": unknown,
            "estimate_basis": "Feed-only upper estimate: episode pages may have transcripts not declared in RSS. Failed feeds and unknown durations make coverage incomplete. Reconcile against the selected unread episodes before approving spend.", "shows": shows, "prices_as_of": prices["as_of"],
            "options": [{"id": o["id"], "name": o["name"], "usd": round(hours * o["usd_per_hour"], 2),
                         "usd_per_hour": o["usd_per_hour"], "wired": o["wired"], "note": o["note"]}
                        for o in prices["options"]]}


def settings(root):
    path = Path(root).expanduser() / "audio.json"
    return radar.read_json(path) if path.exists() else {"backend": "skip"}


def use(root, backend, model=None, budget=None):
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of {', '.join(BACKENDS)}")
    if backend == "whisper":
        model = model or next((m for m in find_local()["models"] if m.endswith(".bin")), None)
        if not model or not Path(model).expanduser().exists():
            raise ValueError("whisper needs a ggml model file; pass --model PATH")
    if backend == "openrouter":
        model = model or "openai/whisper-large-v3-turbo"
        supported = {o.get("model") for o in radar.read_json(PRICES)["options"] if o.get("model")}
        if model not in supported:
            raise ValueError("unsupported transcription model; choose an option from audio.py estimate")
    value = {"backend": backend, **({"model": model} if model else {})}
    if backend == "openrouter":
        budget = DEFAULT_BUDGET_USD if budget is None else budget
        if not 0 < budget <= 50:
            raise ValueError("--budget must be between 0 and 50 dollars per run")
        value["budget_usd"] = budget
    (Path(root).expanduser() / "audio.json").write_text(json.dumps(value, indent=2) + "\n")
    return value


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def openrouter_chunk(path, key, model="openai/whisper-large-v3-turbo"):
    body = json.dumps({"model": model,
                       "input_audio": {"data": base64.b64encode(Path(path).read_bytes()).decode(), "format": "mp3"}}).encode()
    request = urllib.request.Request("https://openrouter.ai/api/v1/audio/transcriptions", data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": radar.UA})
    with urllib.request.urlopen(request, timeout=180) as response:
        out = json.loads(response.read())
    reported = (out.get("usage") or {}).get("cost")
    return (out.get("text") or "").strip(), float(reported) if reported is not None else None


def transcribe(root, url, max_secs=None):
    chosen = settings(root)
    backend = chosen["backend"]
    if backend == "skip":
        raise ValueError("audio is set to skip; choose a backend with `audio.py use`")
    folder = Path(root).expanduser() / "evidence" / "raw"
    cache_key = json.dumps([url, backend, chosen.get("model"), max_secs])
    path = folder / (hashlib.sha256(cache_key.encode()).hexdigest()[:20] + ".transcript.txt")
    meta_path = path.with_suffix(".json")
    if path.is_file() and path.stat().st_size and meta_path.is_file():
        return {**json.loads(meta_path.read_text()), "raw": str(path), "cached": True, "usd": 0}
    if backend == "openrouter" and not radar.keys().get("OPENROUTER_API_KEY"):
        raise ValueError("no OPENROUTER_API_KEY; run `radar.py keys --open`")
    if not shutil.which("ffmpeg"):
        raise ValueError("ffmpeg is not installed (macOS: brew install ffmpeg)")
    cut = ["-t", str(max_secs)] if max_secs else []
    cost = 0.0
    with tempfile.TemporaryDirectory(prefix="farfield-audio-") as tmp:
        pre, post = [], cut
        if max_secs:
            # A test clip streams only the first seconds; ffmpeg stops reading once it has them.
            src, pre = url, ["-user_agent", radar.UA]
        else:
            src = os.path.join(tmp, "src.audio")
            request = urllib.request.Request(url, headers={"User-Agent": radar.UA})
            with urllib.request.urlopen(request, timeout=300) as response, open(src, "wb") as handle:
                shutil.copyfileobj(response, handle)
        wav = os.path.join(tmp, "a.wav")
        if backend == "whisper":
            run(["ffmpeg", "-loglevel", "error", *pre, "-i", src, *post, "-map", "0:a:0", "-ac", "1", "-ar", "16000", wav])
            # -mc 0: no cross-segment context, which stops whisper's repeat loops on long audio
            run(["whisper-cli", "-m", str(Path(chosen["model"]).expanduser()), "-f", wav, "-otxt", "-of",
                 os.path.join(tmp, "o"), "-nt", "-np", "-mc", "0", "-t", str(os.cpu_count() or 4)])
            text = Path(tmp, "o.txt").read_text()
        elif backend == "parakeet":
            if not parakeet_bin():
                raise ValueError("Parakeet is not set up; run `audio.py install`")
            run(["ffmpeg", "-loglevel", "error", *pre, "-i", src, *post, "-map", "0:a:0", "-ac", "1", "-ar", "16000", wav])
            extra = ["--model", chosen["model"]] if chosen.get("model") else []
            run([parakeet_bin(), wav, "--output-format", "txt", "--output-dir", tmp, *extra])
            text = Path(tmp, "a.txt").read_text()
        else:
            key = radar.keys().get("OPENROUTER_API_KEY")
            if not key:
                raise ValueError("no OPENROUTER_API_KEY; run `radar.py keys --open`")
            run(["ffmpeg", "-loglevel", "error", *pre, "-i", src, *post, "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-b:a", "32k",
                 "-f", "segment", "-segment_time", str(CHUNK_S), "-reset_timestamps", "1", os.path.join(tmp, "c%03d.mp3")])
            chunks = sorted(Path(tmp).glob("c*.mp3"))
            rate = next((o["usd_per_hour"] for o in radar.read_json(PRICES)["options"]
                         if o.get("model") == chosen.get("model", "openai/whisper-large-v3-turbo")), None)
            budget = chosen.get("budget_usd", DEFAULT_BUDGET_USD)
            planned = len(chunks) * CHUNK_S / 3600 * (rate or 0)
            if rate is None or planned > budget:
                raise ValueError(f"this episode would cost about ${planned:.2f} with {chosen.get('model')}, over the "
                                 f"${budget:.2f} per-run budget in audio.json; nothing was sent. Ask the user before "
                                 "raising it with `audio.py use ... --budget`")
            parts = []
            for chunk in chunks:
                piece, spent = openrouter_chunk(chunk, key, chosen.get("model", "openai/whisper-large-v3-turbo"))
                parts.append(piece)
                cost = cost + spent if cost is not None and spent is not None else None
            text = "\n\n".join(p for p in parts if p)
    text = " ".join(text.split())
    if not text:
        raise ValueError("transcription produced no text")
    folder = Path(root).expanduser() / "evidence" / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{url}\nmachine transcript, {backend}{' (first %ss)' % max_secs if max_secs else ''}\n{text}\n")
    result = {"raw": str(path), "words": len(text.split()), "backend": backend,
              "model": chosen.get("model"), "max_secs": max_secs, "usd": round(cost, 4) if cost is not None else None, "cached": False}
    meta_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("find")
    commands.add_parser("install")
    est = commands.add_parser("estimate")
    est.add_argument("workspace")
    est.add_argument("--days", type=int, default=30)
    pick = commands.add_parser("use")
    pick.add_argument("workspace")
    pick.add_argument("backend", choices=BACKENDS)
    pick.add_argument("--model")
    pick.add_argument("--budget", type=float)
    tr = commands.add_parser("transcribe")
    tr.add_argument("workspace")
    tr.add_argument("url")
    tr.add_argument("--max-secs", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "find":
            out = find_local()
        elif args.command == "install":
            out = install()
        elif args.command == "estimate":
            out = estimate(args.workspace, args.days)
        elif args.command == "use":
            out = use(args.workspace, args.backend, args.model, args.budget)
        else:
            out = transcribe(args.workspace, args.url, args.max_secs)
        print(json.dumps(out, indent=1))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
