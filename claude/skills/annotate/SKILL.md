---
name: annotate
description: Check a human-written vault note against the source and add verification, corrections, references and gaps as scientia callouts, without touching the human's text. Use for "annotate", "check my notes", "fact-check this note", "fill in references".
---

# Annotate

Target: the note named in the arguments, or the most recently modified note in the vault
not tagged `scientia/*`. The human's text is sacrosanct; see "Human-authored notes" in
AGENTS.md.

## Steps

1. Read the note. Remove any `> [!scientia]` callouts from a previous pass; they are
   regenerated.
2. For each factual claim about the code, find the source that confirms or refutes it.
3. After the paragraph containing the claim, add at most one callout:
   - `Verified` with the citation, when the claim holds and a reference adds value.
     Skip it for trivial claims; do not carpet the note.
   - `Correction` when the source disagrees. Quote the code; state what it actually does.
   - `Reference` for a file, test or commit the human would want and did not cite.
   - `Gap` for something adjacent and important the note does not cover.
   - `Question` when the note's claim cannot be settled from the source.
4. If the note has no frontmatter `project:`, add only that key; change no other frontmatter.
5. Add wikilinks only inside your callouts, never in the human's text.
6. Finish with a one-line tally in chat: verified, corrected, gaps, questions.

Density guide: a callout per two or three paragraphs is typical. If you find yourself
adding one per sentence, keep only the corrections and the biggest gaps.
