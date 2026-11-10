"""Checks claude/settings.json against rules Claude Code warns about."""

import json
import unittest
from pathlib import Path

SETTINGS = Path(__file__).resolve().parent.parent / "claude" / "settings.json"


class SettingsTest(unittest.TestCase):
    def test_path_rules_use_edit_not_write(self):
        permissions = json.loads(SETTINGS.read_text())["permissions"]
        rules = permissions["allow"] + permissions["deny"]
        self.assertEqual([], [r for r in rules if r.startswith("Write(")])

    def test_filing_a_drop_is_allowed_without_mv(self):
        permissions = json.loads(SETTINGS.read_text())["permissions"]
        self.assertIn("Bash(inbox-file /notes/:*)", permissions["allow"])
        self.assertEqual([], [r for r in permissions["allow"] if r.startswith("Bash(mv ")])

    def test_shell_file_editors_are_denied(self):
        deny = json.loads(SETTINGS.read_text())["permissions"]["deny"]
        for rule in ["Bash(sed -i:*)", "Bash(sed --in-place:*)", "Bash(python:*)",
                     "Bash(python3:*)", "Bash(perl:*)", "Bash(awk -i:*)"]:
            self.assertIn(rule, deny)

    def test_bash_write_guard_hook_is_configured(self):
        hooks = json.loads(SETTINGS.read_text())["hooks"]["PreToolUse"]
        bash = [h for entry in hooks if entry["matcher"] == "Bash" for h in entry["hooks"]]
        self.assertEqual(["/opt/scientia/claude/hooks/bash-write-guard"], [h["command"] for h in bash])
        repo_path = SETTINGS.parent / "hooks" / "bash-write-guard"
        self.assertTrue(repo_path.is_file() and repo_path.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
