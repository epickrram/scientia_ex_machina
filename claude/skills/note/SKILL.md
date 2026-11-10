---
name: note
description: Record a quick note typed in chat and file it into the vault the same way as an inbox drop — classified, augmented from the sources, or queued for context. Use for "/note <text>", "note that ...", "jot down ...".
---

# Note

The arguments are the note, as terse as the human likes. With no arguments, ask for the
note in one line and wait.

File it with the **On `new <path>`** procedure of the `/inbox` skill, steps 2–6 and 8,
with these differences:

- The drop is the argument text, kept verbatim in the quote block.
- Frontmatter: `inbox_source: chat`, `received:` the current time (`date '+%Y-%m-%d %H:%M'`).
- There is no file to move, so skip step 7.
- Several distinct notes in one message (separate lines or an explicit list) are filed
  separately; one thought spread over several lines is one note.

This works with or without a `/notes` inbox. If the note needs context, ask the question
right away rather than waiting for the next tick, since the human is present; if they
skip it, it goes to `Inbox/Needs context.md` as usual.

Reply in one line per note: title, category, path.
