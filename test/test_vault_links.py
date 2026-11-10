"""Tests bin/vault-links, which lists wikilinks with no target in the vault."""

import subprocess
import tempfile
import unittest
from pathlib import Path

VAULT_LINKS = Path(__file__).resolve().parent.parent / "bin" / "vault-links"

NOTE_A = """---
project: liberty
---
# Note A

Resolved: [[Projects/liberty/Overview]], [[overview]], [[Order book.md]],
[[Order book#Depth|depth]], ![[diagram.png]], [[liberty/Overview]], [[#Local heading]].

| Table | [[Overview\\|alias]] |

Not links: `[[In code]]` and ``[[In double code]]``.

```
[[In fence]]
```

Unresolved: [[Scaled value]], [[Order books|the books]], [[Missing thing]],
[[Projects/<project>/Overview]].
"""

NOTE_B = """# Note B

Also [[Missing thing#Section]] and [[Liberty connectors]].
Created by clicking: [[SBE]], [[SBE|encoding]], [[Glossary/Clicked]].
"""


class VaultLinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vault = Path(tempfile.mkdtemp())
        files = {
            "Projects/liberty/Overview.md": "---\naliases: [Liberty connectors]\n---\n# liberty\n",
            "Projects/liberty/ScaledValue.md": "# ScaledValue\n",
            "Glossary/Order book.md": "# Order book\n",
            "Projects/SBE.md": "",
            "Glossary/Clicked.md": "---\ntags: []\n---\n\n",
            "Notes/Orphan stub.md": "  \n",
            "Notes/a.md": NOTE_A,
            "Notes/b.md": NOTE_B,
            "_templates/Topic.md": "[[Projects/<project>/Overview]] [[Template only]]\n",
            ".obsidian/workspace.md": "[[Obsidian only]]\n",
        }
        for path, content in files.items():
            (cls.vault / path).parent.mkdir(parents=True, exist_ok=True)
            (cls.vault / path).write_text(content)
        (cls.vault / "assets").mkdir()
        (cls.vault / "assets" / "diagram.png").write_bytes(b"\x89PNG")

        result = subprocess.run([str(VAULT_LINKS), "--vault", str(cls.vault)],
                                capture_output=True, text=True)
        cls.returncode = result.returncode
        cls.stderr = result.stderr
        cls.output = result.stdout
        cls.lines = result.stdout.splitlines()

    def entry(self, target):
        for index, line in enumerate(self.lines):
            if line.split(" — ")[0] in (target, f"malformed {target}", f"empty {target}"):
                following = self.lines[index + 1] if index + 1 < len(self.lines) else ""
                return line, following if following.startswith("  ") else ""
        self.fail(f"{target} not reported:\n{self.output}")

    def reported_targets(self):
        return [line.split(" — ")[0] for line in self.lines if not line.startswith("  ")]

    def test_exits_cleanly(self):
        self.assertEqual(0, self.returncode, self.stderr)

    def test_reports_exactly_the_unresolved_targets(self):
        self.assertEqual(
            ["Missing thing", "Liberty connectors", "Order books",
             "malformed Projects/<project>/Overview", "Scaled value"],
            [t for t in self.reported_targets() if not t.startswith("empty ")])

    def test_reports_empty_notes_with_the_links_to_them(self):
        line, _ = self.entry("empty Projects/SBE.md")
        self.assertEqual("empty Projects/SBE.md — 2 refs: Notes/b.md", line)

    def test_frontmatter_only_notes_are_empty(self):
        line, _ = self.entry("empty Glossary/Clicked.md")
        self.assertEqual("empty Glossary/Clicked.md — 1 ref: Notes/b.md", line)

    def test_unreferenced_empty_notes_are_reported(self):
        line, _ = self.entry("empty Notes/Orphan stub.md")
        self.assertEqual("empty Notes/Orphan stub.md — 0 refs", line)

    def test_empty_notes_are_not_candidates(self):
        self.assertNotIn("Projects/SBE.md", "\n".join(l for l in self.lines if l.startswith("  ")))

    def test_counts_references_and_lists_sources(self):
        line, _ = self.entry("Missing thing")
        self.assertEqual("Missing thing — 2 refs: Notes/a.md, Notes/b.md", line)

    def test_singular_reference(self):
        line, _ = self.entry("Scaled value")
        self.assertEqual("Scaled value — 1 ref: Notes/a.md", line)

    def test_suggests_close_matches(self):
        self.assertIn("Projects/liberty/ScaledValue.md", self.entry("Scaled value")[1])
        self.assertIn("Glossary/Order book.md", self.entry("Order books")[1])

    def test_suggests_notes_by_alias(self):
        self.assertIn("Projects/liberty/Overview.md", self.entry("Liberty connectors")[1])

    def test_candidates_line_format(self):
        self.assertRegex(self.entry("Order books")[1], r"^  candidates: \S")

    def test_no_candidates_line_without_matches(self):
        self.assertEqual("", self.entry("Missing thing")[1])

    def test_flags_template_placeholders_as_malformed(self):
        line, _ = self.entry("Projects/<project>/Overview")
        self.assertTrue(line.startswith("malformed "))

    def test_ignores_code_spans_and_fences(self):
        self.assertNotIn("In code", self.output)
        self.assertNotIn("In double code", self.output)
        self.assertNotIn("In fence", self.output)

    def test_ignores_templates_and_obsidian_config(self):
        self.assertNotIn("Template only", self.output)
        self.assertNotIn("Obsidian only", self.output)

    def test_prints_nothing_when_all_links_resolve(self):
        vault = Path(tempfile.mkdtemp())
        (vault / "One.md").write_text("[[Two]]\n")
        (vault / "Two.md").write_text("[[One]]\n")
        result = subprocess.run([str(VAULT_LINKS), "--vault", str(vault)], capture_output=True, text=True)
        self.assertEqual(("", 0), (result.stdout, result.returncode))

    def test_rejects_a_missing_vault(self):
        result = subprocess.run([str(VAULT_LINKS), "--vault", "/nonexistent"], capture_output=True)
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
