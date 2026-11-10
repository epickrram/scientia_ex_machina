---
name: start
description: Start an scientia session - discover credentials, arm the event watcher, refresh the search index, catch up the development journal, and pick up the notes inbox. The launcher runs this first; also use for "restart the watcher" or after the watcher has died.
---

# Start

Do these in order, then tell the human in one line what is running: services available,
journal state, inbox items filed or awaiting context. Then carry on with whatever they
ask; events interleave with other work.

1. Run `creds list` (see "External services" in AGENTS.md).
2. Arm the watcher as a background event stream:
   - command: `events --daily ${SCIENTIA_JOURNAL_AT:-18:00} --index-interval
     ${SCIENTIA_INDEX_INTERVAL:-900}`, plus
     ` --inbox /notes --tick ${SCIENTIA_ASK_INTERVAL:-1800}` if `/notes` exists
   - description: `scientia events`

   If the stream has a time limit, re-arm it on expiry with the same command, without
   comment. Inbox files still unfiled are reported again, so nothing is lost across
   re-arms.
3. Run `/index`, then `/journal` to catch up to today.
4. If `/notes` exists and `Inbox/Needs context.md` lists open items, run the **Chase**
   step of `/inbox` once.

## Routing events

| Event | Action |
|---|---|
| `new <path>` | `/inbox` **On `new <path>`** |
| `tick` | `/inbox` **Chase** |
| `daily` | `/journal` |
| `index` | `/index` |

The watcher exiting on its own (not an expiry) is a failure: say so, and re-arm once.
