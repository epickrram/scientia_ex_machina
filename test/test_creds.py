"""Tests bin/creds, the reader for the scientia credentials file."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

CREDS = Path(__file__).resolve().parent.parent / "bin" / "creds"
TOKEN = "github_pat_secret123"

VALID = f"""# fine-grained tokens
ACME_GITHUB={TOKEN}
ACME_GITHUB_SERVICE=github

TRACKER=lin_api_secret456
TRACKER_SERVICE=linear
WIKI=wiki_secret789
WIKI_SERVICE=confluence
"""


def write_creds(content, mode=0o600):
    path = Path(tempfile.mkdtemp()) / "creds"
    path.write_text(content)
    path.chmod(mode)
    return path


def creds(path, *args):
    return subprocess.run([str(CREDS), "--file", str(path), *args], capture_output=True, text=True)


class CheckTest(unittest.TestCase):
    def assert_rejected(self, content, mode=0o600):
        result = creds(write_creds(content, mode), "check")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("secret", result.stderr, "errors must not echo token values")

    def test_accepts_a_valid_file(self):
        result = creds(write_creds(VALID), "check")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_a_token_without_a_service(self):
        self.assert_rejected("ACME_GITHUB=secret\n")

    def test_rejects_a_service_without_a_token(self):
        self.assert_rejected("ACME_GITHUB_SERVICE=github\n")

    def test_rejects_a_malformed_line(self):
        self.assert_rejected("ACME_GITHUB secret\nACME_GITHUB_SERVICE=github\n")

    def test_rejects_a_lowercase_name(self):
        self.assert_rejected("acme=secret\nacme_SERVICE=github\n")

    def test_rejects_duplicate_names(self):
        self.assert_rejected("A=secret\nA=secret2\nA_SERVICE=github\n")

    def test_rejects_an_empty_value(self):
        self.assert_rejected("A=\nA_SERVICE=github\n")

    def test_rejects_a_file_others_can_read(self):
        self.assert_rejected(VALID, mode=0o644)

    def test_rejects_a_missing_file(self):
        self.assertNotEqual(0, creds(Path("/nonexistent/creds"), "check").returncode)


class ListTest(unittest.TestCase):
    def test_lists_names_and_services_without_values(self):
        result = creds(write_creds(VALID), "list")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["ACME_GITHUB github", "TRACKER linear", "WIKI confluence"],
                         result.stdout.splitlines())
        self.assertNotIn("secret", result.stdout)


class RunTest(unittest.TestCase):
    def setUp(self):
        self.path = write_creds(VALID)

    def env_of(self, name):
        result = creds(self.path, "run", name, "--", "env")
        self.assertEqual(0, result.returncode, result.stderr)
        return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

    def test_sets_the_service_variables_for_github(self):
        env = self.env_of("ACME_GITHUB")
        self.assertEqual(TOKEN, env["GH_TOKEN"])
        self.assertEqual(TOKEN, env["GITHUB_TOKEN"])

    def test_sets_the_service_variable_for_linear(self):
        self.assertEqual("lin_api_secret456", self.env_of("TRACKER")["LINEAR_API_KEY"])

    def test_always_sets_the_token_under_its_own_name(self):
        self.assertEqual("wiki_secret789", self.env_of("WIKI")["WIKI"])

    def test_sets_only_the_named_token(self):
        self.assertNotIn("TRACKER", self.env_of("ACME_GITHUB"))

    def test_passes_the_exit_code_through(self):
        self.assertEqual(3, creds(self.path, "run", "WIKI", "--", "sh", "-c", "exit 3").returncode)

    def test_rejects_an_unknown_name(self):
        self.assertNotEqual(0, creds(self.path, "run", "NOPE", "--", "true").returncode)

    def test_reads_the_file_from_the_environment(self):
        result = subprocess.run([str(CREDS), "list"], capture_output=True, text=True,
                                env={**os.environ, "SCIENTIA_CREDS": str(self.path)})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("TRACKER linear", result.stdout)


if __name__ == "__main__":
    unittest.main()
