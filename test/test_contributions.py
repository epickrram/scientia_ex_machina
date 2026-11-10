"""Tests bin/contributions, which lists the human's commits across source repos."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

CONTRIBUTIONS = Path(__file__).resolve().parent.parent / "bin" / "contributions"
ME = "Mark Price <mark@example.com>"
OTHER = "Someone Else <other@example.com>"


def commit(repo, author, date, subject, filename="f.txt"):
    name, email = author[:-1].split(" <")
    (repo / filename).write_text(subject)
    env = {**os.environ, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
           "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
           "GIT_AUTHOR_DATE": f"{date}T12:00:00", "GIT_COMMITTER_DATE": f"{date}T12:00:00"}
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", subject], check=True, env=env)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class ContributionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp())
        alpha = cls.root / "alpha"
        beta = cls.root / "beta"
        (cls.root / "not-a-repo").mkdir()
        for repo in (alpha, beta):
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
        commit(alpha, ME, "2026-08-31", "Before the range")
        commit(alpha, ME, "2026-09-01", "Add parser", "p.txt")
        commit(alpha, OTHER, "2026-09-01", "Someone else's change")
        commit(alpha, ME, "2026-09-02", "Fix parser edge case", "g.txt")
        git(alpha, "checkout", "-q", "-b", "feature")
        commit(alpha, ME, "2026-09-03", "Work on a branch", "h.txt")
        git(alpha, "checkout", "-q", "main")
        git(alpha, "-c", "user.name=Mark Price", "-c", "user.email=mark@example.com",
            "merge", "-q", "--no-ff", "-m", "Merge feature", "feature")
        commit(beta, ME, "2026-09-02", "Beta change")
        commit(beta, ME, "2026-09-10", "After the range")

    def run_contributions(self, *args, env=None):
        return subprocess.run(
            [str(CONTRIBUTIONS), "--root", str(self.root), "--since", "2026-09-01",
             "--until", "2026-09-05", *args],
            capture_output=True, text=True, env={**os.environ, **(env or {})})

    def lines(self, *args, env=None):
        result = self.run_contributions(*args, env=env)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.splitlines()

    def subjects(self, *args, env=None):
        return [line.split(" ", 2)[2].rsplit(" (", 1)[0]
                for line in self.lines(*args, env=env) if line[:1].isdigit()]

    def test_lists_my_commits_in_the_range_oldest_first(self):
        self.assertEqual(["Add parser", "Fix parser edge case", "Work on a branch", "Beta change"],
                         self.subjects("--author", "mark@example.com"))

    def test_groups_commits_under_a_project_heading(self):
        lines = self.lines("--author", "mark@example.com")
        self.assertEqual("## alpha", lines[0])
        self.assertIn("## beta", lines)

    def test_orders_projects_by_name_and_commits_by_date(self):
        lines = self.lines("--author", "mark@example.com")
        alpha = lines[1:lines.index("## beta")]
        self.assertEqual(["2026-09-01", "2026-09-02", "2026-09-03"], [line[:10] for line in alpha if line])

    def test_shows_short_sha_and_change_size(self):
        line = next(l for l in self.lines("--author", "mark@example.com") if "Add parser" in l)
        self.assertRegex(line, r"^2026-09-01 [0-9a-f]{7,} Add parser \(\+1 -0, 1 file\)$")

    def test_excludes_other_authors_and_merges(self):
        subjects = self.subjects("--author", "mark@example.com")
        self.assertNotIn("Someone else's change", subjects)
        self.assertNotIn("Merge feature", subjects)

    def test_matches_any_of_several_authors(self):
        subjects = self.subjects("--author", "nobody@example.com", "--author", "other@example.com")
        self.assertEqual(["Someone else's change"], subjects)

    def test_reads_authors_from_the_environment(self):
        subjects = self.subjects(env={"SCIENTIA_AUTHORS": "nobody@example.com,mark@example.com"})
        self.assertIn("Add parser", subjects)

    def test_prints_nothing_when_there_are_no_commits(self):
        self.assertEqual([], self.lines("--author", "nobody@example.com"))

    def test_matches_authors_case_insensitively(self):
        self.assertIn("Add parser", self.subjects("--author", "mark price"))

    def test_identities_lists_matching_authors_with_counts_and_projects(self):
        self.assertEqual(["4 Mark Price <mark@example.com> (alpha, beta)"],
                         self.lines("--identities", "--author", "mark"))

    def test_identities_without_authors_lists_everyone(self):
        lines = self.lines("--identities", env={"SCIENTIA_AUTHORS": ""})
        self.assertEqual(["4 Mark Price <mark@example.com> (alpha, beta)",
                          "1 Someone Else <other@example.com> (alpha)"], lines)

    def test_requires_an_author(self):
        result = self.run_contributions(env={"SCIENTIA_AUTHORS": ""})
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
