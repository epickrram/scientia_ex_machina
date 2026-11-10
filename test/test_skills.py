"""Checks each skill's SKILL.md frontmatter."""

import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parent.parent / "claude" / "skills"


class SkillsTest(unittest.TestCase):
    def test_note_skill_exists(self):
        self.assertTrue((SKILLS / "note" / "SKILL.md").is_file())

    def test_frontmatter_names_match_directories(self):
        for skill in SKILLS.iterdir():
            with self.subTest(skill=skill.name):
                frontmatter = re.match(r"---\n(.*?)\n---\n", (skill / "SKILL.md").read_text(), re.S)
                self.assertIsNotNone(frontmatter)
                self.assertIn(f"name: {skill.name}\n", frontmatter.group(1) + "\n")
                self.assertRegex(frontmatter.group(1), r"(?m)^description: \S")


if __name__ == "__main__":
    unittest.main()
