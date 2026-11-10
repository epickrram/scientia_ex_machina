---
name: survey
description: Map one or more codebases under /src into project overview notes in the vault. Use for "survey", "map this codebase", "what is in /src/x", or as the first step on a project with no Overview note.
---

# Survey

Produce `Projects/<project>/Overview.md` for each project named in the arguments, or for
every directory in `/src` that lacks one. Follow the conventions in AGENTS.md.

## Steps

1. Orient without reading much: `ls`, the README, top-level build files, `git log --oneline -20`,
   and a count of files per extension (`git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn | head`).
2. Establish, citing sources for each:
   - purpose, in two sentences
   - languages and their share of the tree
   - build system, how to build and test, CI config
   - entry points: binaries, services, public API surface, CLI commands
   - top-level modules and what each owns (one line each)
   - external dependencies that shape the design (frameworks, databases, protocols)
   - how the code is configured at runtime
3. Draw one Mermaid diagram of module dependencies or runtime components, whichever
   explains more.
4. List 3–7 candidate topics for `/explain` or `/trace`: the parts a newcomer must
   understand first, ranked by importance. Link each as a `[[Projects/<project>/<topic>]]`
   wikilink even though the note does not exist yet.
5. With several projects, add a `## Relationships` section to each overview naming the
   seams between them (shared schemas, RPC, library use), citing both sides.
6. Update `00 Index.md` and `Questions.md`.

## Overview note shape

```
# <project>
<purpose>
## At a glance        (table: languages, build, test, entry points, size, last commit)
## Structure          (module table + diagram)
## Runtime            (config, processes, external systems)
## Where to start     (ranked topic links)
## Relationships      (multi-project only)
```

Keep it under ~150 lines. The overview is a map, not a tour; depth goes in topic notes.
