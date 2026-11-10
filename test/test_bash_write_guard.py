"""Tests claude/hooks/bash-write-guard, the PreToolUse hook that stops Bash writing files."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "claude" / "hooks" / "bash-write-guard"


class BashWriteGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The vault is itself under /tmp here, so a separate dir stands in for the scratch root.
        cls.vault = Path(tempfile.mkdtemp())
        cls.scratch = Path(tempfile.mkdtemp())
        (cls.vault / "stub.md").write_text("")
        (cls.vault / "frontmatter-only.md").write_text("---\ntags: []\n---\n\n")
        (cls.vault / "note.md").write_text("# Real content\n")

    def run_guard(self, command, tool="Bash"):
        payload = {"tool_name": tool, "tool_input": {"command": command}, "cwd": str(self.vault)}
        return subprocess.run([str(GUARD)], input=json.dumps(payload), capture_output=True, text=True,
                              env={**os.environ, "SCIENTIA_SCRATCH": str(self.scratch)})

    def assert_allowed(self, command):
        command = command.replace("SCRATCH", str(self.scratch))
        result = self.run_guard(command)
        self.assertEqual(0, result.returncode, f"{command!r} blocked: {result.stderr}")

    def assert_blocked(self, command):
        result = self.run_guard(command)
        self.assertEqual(2, result.returncode, f"{command!r} allowed")
        self.assertIn("Edit", result.stderr, "the refusal should point at the file-editing tools")

    def test_allows_read_only_commands(self):
        for command in [
            "rg -n 'python' /src/liberty",
            "git -C /src/liberty log --oneline -5",
            "ls /vault",
            "cat note.md | grep Real",
            "sed -n 1,5p note.md",
            "awk '{print $1}' note.md",
            "find /src -name '*.md'",
            "wc -l note.md && head -3 note.md",
        ]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_allows_scientia_helpers(self):
        for command in [
            "inbox-file /notes/drop.md",
            "events --inbox /notes --tick 1800",
            "contributions --since 2026-09-01 --until 2026-09-30",
            "vault-links",
            "creds list",
            "creds run LINEAR -- sh -c 'curl -sS https://api.linear.app/graphql "
            "-H \"Authorization: $LINEAR_API_KEY\" -d @-' <<< '{\"query\":\"{ viewer { name } }\"}'",
        ]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_allows_harmless_redirection(self):
        for command in ["make 2>&1", "rg x /src > /dev/null", "echo x > SCRATCH/scratch", "ls 2>/dev/null"]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_allows_writes_under_tmp(self):
        for command in ["mkdir -p SCRATCH/work", "cp note.md SCRATCH/copy.md", "tee SCRATCH/out < note.md"]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_allows_deleting_empty_notes(self):
        self.assert_allowed("rm stub.md")
        self.assert_allowed("rm -f SCRATCH/x frontmatter-only.md")

    def test_blocks_in_place_editors(self):
        for command in [
            "sed -i 's/a/b/' note.md",
            "sed -ni 's/a/b/p' note.md",
            "sed --in-place 's/a/b/' note.md",
            "sed -i.bak 's/a/b/' note.md",
            "awk -i inplace '{print}' note.md",
            "perl -pi -e 's/a/b/' note.md",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_blocks_interpreters_however_invoked(self):
        for command in [
            "python3 -c 'print(1)'",
            "python fix.py",
            "/usr/bin/python3 fix.py",
            "env python3 fix.py",
            "ruby -e 'puts 1'",
            "node -e '1'",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_blocks_redirection_into_files(self):
        for command in [
            "echo x > note.md",
            "echo x >> /vault/other.md",
            "cat <<'EOF' > new.md\ncontent\nEOF",
            "printf x >| note.md",
            "ls &> listing.md",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_blocks_file_writing_commands(self):
        for command in [
            "tee note.md < /dev/null",
            "cp /tmp/a note.md",
            "mv note.md renamed.md",
            "touch new.md",
            "truncate -s 0 note.md",
            "ln -s note.md link.md",
            "rm note.md",
            "rm -rf Projects",
            "curl -sS -o page.md https://example.com",
            "wget https://example.com/page.md",
            "dd if=/dev/zero of=note.md",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_looks_inside_chains_wrappers_and_substitutions(self):
        for command in [
            "cd /vault && sed -i 's/a/b/' note.md",
            "rg -l x | xargs sed -i 's/a/b/'",
            "find /vault -name '*.md' -exec sed -i 's/a/b/' {} \\;",
            "find /vault -name '*.md' -delete",
            "bash -c \"sed -i 's/a/b/' note.md\"",
            "sh -c 'echo x > note.md'",
            "echo $(python3 -c 'print(1)')",
            "echo `python3 -c 1`",
            "timeout 5 python3 x.py",
            "creds run LINEAR -- sh -c 'curl -o note.md https://example.com'",
            "FOO=1 python3 x.py",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_blocks_what_it_cannot_parse(self):
        self.assert_blocked("echo 'unterminated")

    def test_ignores_other_tools(self):
        self.assertEqual(0, self.run_guard("sed -i x note.md", tool="Read").returncode)


if __name__ == "__main__":
    unittest.main()
