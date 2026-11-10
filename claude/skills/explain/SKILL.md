---
name: explain
description: Write a deep-dive topic note on a module, subsystem, pattern or concept in a codebase under /src. Use for "explain X", "how does X work", "write up the Y module".
---

# Explain

Write `Projects/<project>/<Topic>.md` on the topic in the arguments. If the project has no
`Overview.md`, run the survey steps for it first, briefly. Follow AGENTS.md conventions and
the shape of `_templates/Topic.md`.

## Steps

1. Find the code: `rg` for the names involved, then read the core files fully rather than
   skimming many.
2. Check history for the why: `git log --follow` and `git blame` on the central file often
   name the problem the design solves.
3. Write the note:
   - **Summary**: what it is and why it exists, 3–5 lines.
   - **How it works**: the mechanism, in the order a reader needs it. Cite every step.
     Include a Mermaid diagram when there are more than three moving parts.
   - **Key files**: table of path and role.
   - **Gotchas**: invariants, surprising behaviour, known sharp edges, with evidence.
   - **Open questions**: what you could not determine, and what would settle it.
4. Link the note from the project overview's "Where to start" list, from `00 Index.md`, and
   to any glossary terms it uses.

If the human already has a note on this topic, do not write a competing one; use `/annotate`
on theirs instead and say so.
