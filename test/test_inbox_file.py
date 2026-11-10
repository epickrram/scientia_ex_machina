"""Tests bin/inbox-file, which moves a filed drop into processed/."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

INBOX_FILE = Path(__file__).resolve().parent.parent / "bin" / "inbox-file"


def run(*args):
    return subprocess.run([str(INBOX_FILE), *map(str, args)], capture_output=True, text=True)


class InboxFileTest(unittest.TestCase):
    def setUp(self):
        self.inbox = Path(tempfile.mkdtemp())
        (self.inbox / "processed").mkdir()

    def test_moves_a_drop_into_processed(self):
        drop = self.inbox / "meetings.txt"
        drop.write_text("standup 09:30")
        result = run(drop)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(drop.exists())
        self.assertEqual("standup 09:30", (self.inbox / "processed" / "meetings.txt").read_text())
        self.assertEqual(str(self.inbox / "processed" / "meetings.txt"), result.stdout.strip())

    def test_prefixes_the_received_time_when_the_name_is_taken(self):
        (self.inbox / "processed" / "meetings.txt").write_text("older")
        drop = self.inbox / "meetings.txt"
        drop.write_text("newer")
        os.utime(drop, (1790000000, 1790000000))
        result = run(drop)
        self.assertEqual(0, result.returncode, result.stderr)
        moved = Path(result.stdout.strip())
        self.assertRegex(moved.name, r"^\d{8}-\d{4} meetings\.txt$")
        self.assertEqual("newer", moved.read_text())
        self.assertEqual("older", (self.inbox / "processed" / "meetings.txt").read_text())

    def test_creates_processed_if_missing(self):
        (self.inbox / "processed").rmdir()
        drop = self.inbox / "a.md"
        drop.write_text("x")
        self.assertEqual(0, run(drop).returncode)
        self.assertTrue((self.inbox / "processed" / "a.md").exists())

    def test_rejects_files_already_in_processed(self):
        done = self.inbox / "processed" / "a.md"
        done.write_text("x")
        self.assertNotEqual(0, run(done).returncode)
        self.assertTrue(done.exists())

    def test_rejects_missing_files_and_directories(self):
        self.assertNotEqual(0, run(self.inbox / "missing.md").returncode)
        self.assertNotEqual(0, run(self.inbox / "processed").returncode)


if __name__ == "__main__":
    unittest.main()
