"""Asserts the macOS (sandbox-exec) launch of bin/scientia, from its dry run on any platform."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAUNCHER = REPO / "bin" / "scientia"


class DarwinLaunchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp()).resolve()
        cls.src = cls.work / "alpha"
        cls.src.mkdir()
        cls.vault = cls.work / "vault"
        cls.config = cls.work / "config"
        cls.notes = cls.work / "notes"
        cls.creds = cls.work / "creds"
        cls.creds.write_text("ACME_GITHUB=github_pat_secret123\nACME_GITHUB_SERVICE=github\n")
        cls.creds.chmod(0o600)
        result = subprocess.run(
            [str(LAUNCHER), "--dry-run", "--sandbox", "seatbelt", "--vault", str(cls.vault), "--config", str(cls.config),
             "--notes", str(cls.notes), str(cls.src)],
            capture_output=True, text=True,
            env={**os.environ, "SCIENTIA_PLATFORM": "Darwin", "SCIENTIA_CREDS": str(cls.creds)})
        assert result.returncode == 0, result.stderr
        # One argument per line, but the profile and system prompt span several.
        cls.out = result.stdout
        cls.lines = cls.out.splitlines()
        cls.profile = cls.out.split("\n-p\n")[1].split("\nclaude\n")[0]
        cls.prompt = cls.out.split("\n--append-system-prompt\n")[1].split("\n/start\n")[0]
        cls.env = {}
        for arg in cls.lines[2:cls.lines.index("sandbox-exec")]:
            name, _, value = arg.partition("=")
            cls.env[name] = value
        cls.run_dir = Path(cls.env["SCIENTIA_SRC"]).parent

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work)

    def test_runs_claude_under_sandbox_exec_with_a_clear_environment(self):
        self.assertEqual(["env", "-i"], self.lines[:2])
        self.assertTrue(self.profile.startswith("(version 1)"))
        self.assertEqual("/start", self.lines[-1])

    def test_paths_are_host_paths(self):
        self.assertEqual(str(self.vault), self.env["SCIENTIA_VAULT"])
        self.assertEqual(str(self.notes), self.env["SCIENTIA_NOTES_DIR"])
        self.assertEqual(str(REPO), self.env["SCIENTIA_HOME"])
        self.assertEqual(str(self.config), self.env["CLAUDE_CONFIG_DIR"])
        self.assertEqual(str(self.creds), self.env["SCIENTIA_CREDS"])
        self.assertEqual(str(self.run_dir / "tmp"), self.env["SCIENTIA_SCRATCH"])
        self.assertTrue(self.env["TMPDIR"].startswith(self.env["SCIENTIA_SCRATCH"]))

    def test_system_prompt_maps_logical_paths(self):
        prompt = self.prompt
        self.assertIn(f"/vault = {self.vault}", prompt)
        self.assertIn(f"/notes = {self.notes}", prompt)
        self.assertIn(f"/src = {self.run_dir / 'src'}", prompt)

    def test_profile_hides_home_and_limits_writes(self):
        self.assertIn(f'(deny file-read* (subpath "{Path.home().resolve()}")', self.profile)
        self.assertIn('(deny file-write* (subpath "/"))', self.profile)
        writable = self.profile.split('(deny file-write* (subpath "/"))')[1].split("\n")[1]
        for path in (self.vault, self.notes, self.config, self.run_dir / "tmp"):
            self.assertIn(f'(subpath "{path}")', writable)
        self.assertNotIn(f'(subpath "{self.src}")', writable)

    def test_profile_keeps_sources_repo_and_config_read_only(self):
        denied = self.profile.rstrip().split("\n")[-1]
        self.assertTrue(denied.startswith("(deny file-write*"))
        for rule in (f'(subpath "{self.src}")', f'(subpath "{REPO}")', f'(subpath "{self.vault}/_templates")',
                     f'(literal "{self.config}/settings.json")', f'(literal "{self.config}/CLAUDE.md")'):
            self.assertIn(rule, denied)

    def test_settings_are_rendered_with_host_paths(self):
        settings = json.loads((self.config / "settings.json").read_text())
        allow, deny = settings["permissions"]["allow"], settings["permissions"]["deny"]
        self.assertIn(f"Edit(/{self.vault}/**)", allow)
        self.assertIn(f"Bash(inbox-file {self.notes}/:*)", allow)
        self.assertIn(f"Edit(/{self.run_dir}/src/**)", deny)
        self.assertIn(f"Read(/{self.creds})", deny)
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertEqual(f"{REPO}/claude/hooks/bash-write-guard", hook)
        self.assertNotIn("/opt/scientia", (self.config / "settings.json").read_text())

    def test_claude_md_imports_agents_md_from_the_repo(self):
        self.assertEqual(f"@{REPO}/AGENTS.md", (self.config / "CLAUDE.md").read_text().splitlines()[0])
        self.assertEqual(REPO / "claude" / "skills", (self.config / "skills").resolve())


if __name__ == "__main__":
    unittest.main()
