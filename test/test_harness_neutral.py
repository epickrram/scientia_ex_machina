"""Generic files must not assume one agent harness; harness specifics live in claude/."""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARNESS_SPECIFIC = re.compile(
    r"claude|anthropic|AskUserQuestion|Monitor tool|\bMonitor\b|timeout_ms|TaskStop|"
    r"Read, Edit|Edit tool|Write tool", re.I)


def generic_files():
    yield REPO / "AGENTS.md"
    yield from sorted((REPO / "claude" / "skills").glob("*/SKILL.md"))
    yield from sorted(p for p in (REPO / "bin").iterdir() if p.name != "scientia")
    yield from sorted((REPO / "vault-template").rglob("*.md"))


class HarnessNeutralTest(unittest.TestCase):
    def test_generic_files_name_no_harness(self):
        for path in generic_files():
            with self.subTest(path=str(path.relative_to(REPO))):
                hits = [f"{n}: {line.strip()}" for n, line in enumerate(path.read_text().splitlines(), 1)
                        if HARNESS_SPECIFIC.search(line)]
                self.assertEqual([], hits)

    def test_claude_adapter_maps_the_generic_terms(self):
        adapter = (REPO / "claude" / "CLAUDE.md").read_text()
        for term in ("background event stream", "structured question", "Monitor", "AskUserQuestion"):
            self.assertIn(term, adapter)


if __name__ == "__main__":
    unittest.main()
