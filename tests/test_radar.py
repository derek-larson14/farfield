import contextlib
import copy
import io
import importlib.util
import tempfile
import unittest
import unittest.mock
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
        self.assertIn("Selected from catalog (1)", radar.render_sources(resolved))
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
        with self.assertRaises(ValueError):
            radar.check_evidence(pack)

    def test_legacy_pack_reports_missing_provenance(self):
        pack = radar.read_json(REPO / "examples/evidence.json")
        quote = pack["ideas"][0]["quotes"][0]
        del quote["excerpt"]
        del quote["origin_id"]
        warnings = radar.check_evidence(pack)
        self.assertTrue(any("original quote unverified" in item for item in warnings))
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
            with unittest.mock.patch.object(radar, "http", return_value=page):
                raw = radar.fetch(path, "https://example.org/a")["raw"]
            pack = radar.read_json(REPO / "examples/evidence.json")
            quote = pack["ideas"][0]["quotes"][0]
            quote.update(quote='"the tide sets the roster"', excerpt='He said "the tide sets the roster" today.', raw=raw)
            self.assertFalse(any("not checked against the page" in w for w in radar.check_evidence(pack)))
            quote.update(quote="We said nothing", excerpt="We said nothing")
            with self.assertRaises(ValueError):
                radar.check_evidence(pack)

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
                     "references/schedule.md", "references/updating.md", "references/audio.md", "scripts/feed.py",
                     "scripts/audio.py", "stt.json"):
            self.assertTrue((skill / name).exists(), name)
        self.assertEqual(radar.version()["version"], radar.read_json(REPO / ".claude-plugin/plugin.json")["version"])


if __name__ == "__main__":
    unittest.main()
