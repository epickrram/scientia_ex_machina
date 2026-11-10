"""Asserts the docker launch of bin/scientia from its dry run, with a stub docker on PATH.

The full sandbox suite runs against docker with SCIENTIA_SANDBOX=docker.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAUNCHER = REPO / "bin" / "scientia"


class DockerLaunchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp()).resolve()
        cls.src = cls.work / "alpha"
        cls.src.mkdir()
        cls.vault = cls.work / "vault"
        cls.config = cls.work / "config"
        cls.notes = cls.work / "notes"
        cls.bin = cls.work / "bin"
        cls.bin.mkdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work)

    def dry_run(self, *args, security_options="[name=seccomp,profile=builtin]", env=None):
        docker = self.bin / "docker"
        docker.write_text(f"#!/bin/sh\necho '{security_options}'\n")
        docker.chmod(0o755)
        result = subprocess.run(
            [str(LAUNCHER), "--dry-run", "--sandbox", "docker", "--vault", str(self.vault),
             "--config", str(self.config), *args, str(self.src)],
            capture_output=True, text=True,
            env={**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin", "SCIENTIA_CREDS": str(self.work / "absent"),
                 **(env or {})})
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.splitlines()

    def test_runs_unprivileged_as_the_invoking_user(self):
        lines = self.dry_run()
        self.assertEqual(["docker", "run"], lines[:2])
        for flag in ("--read-only", "--init", "--rm"):
            self.assertIn(flag, lines)
        self.assertEqual("ALL", lines[lines.index("--cap-drop") + 1])
        self.assertEqual("no-new-privileges", lines[lines.index("--security-opt") + 1])
        self.assertEqual(f"{os.getuid()}:{os.getgid()}", lines[lines.index("--user") + 1])

    def test_rootless_docker_keeps_container_root(self):
        self.assertNotIn("--user", self.dry_run(security_options="[name=rootless name=seccomp]"))

    def test_mounts_logical_paths(self):
        lines = self.dry_run("--notes", str(self.notes))
        mounts = [lines[i + 1] for i, arg in enumerate(lines) if arg == "--mount"]
        self.assertIn(f"type=bind,src={self.src},dst=/src/alpha,readonly", mounts)
        self.assertIn(f"type=bind,src={self.vault},dst=/vault", mounts)
        self.assertIn(f"type=bind,src={self.notes},dst=/notes", mounts)
        self.assertIn(f"type=bind,src={REPO},dst=/opt/scientia,readonly", mounts)
        self.assertIn(f"type=bind,src={REPO}/claude/settings.json,dst=/home/scientia/.claude/settings.json,readonly",
                      mounts)
        self.assertEqual("/vault", lines[lines.index("--workdir") + 1])

    def test_environment_uses_logical_paths(self):
        lines = self.dry_run("--notes", str(self.notes))
        env = [lines[i + 1] for i, arg in enumerate(lines) if arg == "-e"]
        for entry in ("HOME=/home/scientia", "CLAUDE_CONFIG_DIR=/home/scientia/.claude", "SCIENTIA_SRC=/src",
                      "SCIENTIA_VAULT=/vault", "SCIENTIA_NOTES_DIR=/notes", "SCIENTIA_HOME=/opt/scientia"):
            self.assertIn(entry, env)

    def test_image_is_tagged_by_dockerfile_checksum(self):
        lines = self.dry_run()
        self.assertTrue(lines[lines.index("claude") - 1].startswith("scientia:"))
        self.assertEqual("/start", lines[-1])
        self.assertIn("my/image", self.dry_run(env={"SCIENTIA_IMAGE": "my/image"}))

    def test_config_mountpoints_are_created(self):
        self.dry_run()
        self.assertTrue((self.config / "skills").is_dir())
        self.assertTrue((self.config / "settings.json").is_file())


if __name__ == "__main__":
    unittest.main()
