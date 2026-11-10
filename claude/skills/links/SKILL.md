---
name: links
description: Repair unresolved wikilinks and populate empty notes (created by clicking an unresolved link) in the vault - retarget each to an existing page where one fits, otherwise research its subject in the projects and write the missing note, asking the human when the subject is not certain. Use for "/links", "fix broken links", "fill in missing notes".
---

# Links

Run `vault-links`. It lists every link target with no file, its referencing notes, and
close matches among existing notes; and every `empty` note (blank, or frontmatter only),
with the links that resolve to it. Clicking an unresolved link in Obsidian creates such an
empty note, so an empty note is a missing note: handle it exactly like an unresolved
target. With arguments, handle only the targets named.

Skip targets listed under `## Unresolved links` in `Questions.md`; the human declined them
before. Handle the rest most-referenced first, and write at most 10 new notes per run;
report what is left.

## For each target

1. **Read every reference.** Open each source note at the link and read its paragraph.
   Note the source's `project:` frontmatter or `Projects/<project>/` folder.
2. **Existing page?** Check the candidates, and `rg -il` the link text over the vault's
   file names, titles, headings and `aliases`. If a page covers the same subject beyond
   doubt (case, plural, spelling or path variant; an alias; a renamed note), retarget the
   link and keep what it displays: `[[Real/target|original text]]`, or keep the existing
   `|text`. Done.
3. **Infer the subject.** From the link text and every referencing paragraph, then
   `rg` across `/src/<project>` (types, modules, config keys, docs) and, if `creds list`
   offers the issue tracker, issue titles. The subject is certain only when every
   reference agrees and it maps to exactly one thing in the sources.
4. **Not certain → ask.** Batch up to 4 targets per structured question. For each, quote
   the link and one referencing sentence, and offer the 2–3 subjects you found (e.g.
   "Aeron IPC transport in liberty's market data path", "Aeron's IPC media in general")
   plus "Leave unresolved". A free-text answer is the subject. "Leave unresolved"
   → add `- [[target]]: <what was unclear>` under `## Unresolved links` in `Questions.md`.
5. **Write the note**, following the procedure for its kind:

   | Subject | Procedure |
   |---|---|
   | module, subsystem, mechanism, design pattern | `/explain` |
   | request or data path | `/trace` |
   | term, acronym, name | `/glossary` |
   | process or anything else | short note, AGENTS.md conventions |

   The file must be named so the link resolves: a target with a path is created at that
   path (`Projects/aeron/Media Driver` → `Projects/aeron/Media Driver.md`); a bare name
   goes in the folder the vault layout gives its kind, with the same file name. A glossary
   target without a project folder (`Glossary/SBE`) is written in the tree `/glossary`
   uses, and the link retargeted to it. Link back to the referencing notes' subject where
   it helps, and add the note to `00 Index.md`.

Two targets for one subject (`Glossary/liberty/Libre`, `Projects/liberty/Libre`) are two
notes only if they serve different purposes, definition and deep dive; otherwise write one
and retarget the other.

## Empty notes

The empty file's name is the link target; its referencing paragraphs give the context, as
above. An unreferenced empty note was created by the human: infer its subject from the
file name and folder, and ask if that is not enough.

Populate it in place when its folder is where the vault layout puts that kind of note.
Obsidian creates a note from a bare link (`[[SBE]]`) in its default new-note folder,
which is often wrong: then write the note at its proper path with the same file name,
delete the empty file, and retarget the links if they no longer resolve to the new note.
Keep any frontmatter the empty file had.

## Malformed targets

Template placeholders (`[[Projects/<project>/Overview]]`) in scientia-generated notes:
replace with the intended real target. In human notes: report them, do not edit.

## Report

One line per target: `<target> → retargeted to <page> | wrote <path> | populated <path> | asked |
declined`.
