---
name: index
description: Refresh the vault's full-text search index (SQLite FTS5 at /vault/.scientia/index.sqlite). Runs from /start and on the watcher's periodic index event; also use for "reindex the vault", "rebuild the search index".
---

# Index

Run `vault-index`. It indexes new and changed notes and drops removed ones, comparing file
size and modification time, so a run with nothing changed is cheap. With the argument
`rebuild`, or if `vault-index` fails on a damaged database, run `vault-index --rebuild`.

Say nothing when a periodic run reports `indexed 0, removed 0`. Otherwise report its
output line. On failure, report the error once; do not retry in a loop.
