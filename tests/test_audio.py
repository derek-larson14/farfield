import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audio", REPO / "skills/farfield/scripts/audio.py")
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)
radar = audio.radar


def feed(items):
    body = "".join(
        f"<item><title>{t}</title><pubDate>{format_datetime(when)}</pubDate>"
        f"<enclosure url='https://example.org/{t}.mp3'/>"
        + (f"<itunes:duration>{d}</itunes:duration>" if d else "")
        + ("<podcast:transcript url='https://example.org/t.vtt' type='text/vtt'/>" if tr else "") + "</item>"
        for t, when, d, tr in items)
    return ("<?xml version='1.0' encoding='UTF-8'?><rss xmlns:itunes='http://www.itunes.com/dtds/podcast-1.0.dtd' "
            "xmlns:podcast='https://podcastindex.org/namespace/1.0'><channel>" + body + "</channel></rss>")


class AudioTest(unittest.TestCase):
    def test_durations(self):
        self.assertEqual([audio.seconds(v) for v in ("3600", "01:02:03", "12:30", "", "abc")],
                         [3600, 3723, 750, None, None])

    def test_estimate_counts_only_recent_episodes_without_a_transcript(self):
        now = datetime.now(timezone.utc)
        xml = feed([("new", now - timedelta(days=2), "02:00:00", False),
                    ("has-transcript", now - timedelta(days=3), "01:00:00", True),
                    ("no-length", now - timedelta(days=4), None, False),
                    ("old", now - timedelta(days=90), "05:00:00", False)])
        with tempfile.TemporaryDirectory() as path:
            radar.init_workspace(path, remember=False)
            podcasts = [s for s in radar.read_json(radar.CATALOG)["sources"] if s["kind"] == "podcast"]
            for source in podcasts[1:]:
                radar.set_enabled(path, source["id"], False)
            out = audio.estimate(path, days=30, fetch=lambda url: xml)
        self.assertEqual(out["hours"], 2.0)
        self.assertEqual(out["episodes_with_published_transcript"], 1)
        self.assertEqual(out["episodes_with_unknown_length"], 1)
        self.assertEqual(len(out["shows"]), 1)
        by = {o["id"]: o for o in out["options"]}
        self.assertEqual(by["parakeet"]["usd"], 0)
        self.assertEqual(by["openrouter"]["usd"], 0.02)
        self.assertEqual(set(by), {"parakeet", "whisper", "openrouter"})
        self.assertTrue(all(option["wired"] for option in by.values()))

    def test_feed_cut_off_mid_item_still_yields_the_complete_items(self):
        now = datetime.now(timezone.utc)
        xml = feed([("a", now, "10:00", False), ("b", now, "20:00", False)])
        cut = xml[:xml.rfind("<item>") + 30]
        got = audio.episodes(cut, now - timedelta(days=1))
        self.assertEqual([e["title"] for e in got], ["a"])

    def test_choice_is_remembered_and_skip_refuses(self):
        with tempfile.TemporaryDirectory() as path:
            self.assertEqual(audio.settings(path), {"backend": "skip"})
            with self.assertRaises(ValueError):
                audio.transcribe(path, "https://example.org/a.mp3")
            with self.assertRaises(ValueError):
                audio.use(path, "whisper", model=str(Path(path) / "missing.bin"))
            model = Path(path) / "ggml-x.bin"
            model.write_text("x")
            self.assertEqual(audio.use(path, "whisper", model=str(model))["backend"], "whisper")
            self.assertEqual(audio.settings(path)["model"], str(model))


if __name__ == "__main__":
    unittest.main()
