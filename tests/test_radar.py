import contextlib
import copy
import io
import importlib.util
import tempfile
import unittest
import unittest.mock
import subprocess
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("radar", Path(__file__).resolve().parents[1] / "skills/farfield/scripts/radar.py")
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)
REPO = Path(__file__).resolve().parents[1]


class RadarTest(unittest.TestCase):
    def test_only_mine_excludes_future_catalog_entries_but_keeps_explicit_selections(self):
        local = {"include_curated": False, "overrides": {"chosen": {"enabled": True}},
                 "add": [{"id": "local:mine", "enabled": True}]}
        pack = {"id": "test", "version": "2", "sources": [
            {"id": "chosen", "enabled": True}, {"id": "new", "enabled": True}]}
        resolved = radar.resolve_sources(pack, local)
        self.assertEqual([s["id"] for s in resolved["sources"] if s["enabled"]],
                         ["chosen", "local:mine"])
        self.assertIn("Picked from the curated list (1)", radar.render_sources(resolved))
        self.assertTrue(pack["sources"][1]["enabled"])

    def test_init_preserves_user_edits(self):
        with tempfile.TemporaryDirectory() as path:
            radar.init_workspace(path, remember=False)
            profile = Path(path) / "me.md"
            profile.write_text("My edited project")
            radar.init_workspace(path, remember=False)
            self.assertEqual(profile.read_text(), "My edited project")

    def test_mute_survives_upstream_updates_and_reappearance(self):
        local = {"overrides": {"podcast": {"enabled": False}}}
        pack = {"id": "friends", "version": "2", "sources": [
            {"id": "podcast", "url": "https://example.org/new-feed", "enabled": True},
            {"id": "new-source", "enabled": True},
        ]}
        result = radar.resolve_sources(pack, local)
        self.assertFalse(result["sources"][0]["enabled"])
        self.assertEqual(result["sources"][0]["url"], "https://example.org/new-feed")
        self.assertTrue(result["sources"][1]["enabled"])
        removed = copy.deepcopy(pack)
        removed["sources"] = []
        self.assertEqual(radar.resolve_sources(removed, local)["inactive_override_ids"], ["podcast"])
        self.assertFalse(radar.resolve_sources(pack, local)["sources"][0]["enabled"])
        self.assertTrue(pack["sources"][0]["enabled"])

    def test_local_additions_preserved_and_collisions_rejected(self):
        pack = {"id": "friends", "version": "1", "sources": []}
        local = {"add": [{"id": "local:journal", "enabled": True}]}
        self.assertEqual(radar.resolve_sources(pack, local)["sources"], local["add"])
        pack["sources"] = local["add"]
        with self.assertRaises(ValueError):
            radar.resolve_sources(pack, local)

    def test_changed_quote_fails(self):
        pack = radar.read_json(REPO / "examples/evidence.json")
        radar.check_evidence(pack)
        pack["ideas"][0]["quotes"][0]["quote"] = "Fabricated replacement"
        warnings, failures = radar.check_evidence(pack)
        self.assertEqual(len(failures), 1)
        self.assertIn("not verbatim", failures[0])

    def test_legacy_pack_reports_missing_provenance(self):
        pack = radar.read_json(REPO / "examples/evidence.json")
        quote = pack["ideas"][0]["quotes"][0]
        del quote["excerpt"]
        del quote["origin_id"]
        warnings, failures = radar.check_evidence(pack)
        self.assertEqual(failures, [])
        self.assertTrue(any("no source excerpt" in item for item in warnings))
        self.assertTrue(any("independence unverified" in item for item in warnings))

    def test_add_mute_and_readable_list(self):
        with tempfile.TemporaryDirectory() as path:
            radar.init_workspace(path, remember=False)
            ident = radar.add_source(path, "https://example.org/feed.xml", "Example Journal")
            self.assertEqual(ident, "local:example-journal")
            with self.assertRaises(ValueError):
                radar.add_source(path, "https://example.org/feed.xml/", "Same thing again")
            first = radar.read_json(radar.CATALOG)["sources"][0]["id"]
            radar.set_enabled(path, first, False)
            text = (Path(path) / "sources.md").read_text()
            yours, muted = text.split("## Yours")[1].split("## Muted")
            self.assertIn("Example Journal", yours)
            self.assertIn(f"`{first}`", muted)
            self.assertNotIn(f"`{first}`", text.split("## Yours")[0])
            radar.set_enabled(path, first, True)
            self.assertIn("None.", (Path(path) / "sources.md").read_text().split("## Muted")[1])
            with self.assertRaises(ValueError):
                radar.set_enabled(path, "no-such-id", False)

    def test_quote_is_checked_against_the_fetched_page(self):
        with tempfile.TemporaryDirectory() as path:
            page = "<html><script>var x='We said nothing'</script><p>He said \u201cthe tide&nbsp;sets the\n roster\u201d today.</p></html>"
            with unittest.mock.patch.object(radar, "download", return_value=("text/html", page.encode())):
                raw = radar.fetch(path, "https://example.org/a")["raw"]
            pack = radar.read_json(REPO / "examples/evidence.json")
            quote = pack["ideas"][0]["quotes"][0]
            quote.update(quote='"the tide sets the roster"', excerpt='He said "the tide sets the roster" today.', raw=raw)
            warnings, failures = radar.check_evidence(pack)
            self.assertEqual(failures, [])
            self.assertFalse(any("not checked against the page" in w for w in warnings))
            quote.update(quote="We said nothing", excerpt="We said nothing")
            self.assertIn("not in the fetched page", radar.check_evidence(pack)[1][0])

    def test_quote_ending_at_a_link_and_curly_quotes_still_match(self):
        with tempfile.TemporaryDirectory() as path:
            page = "<p>Build a separate judge for each <a href='/x'>failure mode</a>. It’s cheaper.</p>"
            with unittest.mock.patch.object(radar, "download", return_value=("text/html", page.encode())):
                raw = radar.fetch(path, "https://example.org/b")["raw"]
            pack = radar.read_json(REPO / "examples/evidence.json")
            pack["ideas"][0]["quotes"][0].update(
                quote="Build a separate judge for each failure mode. It's cheaper.",
                excerpt="Build a separate judge for each failure mode. It’s cheaper.", raw=raw)
            self.assertEqual(radar.check_evidence(pack)[1], [])

    def test_one_bad_quote_does_not_sink_the_others(self):
        pack = radar.read_json(REPO / "examples/evidence.json")
        good = dict(pack["ideas"][0]["quotes"][0])
        pack["ideas"][0]["quotes"] = [good, dict(good, quote="Invented words")]
        warnings, failures = radar.check_evidence(pack)
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith(pack["ideas"][0]["id"] + " quote 2"))

    def test_pdf_text_is_saved_and_quotes_check_against_it(self):
        with tempfile.TemporaryDirectory() as path:
            with unittest.mock.patch.object(radar, "download", return_value=("application/pdf", b"%PDF-1.7")), \
                    unittest.mock.patch.object(radar, "pdf_text", return_value="Results\nWe find that evaluation\ndrift is real.\n"):
                result = radar.fetch(path, "https://arxiv.org/pdf/2601.01234v2")
            self.assertEqual(result["via"], "pdf")
            pack = radar.read_json(REPO / "examples/evidence.json")
            pack["ideas"][0]["quotes"][0].update(quote="We find that evaluation drift is real.",
                                                 excerpt="We find that evaluation drift is real.", raw=result["raw"])
            self.assertEqual(radar.check_evidence(pack)[1], [])

    def test_real_pdf_extraction_when_a_reader_exists(self):
        if not (radar.shutil.which("pdftotext") or radar.sys.platform == "darwin"):
            self.skipTest("no PDF reader on this machine")
        pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj "
               b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 10 50 Td (Quoted words here) Tj ET\nendstream endobj "
               b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF")
        self.assertIn("Quoted words here", radar.pdf_text(pdf))

    def test_same_site_needs_force(self):
        with tempfile.TemporaryDirectory() as path:
            radar.init_workspace(path, remember=False)
            with self.assertRaises(ValueError) as caught:
                radar.add_source(path, "https://www.hamel.dev/", "Hamel")
            self.assertIn("hamel-husain", str(caught.exception))
            self.assertTrue(radar.add_source(path, "https://hamel.dev/notes.xml", "Hamel notes", force=True))

    def test_items_reports_partial_feed_coverage(self):
        feed = """<?xml version="1.0"?><rss><channel>
          <item><title>New</title><link>https://ex.org/new</link><pubDate>Mon, 16 Nov 2026 10:00:00 GMT</pubDate></item>
          <item><title>Mid</title><link>https://ex.org/mid</link><pubDate>Mon, 09 Nov 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        atom = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>A</title>
          <link rel="alternate" href="https://at.org/a"/><published>2026-11-10T00:00:00Z</published></entry>
          <entry><title>Old</title><link href="https://at.org/old"/><updated>2026-09-01T00:00:00Z</updated></entry></feed>"""
        with tempfile.TemporaryDirectory() as path:
            radar.init_workspace(path, remember=False)
            radar.set_source_mode(path, "only-mine")
            radar.add_source(path, "https://ex.org/feed", "Ex")
            radar.add_source(path, "https://at.org/atom", "At")
            pages = {"https://ex.org/feed": feed, "https://at.org/atom": atom}
            with unittest.mock.patch.object(radar, "http", side_effect=lambda url, **k: pages[url]):
                out = radar.list_items(path, radar.date(2026, 11, 1))
            by_id = {s["id"]: s for s in out["sources"]}
            self.assertEqual(by_id["local:ex"]["status"], "partial")
            self.assertEqual(by_id["local:ex"]["count"], 2)
            self.assertEqual(by_id["local:at"]["status"], "complete")
            saved = radar.read_json(out["saved"])
            at = next(s for s in saved["sources"] if s["id"] == "local:at")
            self.assertEqual([i["url"] for i in at["items"]], ["https://at.org/a"])

    def test_keys_come_from_a_private_file_and_are_never_printed(self):
        with tempfile.TemporaryDirectory() as path:
            old = radar.KEYFILE
            radar.KEYFILE = Path(path) / "env"
            try:
                with unittest.mock.patch.dict("os.environ", {}, clear=True):
                    self.assertEqual(radar.keys(), {})
                    radar.KEYFILE.write_text("# note\nEXA_API_KEY='abc'\nOTHER=zzz\n")
                    self.assertEqual(radar.keys(), {"EXA_API_KEY": "abc"})
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        radar.main(["keys"])
                    self.assertNotIn("abc", out.getvalue())
                    self.assertIn('"EXA_API_KEY": true', out.getvalue())
            finally:
                radar.KEYFILE = old

    def test_pointer_remembers_workspace(self):
        with tempfile.TemporaryDirectory() as path:
            old = radar.POINTER
            radar.POINTER = Path(path) / "config" / "workspace"
            try:
                self.assertIsNone(radar.where())
                root = radar.init_workspace(Path(path) / "ws")
                self.assertEqual(radar.where(), root)
            finally:
                radar.POINTER = old

    def test_skill_folder_is_self_contained(self):
        skill = REPO / "skills/farfield"
        for name in ("SKILL.md", "skill.json", "catalog.json", "templates/me.md", "templates/feed.json",
                     "templates/sources.local.json", "references/start.md", "references/sources.md",
                     "references/memory.md", "scripts/library.py", "scripts/social.py", "references/reading.md", "references/context.md", "references/social.md",
                     "references/schedule.md", "references/updating.md", "references/audio.md", "scripts/feed.py",
                     "scripts/audio.py", "stt.json"):
            self.assertTrue((skill / name).exists(), name)
        self.assertEqual(radar.version()["version"], radar.read_json(REPO / ".claude-plugin/plugin.json")["version"])


if __name__ == "__main__":
    unittest.main()


class ReadingListTest(unittest.TestCase):
    def test_sources_md_matches_catalog(self):
        result = subprocess.run([sys.executable, str(REPO / "tools" / "sources_md.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_source_has_a_home_and_a_reason(self):
        for source in radar.read_json(radar.CATALOG)["sources"]:
            self.assertTrue(source.get("home", "").startswith("https://"), source["id"])
            self.assertTrue(source.get("why"), source["id"])


class VersionTest(unittest.TestCase):
    def test_versions_match_and_changelog_names_it(self):
        plugin = radar.read_json(REPO / ".claude-plugin" / "plugin.json")["version"]
        self.assertEqual(plugin, radar.read_json(radar.SKILL / "skill.json")["version"])
        self.assertEqual(plugin, radar.read_json(radar.CATALOG)["version"])
        self.assertIn(f"## {plugin}", (REPO / "CHANGELOG.md").read_text())


class ReaderFallbackTest(unittest.TestCase):
    def test_blocked_page_is_read_through_the_reader_and_quotes_still_match(self):
        markdown = ("Title: X\n\nMarkdown Content:\n## Scaling\n\nWe built **Pando**, a new [backend](https://x.org) for "
                    "Git repositories, without interrupting any engineering work. " + "More words here. " * 20)
        def fake(url, data=None, headers=None, limit=None):
            if url.startswith(radar.READER):
                return "text/plain", markdown.encode()
            raise radar.urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        with tempfile.TemporaryDirectory() as path:
            with unittest.mock.patch.object(radar, "download", side_effect=fake):
                result = radar.fetch(path, "https://openai.com/index/scaling-git")
            self.assertEqual(result["via"], "reader")
            pack = radar.read_json(REPO / "examples/evidence.json")
            pack["ideas"][0]["quotes"][0].update(
                quote="We built Pando, a new backend for Git repositories, without interrupting any engineering work.",
                excerpt="We built Pando, a new backend for Git repositories, without interrupting any engineering work.",
                raw=result["raw"])
            self.assertEqual(radar.check_evidence(pack)[1], [])
