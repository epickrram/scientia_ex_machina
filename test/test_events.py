"""Black-box tests for the event stream of bin/events."""

import datetime
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

EVENTS = Path(__file__).resolve().parent.parent / "bin" / "events"


def clock_in(seconds):
    return (datetime.datetime.now() + datetime.timedelta(seconds=seconds)).strftime("%H:%M:%S")


def collect(args, seconds):
    process = subprocess.Popen([str(EVENTS), *args], stdout=subprocess.PIPE, text=True)
    time.sleep(seconds)
    process.terminate()
    return process.communicate()[0].splitlines()


class InboxEventsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inbox = Path(tempfile.mkdtemp()) / "notes"
        (cls.inbox / "processed").mkdir(parents=True)
        (cls.inbox / "before.md").write_text("existing")
        (cls.inbox / "processed" / "old.md").write_text("done")
        (cls.inbox / ".hidden").write_text("hidden")
        (cls.inbox / "draft.md.swp").write_text("swap")
        (cls.inbox / "draft.md~").write_text("backup")

        watcher = subprocess.Popen(
            [str(EVENTS), "--inbox", str(cls.inbox), "--interval", "0.2", "--tick", "1"],
            stdout=subprocess.PIPE,
            text=True,
        )
        time.sleep(1)
        (cls.inbox / "later.txt").write_text("arrived later\n")
        time.sleep(1)
        with open(cls.inbox / "later.txt", "a") as later:
            later.write("appended\n")
        (cls.inbox / "before.md").rename(cls.inbox / "processed" / "before.md")
        time.sleep(0.5)
        (cls.inbox / "before.md").write_text("same name, new drop")
        time.sleep(1.5)
        watcher.terminate()
        cls.events = watcher.communicate()[0].splitlines()

    def test_existing_files_are_reported_at_startup(self):
        self.assertIn(f"new {self.inbox}/before.md", self.events)

    def test_new_files_are_reported(self):
        self.assertIn(f"new {self.inbox}/later.txt", self.events)

    def test_ticks_are_emitted(self):
        self.assertIn("tick", self.events)

    def test_a_file_is_reported_once(self):
        self.assertEqual(1, self.events.count(f"new {self.inbox}/later.txt"))

    def test_a_refiled_name_is_reported_again(self):
        self.assertEqual(2, self.events.count(f"new {self.inbox}/before.md"))

    def test_subdirectories_are_ignored(self):
        self.assertFalse([e for e in self.events if "processed" in e])

    def test_dotfiles_and_editor_temp_files_are_ignored(self):
        self.assertFalse([e for e in self.events if "hidden" in e or "draft" in e])

    def test_missing_inbox_is_rejected(self):
        result = subprocess.run([str(EVENTS), "--inbox", "/nonexistent/inbox"], capture_output=True)
        self.assertNotEqual(0, result.returncode)


class DailyEventsTest(unittest.TestCase):
    def test_daily_fires_when_the_time_passes(self):
        events = collect(["--interval", "0.2", "--daily", clock_in(2)], 3.5)
        self.assertEqual(["daily"], events)

    def test_daily_does_not_fire_at_startup_for_a_time_already_past(self):
        self.assertEqual([], collect(["--interval", "0.2", "--daily", clock_in(-5)], 1))

    def test_accepts_hours_and_minutes(self):
        self.assertEqual([], collect(["--interval", "0.2", "--daily", "00:00"], 0.5))

    def test_rejects_a_malformed_time(self):
        result = subprocess.run([str(EVENTS), "--daily", "6pm"], capture_output=True)
        self.assertNotEqual(0, result.returncode)

    def test_index_fires_every_interval(self):
        events = collect(["--interval", "0.2", "--index-interval", "1"], 2.5)
        self.assertEqual(["index", "index"], events)

    def test_runs_without_an_inbox(self):
        self.assertEqual([], collect(["--interval", "0.2"], 0.5))


if __name__ == "__main__":
    unittest.main()
