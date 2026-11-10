"""Tests bin/vault-index and bin/vault-search, the vault's full-text index."""

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"

NOTES = {
    "Projects/liberty/Overview.md": "---\ntags: [scientia/survey]\naliases: [Liberty connectors]\n---\n"
                                    "# liberty\n\nTrading connectors for FIX venues.\n\n## Market data\n\nESP receivers.\n",
    "Projects/liberty/Scaled value.md": "# ScaledValue\n\nPrices are held as scaled integers; hashing "
                                        "by value fixed L-3516.\n",
    "Glossary/Common/FIX.md": "# FIX\n\nFinancial Information eXchange, a session protocol for trading.\n",
    "Journal/2026-09.md": "# September 2026\n\n## Overview\n\n- Reworked the connectors release pipeline.\n",
    "_templates/Topic.md": "# Template\n\nconnectors placeholder\n",
    ".obsidian/app.md": "connectors\n",
}


def run(tool, vault, *args):
    return subprocess.run([str(BIN / tool), "--vault", str(vault), *args], capture_output=True, text=True)


def hits(result):
    return [line.split(" — ")[0] for line in result.stdout.splitlines() if line and not line.startswith(" ")]


class VaultSearchTest(unittest.TestCase):
    def setUp(self):
        self.vault = Path(tempfile.mkdtemp())
        for path, content in NOTES.items():
            (self.vault / path).parent.mkdir(parents=True, exist_ok=True)
            (self.vault / path).write_text(content)
        self.index_result = run("vault-index", self.vault)

    def search(self, *args):
        result = run("vault-search", self.vault, *args)
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    def test_index_reports_what_it_did(self):
        self.assertEqual(0, self.index_result.returncode, self.index_result.stderr)
        self.assertEqual("indexed 4, removed 0, unchanged 0", self.index_result.stdout.strip())

    def test_stores_the_index_in_a_hidden_vault_folder(self):
        self.assertTrue((self.vault / ".scientia" / "index.sqlite").is_file())

    def test_finds_notes_by_body_text(self):
        self.assertEqual(["Glossary/Common/FIX.md"], hits(self.search("session protocol")))

    def test_ranks_title_matches_first(self):
        self.assertEqual("Glossary/Common/FIX.md", hits(self.search("FIX"))[0])

    def test_title_match_outranks_repeated_body_mentions(self):
        (self.vault / "Topic.md").write_text("# Aeron IPC messaging\n\nPart of liberty. Uses aeron ipc.\n"
                                             + "Publishers claim buffers and write fragments. " * 60)
        (self.vault / "Other.md").write_text("# Flow control\n\n" + "Aeron IPC with aeron:ipc channels. " * 6)
        run("vault-index", self.vault)
        self.assertEqual("Topic.md", hits(self.search("aeron ipc"))[0])

    def test_stems_words(self):
        self.assertIn("Journal/2026-09.md", hits(self.search("rework")))

    def test_searches_frontmatter_tags_and_aliases(self):
        self.assertEqual(["Projects/liberty/Overview.md"], hits(self.search("survey")))
        self.assertIn("Projects/liberty/Overview.md", hits(self.search("Liberty connectors")))

    def test_skips_templates_and_hidden_folders(self):
        found = hits(self.search("connectors"))
        self.assertNotIn("_templates/Topic.md", found)
        self.assertNotIn(".obsidian/app.md", found)

    def test_output_has_title_and_snippet(self):
        lines = self.search("session protocol").stdout.splitlines()
        self.assertEqual("Glossary/Common/FIX.md — FIX", lines[0])
        self.assertIn("[session] [protocol]", lines[1])

    def test_plain_queries_tolerate_fts_syntax_characters(self):
        self.assertEqual(["Projects/liberty/Scaled value.md"], hits(self.search("L-3516")))
        self.search('foo"bar (baz')

    def test_prefix_queries(self):
        self.assertIn("Projects/liberty/Scaled value.md", hits(self.search("hash*")))

    def test_raw_queries_use_fts5_syntax(self):
        found = hits(self.search("--raw", "session OR pipeline"))
        self.assertEqual({"Glossary/Common/FIX.md", "Journal/2026-09.md"}, set(found))

    def test_limit(self):
        self.assertEqual(1, len(hits(self.search("--limit", "1", "connectors"))))

    def test_no_matches_prints_nothing(self):
        self.assertEqual("", self.search("zebra").stdout)

    def test_reindex_is_incremental(self):
        time.sleep(0.01)
        (self.vault / "Glossary/Common/FIX.md").write_text("# FIX\n\nNow about zebras.\n")
        (self.vault / "Journal/2026-09.md").unlink()
        (self.vault / "Glossary/Common/ESP.md").write_text("# ESP\n\nExecutable streaming prices.\n")
        result = run("vault-index", self.vault)
        self.assertEqual("indexed 2, removed 1, unchanged 2", result.stdout.strip())
        self.assertEqual(["Glossary/Common/FIX.md"], hits(self.search("zebras")))
        self.assertEqual([], hits(self.search("pipeline")))
        self.assertEqual(["Glossary/Common/ESP.md"], hits(self.search("streaming")))

    def test_full_rebuild(self):
        self.assertEqual("indexed 4, removed 0, unchanged 0", run("vault-index", self.vault, "--rebuild").stdout.strip())

    def test_search_warns_when_the_index_is_stale(self):
        (self.vault / "New.md").write_text("# New\n")
        result = self.search("connectors")
        self.assertIn("index is 1 change behind", result.stderr)

    def test_search_without_an_index_says_how_to_build_it(self):
        empty = Path(tempfile.mkdtemp())
        result = run("vault-search", empty, "anything")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("vault-index", result.stderr)


if __name__ == "__main__":
    unittest.main()
