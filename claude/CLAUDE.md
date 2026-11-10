@/opt/scientia/AGENTS.md

# Claude Code harness

AGENTS.md and the skills are written for any coding agent. In Claude Code:

| Generic term | Claude Code |
|---|---|
| background event stream | the Monitor tool: `timeout_ms: 1800000` (the maximum), `description` as given; re-arm on expiry |
| structured question | AskUserQuestion; the free-text answer is "Other"; `multiSelect: true` for multiple choice |
| file-editing tools | Read, Edit, Write |
