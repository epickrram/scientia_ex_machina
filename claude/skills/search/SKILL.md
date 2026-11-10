---
name: search
description: Full-text search of the vault's notes, ranked, with snippets. Use for "/search <words>", "find notes about X", "where did I write about Y", and before answering a question the vault may already cover.
---

# Search

Run `vault-search <query>`. Plain words must all match, `word*` matches a prefix, and
punctuation is literal (`L-3516` works as typed). For OR, NEAR or exact phrases, use
`vault-search --raw '<FTS5 query>'`, e.g. `--raw 'freeze OR embargo'`,
`--raw '"release freeze"'`. `--limit N` changes the default of 10.

If it warns that the index is behind, run `vault-index` and search again. If it finds
nothing, try fewer words, prefixes or synonyms once before reporting no match.

Report the matches as a list, best first: `[[<path without .md>|<title>]]` and the
snippet, trimmed to the relevant words. Do not open the notes unless the human asked a
question that needs their content; then answer from them, citing the notes.
