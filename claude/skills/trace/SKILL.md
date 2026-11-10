---
name: trace
description: Follow a request, event or piece of data through one or more codebases under /src and write it up as a sequence note. Use for "trace", "what happens when", "follow X from A to B", "walk the call path".
---

# Trace

Write `Projects/<project>/Trace - <what>.md` (or under the first project named, for a
cross-project trace). Follow AGENTS.md conventions.

## Steps

1. Pin the start: the entry point where the request or data arrives (HTTP route, CLI
   command, message handler, `main`). Cite it.
2. Follow the path hop by hop. At each hop record the file and line, what changes (data
   shape, thread or process, persistence), and branches that matter. Where dispatch is
   dynamic (interfaces, DI, reflection, config-driven routing), show how you resolved the
   concrete target, or mark the hop **Inferred:**.
3. Stop at the natural end (response sent, row written, message published), or where the
   path leaves `/src`; name the external system.
4. Write the note:
   - Mermaid `sequenceDiagram` of the main path, one participant per component.
   - Numbered steps matching the diagram, each with its citation.
   - **Branches**: errors, retries and alternate paths, briefly.
   - **Observations**: surprising cost, hidden coupling, missing error handling.
5. Link it from the project overview and `00 Index.md`.
