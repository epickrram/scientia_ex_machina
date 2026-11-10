"""Asserts the sandbox boundaries of bin/scientia."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAUNCHER = REPO / "bin" / "scientia"
DARWIN = sys.platform == "darwin"
# SCIENTIA_SANDBOX=docker runs the suite against the docker backend.
SANDBOX = os.environ.get("SCIENTIA_SANDBOX") or ("seatbelt" if DARWIN else "bwrap")
SEATBELT = SANDBOX == "seatbelt"


def env_value(lines, name):
    """A variable's value in a dry run: bwrap --setenv NAME VALUE, or env NAME=VALUE."""
    if name in lines:
        return lines[lines.index(name) + 1]
    for line in lines:
        if line.startswith(name + "="):
            return line[len(name) + 1:]
    return None


class SandboxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # On macOS the sandbox hides $HOME but not the system temp dir.
        base = Path.home() / ".scientia" if SEATBELT else None
        if base:
            base.mkdir(exist_ok=True)
        cls.work = Path(tempfile.mkdtemp(dir=base))
        cls.src_a = cls.work / "alpha"
        cls.src_b = cls.work / "nested" / "beta"
        cls.vault = cls.work / "vault"
        cls.config = cls.work / "config"
        cls.notes = cls.work / "notes"
        for directory in (cls.src_a, cls.src_b, cls.vault, cls.config, cls.notes):
            directory.mkdir(parents=True)
        (cls.src_a / "main.c").write_text("source")
        git = ["git", "-C", str(cls.src_a), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "main.c"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "initial commit"], check=True)
        (cls.config / "sentinel").write_text("sentinel")
        (cls.notes / "drop.md").write_text("terse")
        cls.creds = cls.work / "creds"
        cls.creds.write_text("ACME_GITHUB=github_pat_secret123\nACME_GITHUB_SERVICE=github\n")
        cls.creds.chmod(0o600)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work)

    def launch(self, *args, env=None):
        return subprocess.run(
            [str(LAUNCHER), "--sandbox", SANDBOX, "--vault", str(self.vault), "--config", str(self.config), *args],
            capture_output=True,
            text=True,
            env={**os.environ, "SCIENTIA_CREDS": str(self.creds), **(env or {})},
        )

    def sandbox(self, command):
        return self.launch("--notes", str(self.notes), "--shell",
                           str(self.src_a), str(self.src_b), "--", "-c", command)

    def assert_succeeds(self, command):
        result = self.sandbox(command)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def assert_fails(self, command):
        self.assertNotEqual(0, self.sandbox(command).returncode)

    def dry_run(self, *args, env=None):
        result = self.launch("--dry-run", *args, str(self.src_a), env=env)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.splitlines()

    def test_sources_are_mounted_by_basename(self):
        self.assert_succeeds('test -f "$SCIENTIA_SRC/alpha/main.c" && test -d "$SCIENTIA_SRC/beta"')

    def test_sources_are_read_only(self):
        self.assert_fails('echo x > "$SCIENTIA_SRC/alpha/new.txt"')

    def test_vault_is_writeable_and_reaches_the_host(self):
        self.assert_succeeds('echo note > "$SCIENTIA_VAULT/note.md"')
        self.assertTrue((self.vault / "note.md").exists())

    def test_cwd_is_the_vault(self):
        self.assert_succeeds('test "$PWD" = "$SCIENTIA_VAULT"')

    def test_config_dir_is_home_claude(self):
        self.assert_succeeds('test "$(cat "$CLAUDE_CONFIG_DIR/sentinel")" = sentinel')
        if not SEATBELT:
            self.assert_succeeds('test "$CLAUDE_CONFIG_DIR" = "$HOME/.claude"')

    def test_repo_config_is_visible_and_read_only(self):
        self.assert_succeeds('test -f "$CLAUDE_CONFIG_DIR/skills/survey/SKILL.md" '
                             '&& test -f "$CLAUDE_CONFIG_DIR/CLAUDE.md"')
        self.assert_succeeds('test -f "$SCIENTIA_HOME/AGENTS.md"')
        self.assert_fails('echo x > "$CLAUDE_CONFIG_DIR/CLAUDE.md"')
        self.assert_fails('echo x > "$SCIENTIA_HOME/new.txt"')

    def test_host_is_hidden(self):
        (self.work / "secret").write_text("secret")
        self.assert_fails(f"cat '{self.work}/secret'")
        self.assert_fails(f"ls '{Path.home()}/.ssh'")
        if not SEATBELT:  # macOS shows ancestors of mounted paths, for realpath
            self.assert_fails(f"test -e '{Path.home()}/Code' || test -e '{Path.home()}/.ssh'")
            self.assert_fails(f"test -e '{self.work}'")

    def test_claude_runs(self):
        self.assert_succeeds("claude --version")

    def test_api_is_reachable(self):
        self.assert_succeeds("curl -sS -o /dev/null https://api.anthropic.com")

    def test_git_reads_read_only_sources(self):
        self.assertIn("initial commit", self.assert_succeeds('git -C "$SCIENTIA_SRC/alpha" log --oneline'))

    def test_notes_are_mounted_and_movable(self):
        self.assert_succeeds('test "$(cat "$SCIENTIA_NOTES_DIR/drop.md")" = terse')
        self.assert_succeeds('cd "$SCIENTIA_NOTES_DIR" && mv drop.md processed/drop.md && mv processed/drop.md drop.md')
        self.assertTrue((self.notes / "processed").is_dir())

    def test_bash_write_guard_runs_in_the_sandbox(self):
        payload = '{"tool_name": "Bash", "tool_input": {"command": "sed -i s/a/b/ x.md"}, "cwd": "/vault"}'
        self.assert_succeeds(f"echo '{payload}' | \"$SCIENTIA_HOME/claude/hooks/bash-write-guard\"; test $? = 2")

    def test_inbox_file_is_on_path(self):
        self.assert_succeeds("command -v inbox-file")

    def test_helpers_are_on_path(self):
        self.assert_succeeds("command -v events && command -v contributions && command -v vault-index "
                             "&& command -v vault-search")

    def test_inbox_watcher_runs_in_the_sandbox(self):
        output = self.assert_succeeds(
            'events --inbox "$SCIENTIA_NOTES_DIR" --interval 0.1 --tick 100 & sleep 1; kill $!')
        self.assertIn("drop.md", output)

    def test_duplicate_basenames_are_rejected(self):
        other = self.work / "other" / "alpha"
        other.mkdir(parents=True)
        self.assertNotEqual(0, self.launch("--shell", str(self.src_a), str(other), "--", "-c", "true").returncode)

    def test_missing_source_is_rejected(self):
        self.assertNotEqual(0, self.launch("--shell", str(self.work / "missing"), "--", "-c", "true").returncode)

    def test_empty_vault_is_seeded(self):
        empty = self.work / "empty-vault"
        empty.mkdir()
        subprocess.run([str(LAUNCHER), "--sandbox", SANDBOX, "--vault", str(empty), "--config", str(self.config),
                        "--shell", str(self.src_a), "--", "-c", "true"], check=True)
        self.assertTrue((empty / "00 Index.md").exists())
        self.assertTrue((empty / "Inbox" / "Needs context.md").exists())

    def test_missing_config_dir_is_created(self):
        new_config = self.work / "new-config"
        subprocess.run([str(LAUNCHER), "--sandbox", SANDBOX, "--vault", str(self.vault), "--config", str(new_config),
                        "--shell", str(self.src_a), "--", "-c", "true"], check=True)
        self.assertTrue(new_config.is_dir())

    def test_missing_vault_and_notes_dirs_are_created(self):
        vault = self.work / "new" / "vault"
        notes = self.work / "new" / "notes"
        subprocess.run([str(LAUNCHER), "--sandbox", SANDBOX, "--vault", str(vault), "--config", str(self.config),
                        "--notes", str(notes), "--shell", str(self.src_a), "--", "-c", "true"],
                       check=True)
        self.assertTrue((vault / "00 Index.md").exists())
        self.assertTrue((notes / "processed").is_dir())

    def test_vault_that_is_a_file_is_rejected(self):
        not_a_dir = self.work / "file-vault"
        not_a_dir.write_text("")
        result = subprocess.run([str(LAUNCHER), "--sandbox", SANDBOX, "--vault", str(not_a_dir), "--config", str(self.config),
                                 "--shell", str(self.src_a), "--", "-c", "true"], capture_output=True)
        self.assertNotEqual(0, result.returncode)

    def test_creds_are_mounted_read_only_at_the_host_path(self):
        expected = self.creds.resolve() if SEATBELT else "$HOME/.config/scientia/creds"
        self.assert_succeeds(f'test "$SCIENTIA_CREDS" = "{expected}"')
        self.assert_succeeds('grep -q ACME_GITHUB_SERVICE=github "$SCIENTIA_CREDS"')
        self.assert_fails('echo x >> "$SCIENTIA_CREDS"')

    def test_creds_helper_lists_services_in_the_sandbox(self):
        self.assertEqual("ACME_GITHUB github\n", self.assert_succeeds("creds list"))

    def test_tokens_are_not_in_the_sandbox_environment(self):
        self.assertNotIn("secret123", self.assert_succeeds("env"))

    def test_creds_run_sets_the_token_in_the_sandbox(self):
        self.assertEqual("github_pat_secret123\n",
                         self.assert_succeeds('creds run ACME_GITHUB -- sh -c \'echo "$GH_TOKEN"\''))

    def test_missing_default_creds_file_is_skipped(self):
        lines = self.dry_run(env={"SCIENTIA_CREDS": str(self.work / "absent")})
        self.assertIsNone(env_value(lines, "SCIENTIA_CREDS"))

    def test_explicit_missing_creds_file_is_rejected(self):
        result = self.launch("--dry-run", "--creds", str(self.work / "absent"), str(self.src_a))
        self.assertNotEqual(0, result.returncode)

    def test_invalid_creds_file_is_rejected(self):
        bad = self.work / "bad-creds"
        bad.write_text("ORPHAN=secret\n")
        bad.chmod(0o600)
        result = self.launch("--dry-run", "--creds", str(bad), str(self.src_a))
        self.assertNotEqual(0, result.returncode)

    def test_claude_starts_on_the_start_skill(self):
        self.assertEqual("/start", self.dry_run()[-1])
        self.assertEqual("/start", self.dry_run("--notes", str(self.notes))[-1])

    def test_no_start_skips_the_start_skill(self):
        self.assertNotIn("/start", self.dry_run("--no-start"))

    def test_env_sets_the_notes_dir(self):
        self.assertIsNotNone(env_value(self.dry_run(env={"SCIENTIA_NOTES": str(self.notes)}), "SCIENTIA_NOTES_DIR"))
        self.assertIsNone(env_value(self.dry_run(env={"SCIENTIA_NOTES": ""}), "SCIENTIA_NOTES_DIR"))

    def test_authors_default_to_the_system_user_name(self):
        user = os.environ["USER"]
        if DARWIN:
            expected = subprocess.run(["id", "-F", user], capture_output=True, text=True).stdout.strip() or user
        else:
            gecos = subprocess.run(["getent", "passwd", user], capture_output=True, text=True).stdout
            expected = gecos.split(":")[4].split(",")[0] or user
        lines = self.dry_run(env={"SCIENTIA_AUTHORS": ""})
        self.assertEqual(expected, env_value(lines, "SCIENTIA_AUTHORS"))

    def test_authors_can_be_overridden(self):
        lines = self.dry_run(env={"SCIENTIA_AUTHORS": "a@x.com,b@y.com"})
        self.assertEqual("a@x.com,b@y.com", env_value(lines, "SCIENTIA_AUTHORS"))

    def test_index_interval_passes_through(self):
        lines = self.dry_run(env={"SCIENTIA_INDEX_INTERVAL": "300"})
        self.assertEqual("300", env_value(lines, "SCIENTIA_INDEX_INTERVAL"))

    def test_journal_time_passes_through(self):
        lines = self.dry_run(env={"SCIENTIA_JOURNAL_AT": "17:30"})
        self.assertEqual("17:30", env_value(lines, "SCIENTIA_JOURNAL_AT"))


if __name__ == "__main__":
    unittest.main()
