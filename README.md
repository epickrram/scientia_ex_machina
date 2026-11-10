# scientia

Skills and conventions for a coding agent that studies codebases and keeps notes on them
in an Obsidian vault, plus a sandboxing launcher (bubblewrap, Docker or macOS `sandbox-exec`). Sources are mounted read-only, the vault
writeable, and the agent runs with its own config dir, so it never sees your real home.

`AGENTS.md`, `claude/skills/` and `bin/` are harness-neutral. The launcher and the rest of
`claude/` (`CLAUDE.md` maps the generic terms to Claude Code tools, `settings.json`) target
Claude Code, the only harness supported so far.

## Requirements

One sandbox, none needing root:

| Sandbox | Needs |
|---|---|
| `bwrap` | Linux, bubblewrap ≥ 0.6, Claude Code installed natively (`~/.local/bin/claude`) |
| `seatbelt` | macOS, Xcode Command Line Tools (git, python3), Claude Code installed natively |
| `docker` | Docker (rootless, Desktop, or a docker-group user); Claude Code is installed in the image |

## Usage

```bash
ln -s ~/Code/scientia/bin/scientia ~/.local/bin/scientia
scientia --vault ~/vaults/acme --notes ~/inbox/acme ~/src/acme-api ~/src/acme-web
```

| Option | Env default | Effect |
|---|---|---|
| `--vault DIR` | `$PWD` | Obsidian vault, mounted at `/vault` |
| `--config DIR` | `SCIENTIA_CONFIG`, else `~/.config/scientia/claude` | Claude config, mounted as `~/.claude` |
| `--notes DIR` | `SCIENTIA_NOTES`, else none | notes inbox, mounted at `/notes` |
| `--no-start` | | don't start the agent on `/start` (watcher, journal, inbox) |
| `--creds FILE` | `SCIENTIA_CREDS`, else `~/.config/scientia/creds` if present | access tokens, mounted read-only |
| `--shell` | | run bash instead of claude |
| `--sandbox S` | `SCIENTIA_SANDBOX`, else `auto` | `bwrap`, `seatbelt` or `docker`; `auto`: bwrap on Linux (docker if bwrap is missing), docker on macOS if the daemon answers, else seatbelt |
| `--dry-run` | | print the sandbox command and exit |
| `-- ARGS` | | passed to claude (or bash) |

| Inside the sandbox | Host |
|---|---|
| `/src/<basename>` (ro) | each source dir argument |
| `/vault` (rw, cwd) | `--vault`, default `$PWD`; seeded from `vault-template/` if empty |
| `~/.claude` (rw) | `--config`, default `${SCIENTIA_CONFIG:-~/.config/scientia/claude}` |
| `~/.claude/{CLAUDE.md,settings.json,skills}` (ro) | this repo's `claude/` |
| `/notes` (rw) | `--notes`, default `$SCIENTIA_NOTES`; optional notes inbox |
| `/opt/scientia` (ro) | this repo |

Vault, config and notes dirs are created if missing; source dirs must exist.

Bash cannot write files outside `/tmp`: `claude/settings.json` denies `sed -i`, `python`,
`perl` and `awk -i`, and a `PreToolUse` hook (`claude/hooks/bash-write-guard`) refuses
redirection, interpreters and file-writing commands anywhere in a command line, subagents
included. Notes change only through the agent's file-editing tools.

The first run needs `/login` inside the sandbox; credentials stay in the config dir. The
empty `CLAUDE.md`, `settings.json` and `skills/` in the config dir are bwrap mountpoints.

## macOS

`sandbox-exec` (Seatbelt) restricts access but cannot remap paths, so the agent sees host
paths. Each run gets `~/.scientia/run/<pid>/` with `src/<basename>` symlinks to the sources
and `tmp/` as scratch, removed on exit. The launcher passes the logical-to-host path map as
`--append-system-prompt` and exports it as `SCIENTIA_SRC`, `SCIENTIA_VAULT`,
`SCIENTIA_NOTES_DIR`, `SCIENTIA_HOME`, `SCIENTIA_SCRATCH` (set on Linux too, to the logical
paths). The config dir's `CLAUDE.md` and `settings.json` are rendered from `claude/` with
those paths and `skills` is a symlink to the repo; all three are read-only to the agent.

Profile: `$HOME`, `/Volumes` and `/tmp` are unreadable except the repo, vault, notes,
config, sources, Claude install and creds file; writes are refused except to vault, notes,
config, the run's `tmp/`, `/dev` and the per-user Darwin temp and cache dirs. `/var/folders`
stays readable. Apple marks `sandbox-exec` deprecated but ships it and has no userland
replacement; Claude Code uses it for its own sandbox.

Unverified on a Mac: whether a separate `CLAUDE_CONFIG_DIR` gets its own Keychain login,
and whether Claude follows the `skills` symlink.

## Docker

`docker/Dockerfile` (Debian, git, python3, ripgrep, Claude Code) is built on first use and
tagged `scientia:<checksum>`, so editing it rebuilds; `SCIENTIA_IMAGE` overrides the image.
Mounts match bwrap, with `HOME=/home/scientia`. The container runs as the invoking uid:gid
(container root under rootless Docker, which maps to the invoking user) with `--read-only`,
`--cap-drop ALL` and `no-new-privileges`. Claude credentials live in the config dir, not the
macOS Keychain. Membership of the `docker` group is itself root-equivalent on the host;
prefer rootless Docker or Docker Desktop. `SCIENTIA_SANDBOX=docker` runs
`test/test_sandbox.py` against it.

## Notes inbox

The coding agent starts on `/start`, which arms `bin/events`; with a notes dir configured it
watches that too. Drop terse notes there; each is filed into the vault as a
project, team-process or company-process note, augmented from the sources, and the
original moved to `processed/`. Notes it cannot classify go to `Inbox/` and are listed in
`Inbox/Needs context.md`; the agent asks about them every `SCIENTIA_ASK_INTERVAL` seconds
(default 1800).

## Development journal

`/journal` keeps `Journal/YYYY-MM.md` in the vault: one page per month summarising your
commits across every project in `/src` (all branches, author date), grouped by issue, system or area of code. It runs on
start, catching up from where it last stopped, and daily at `SCIENTIA_JOURNAL_AT`
(default 18:00). The first run backfills the current month and the two before it, and asks
which git identities are yours: candidates match `SCIENTIA_AUTHORS`, which defaults to
your system full name (else login name). The answer is kept in `Journal/Settings.md`.

## Credentials

To let the agent use external services, put fine-grained, read-only tokens in
`~/.config/scientia/creds` (mode 600), each with a line naming its service:

```
ACME_GITHUB=github_pat_...
ACME_GITHUB_SERVICE=github
TRACKER=lin_api_...
TRACKER_SERVICE=linear
```

The launcher validates the file (`bin/creds check`) and mounts it read-only at the same
path. Tokens are not exported into the sandbox; the agent runs `creds list` to see names
and services, and `creds run NAME -- gh ...` to use one. `creds run` sets `NAME` plus the
service's usual variables (github: `GH_TOKEN`, `GITHUB_TOKEN`; gitlab, linear, jira, slack
likewise; see `SERVICE_VARIABLES` in `bin/creds`). Each `creds run` asks for approval,
because it can wrap any command. The token's scope is the real limit, so keep it narrow.

## Skills

| Skill | Output |
|---|---|
| `/survey [project]` | `Projects/<project>/Overview.md`: structure, build, entry points, where to start |
| `/explain <topic>` | topic deep dive with cited source |
| `/trace <flow>` | sequence note following a request or data path |
| `/annotate [note]` | `[!scientia]` callouts verifying and extending your note; your text is untouched |
| `/glossary [term]` | `Glossary/<project>/<Term>.md` notes; `Glossary/Common/` for shared terms |
| `/search <words>` | ranked full-text search of the vault, with snippets (`--raw` for FTS5 syntax) |
| `/index [rebuild]` | refreshes the search index, `.scientia/index.sqlite` in the vault; runs on start and every `SCIENTIA_INDEX_INTERVAL` seconds (default 900) |
| `/links [target...]` | repairs unresolved wikilinks and populates empty notes (e.g. created by clicking a link): retargets to existing notes, or researches and writes the missing note, asking when unsure |
| `/start` | session start: credentials, event watcher, journal catch-up, inbox |
| `/journal [backfill N \| YYYY-MM]` | updates the monthly development journal |
| `/inbox` | files `/notes` drops, chases missing context |
| `/note <text>` | files a note typed in chat, same as an inbox drop |

Conventions the agent follows are in `AGENTS.md`.

## Tests

```bash
python3 -m unittest discover -s test && shellcheck bin/scientia
```
