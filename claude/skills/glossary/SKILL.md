---
name: glossary
description: Extract domain and project-specific terms from codebases under /src and vault notes into linked Glossary notes, grouped by project. Use for "glossary", "define the terms", "what does X mean in this codebase".
---

# Glossary

Create or update one note per term, filed by the projects that use it:

```
Glossary/<project>/<Term>.md   used by one project
Glossary/Common/<Term>.md      same meaning in two or more projects
```

A term meaning different things in different projects gets a note in each project's
folder, and each notes the other meaning. A project-folder term later found with the same
meaning in another project moves to `Common/`; update every link to it.

With a term in the arguments, define that term; otherwise harvest terms from the named
project, or from the vault's unresolved wikilinks. Flat `Glossary/<Term>.md` notes from
before this layout are moved into the tree the first time the skill runs, with their links.

## Selecting terms

Include domain vocabulary, project-coined names and overloaded words with a local meaning.
Skip general programming terms unless the project uses them unusually. Aim for the 10–30
terms a newcomer trips over, not an exhaustive list.

## Term note shape

```
---
generated_by: scientia
project: [<projects using it>]
aliases: [<abbreviations, code identifiers>]
tags: [scientia/glossary]
---
# <Term>
<one-sentence definition in this codebase's sense>

<where it appears: the main type or module, cited>
<how it differs from the general meaning, if it does>

Related: [[Glossary/<folder>/<Other term>|Other term]], [[Projects/<project>/<Topic>]]
```

Put code identifiers (`OrderBook`, `txn_id`) in `aliases` so search and link
autocomplete find the note. Obsidian does not resolve `[[alias]]` links by alias: link as
`[[Glossary/<folder>/<Term>|alias]]`. Always link with the full path, since the same
term name may exist in several folders. When a term already has a note, extend it; never
overwrite human text in it. List terms under `## Glossary` in `00 Index.md`, one
subheading per folder: `### Common` first, then projects alphabetically.
