import copy
import functools
import json
import tempfile
import threading
import unittest
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "farfield" / "scripts"))
import feed  # noqa: E402


def example():
    return {"as_of": "2026-11-16", "sample": True, "private_profile": "PRIVATE SENTINEL",
            "ideas": [{"id": "sample", "name": "Sample idea", "summary": "Fictional test evidence.",
                       "sources": ["feed:a", "feed:b"], "heat": 2, "families": 2,
                       "personal_relevance": "PRIVATE SENTINEL",
                       "quotes": [{"quote": "A complete evidence quote.",
                                   "excerpt": "Context. A complete evidence quote. More context.",
                                   "source": "feed:a", "doc_id": "a:1", "pid": "a:1#0",
                                   "date": "2026-11-15", "url": "https://example.org/evidence",
                                   "private_note": "PRIVATE SENTINEL"}]}]}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FeedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.public = self.root / "public"
        self.manifest = feed.stage(example(), self.public)
        self.cache = self.root / "cache"
        handler = functools.partial(QuietHandler, directory=str(self.public))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f"http://127.0.0.1:{self.server.server_port}/latest.json"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_http_download_without_clone_or_private_fields(self):
        result = feed.fetch(self.url, self.cache, today=date(2026, 11, 17))
        self.assertEqual(result["status"], "downloaded")
        self.assertFalse(result["stale"])
        self.assertTrue(result["evidence"]["sample"])
        self.assertNotIn("PRIVATE SENTINEL", json.dumps(result))
        self.assertEqual(result["sha256"], self.manifest["sha256"])

    def test_broken_refresh_keeps_last_good_feed(self):
        feed.fetch(self.url, self.cache)
        pointer = (self.cache / "current.json").read_bytes()
        (self.public / self.manifest["path"]).write_text("corrupted")
        result = feed.fetch(self.url, self.cache)
        self.assertEqual(result["status"], "cached")
        self.assertIn("checksum mismatch", result["warning"])
        self.assertEqual((self.cache / "current.json").read_bytes(), pointer)

    def test_offline_staleness_and_whole_idea_mute(self):
        feed.fetch(self.url, self.cache)
        result = feed.fetch(self.url, self.cache, offline=True, muted=["feed:b"], today=date(2027, 1, 1))
        self.assertTrue(result["stale"])
        self.assertEqual(result["excluded_ideas"], 1)
        self.assertEqual(result["evidence"]["ideas"], [])
        self.assertEqual(len(feed.fetch(self.url, self.cache, offline=True)["evidence"]["ideas"]), 1)

    def test_cache_not_reused_for_different_feed(self):
        feed.fetch(self.url, self.cache)
        with self.assertRaisesRegex(ValueError, "another URL"):
            feed.fetch(self.url + "?other", self.cache, offline=True)

    def test_manifest_cannot_escape_object_directory(self):
        bad = {**self.manifest, "path": "../../private.json"}
        with self.assertRaisesRegex(ValueError, "unsafe"):
            feed.check_manifest(bad)

    def test_no_cache_fails_instead_of_empty_success(self):
        with self.assertRaises(OSError):
            feed.fetch(self.url, self.cache, offline=True)

    def test_rejects_fabricated_quote_and_future_evidence(self):
        bad = example()
        bad["ideas"][0]["quotes"][0]["quote"] += " Invented tail."
        with self.assertRaisesRegex(ValueError, "verbatim"):
            feed.stage(bad, self.public)
        bad = example()
        bad["ideas"][0]["quotes"][0]["date"] = "2027-01-01"
        with self.assertRaisesRegex(ValueError, "cutoff"):
            feed.stage(bad, self.public)

    def test_failed_stage_does_not_change_pointer(self):
        pointer = (self.public / "latest.json").read_bytes()
        bad = example()
        del bad["ideas"][0]["quotes"][0]["excerpt"]
        with self.assertRaises(ValueError):
            feed.stage(bad, self.public)
        self.assertEqual((self.public / "latest.json").read_bytes(), pointer)

    def test_manifest_cutoff_and_download_size_are_checked(self):
        raw = (self.public / self.manifest["path"]).read_bytes()
        with self.assertRaisesRegex(ValueError, "cutoff"):
            feed.checked_object({**self.manifest, "as_of": "2026-11-17"}, raw)
        with patch.object(feed, "MAX_BYTES", 20):
            with self.assertRaisesRegex(ValueError, "size limit"):
                feed.read_url(self.url)


if __name__ == "__main__":
    unittest.main()
