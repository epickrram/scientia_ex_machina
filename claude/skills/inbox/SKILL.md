---
name: inbox
description: File terse notes the human drops in the /notes inbox as a vault note (company process, team process, or a project), augment it from the sources, and chase the human for context on notes that cannot be classified. Handles events from the /start watcher; also use for "watch my notes", "process the inbox", "what needs context".
---

# Inbox

The human drops short, terse notes into `/notes`. Turn each into a vault note, filed where
it belongs and enriched from `/src`, then move the original to `/notes/processed/`. Follow
AGENTS.md conventions; the drop is human text and is kept verbatim.

## Start

The watcher is armed by `/start`, which routes its `new` and `tick` events here. Invoked
directly, check `/notes` exists (else say no inbox is configured and stop), then run
`/start` if its `scientia events` stream is not already running.

## On `new <path>`

Handle each file fully before the next. If a vault note already has
`inbox_source: <filename>` for this file, it was filed before a crash; just move it.

1. **Read** the drop. Skip empty files (move them, no note).
2. **Classify** into exactly one:

   | Category | Signals | Note goes to |
   |---|---|---|
   | project | names a project in `/src`, or a module, identifier, service or error that `rg` finds there | `Projects/<project>/Notes/<Title>.md` |
   | team process | how the team works: reviews, releases, on-call, rituals, conventions, tooling | `Process/Team/<Title>.md` |
   | company process | org-wide: policy, HR, compliance, finance, cross-team procedure | `Process/Company/<Title>.md` |
   | unclassified | none of the above with reasonable confidence | `Inbox/<Title>.md` |

   Search before deciding: `rg -il` the note's key nouns across `/src` and existing vault
   notes. A note matching a project's code is a project note even if it sounds like
   process. Prefer unclassified over a guess; a wrong filing is harder to notice than an
   open question.
3. **Title** it with a short noun phrase from the content, not the filename.
4. **Merge or create.** If a note from an earlier drop covers the same subject, append a
   `## <YYYY-MM-DD>` section to it instead. Never append to human-authored notes; put a
   `> [!scientia] Reference` callout in them linking to the new note.
5. **Write** the note:
   ```
   ---
   generated_by: scientia
   category: project | team-process | company-process | unclassified
   project: <project, if any>
   inbox_source: <original filename>
   received: <YYYY-MM-DD HH:MM, from the file mtime>
   status: filed | needs-context
   tags: [scientia/inbox]
   ---
   # <Title>

   > <the drop, verbatim, as a quote>

   <expansion: the terse note restated in full sentences, with abbreviations resolved>

   > [!scientia] Reference
   > <what the sources say: cited code, docs, config, commits>
   ```
   Augment only from evidence: code, READMEs and docs under `/src`, git history,
   existing vault notes, and services in `creds list` (resolve ticket ids, PR numbers
   and issue links the note mentions; see "External services" in AGENTS.md). Link related project overviews, topics and glossary terms. If
   nothing relevant is found, say so in one line rather than padding.
6. **Unclassified or unclear**: set `status: needs-context` and add `context_needed:` to
   the frontmatter with one specific question (e.g. "Is 'the freeze' the release freeze
   or the hiring freeze?"). Add a row to `Inbox/Needs context.md`.
7. **File the original**: `inbox-file /notes/<file>`, as a command of its own. It moves the
   drop into `processed/` without overwriting. Never use `mv`; edits to `/notes` are denied.
8. Update `00 Index.md`. Report in one line: title, category, path.

## On `tick`: Chase

1. Read `Inbox/Needs context.md`. If it has no open items, do nothing and say nothing.
2. Pick up to 3 open items, least recently asked first. Skip items asked in the last
   24 hours unless nothing else is open.
3. Ask with a structured question, one per item. Put the note's title and verbatim drop
   in the question, and offer your 2–3 most likely classifications as options (e.g.
   "Team process", "Project: billing-api") plus "Skip for now". A free-text answer is
   context.
4. For each answer:
   - Classification or context given: re-run steps 2–6 of **On new** with it, move the
     note to its category folder (Obsidian updates wikilinks only when it does the move,
     so fix links to the old path yourself), set `status: filed`, and remove the row.
   - "Skip for now" or no answer: bump `asked` and `last_asked` on the row.
5. If the human answers an open question in normal chat instead, treat it the same way.

## Needs context tracker

`Inbox/Needs context.md` is the human's list of what is waiting on them. Keep it as:

```
# Needs context

| Note | Question | Received | Asked | Last asked |
|---|---|---|---|---|
| [[Inbox/Freeze dates]] | Release freeze or hiring freeze? | 2026-09-24 | 1 | 2026-09-24 |
```

The notes' frontmatter is the source of truth. If the table and the notes disagree,
rebuild the table from notes with `status: needs-context`.
