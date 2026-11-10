---
name: journal
description: Update the development journal in the vault from the human's commits across all projects under /src - one page per calendar month, summarising the work by issue, system or area of code. Runs from /start and daily; also use for "update my journal", "what did I do in August", "backfill the journal". Arguments may give "backfill N" (months) or a month (YYYY-MM) to rebuild.
---

# Journal

Pages are `Journal/YYYY-MM.md`, one per calendar month. They record what the human
built, fixed and investigated, summarised from their commits; they are not commit logs.

## Who

Authors live in the frontmatter of `Journal/Settings.md` (`authors:`, a list of exact
`Name <email>` identities). If the file is missing:

1. Run `contributions --identities --since <backfill start> --until <today>`; it matches
   `$SCIENTIA_AUTHORS`, inferred from the system user's name.
2. Ask with a structured multiple-choice question which identities are the human's. Include
   every listed identity as an option with its count and projects, so bots and
   namesakes can be left out; the human can add others as free text.
3. Write `Journal/Settings.md` with `authors:` and `generated_by: scientia`, and one
   line saying the human may edit the list.

Pass each author to `contributions` as `--author '<identity>'`.

## Range

- Months to write: from the month of the latest page's `covered_through` to the current
  month. Each is rebuilt in full from that month's commits, so work items stay coherent
  as the month grows.
- No pages yet, or `backfill N`: also the N months before the current one (default 2).
- A `YYYY-MM` argument rebuilds just that month.

Work one month at a time, oldest first:
`contributions --since <first day> --until <last day or today> --author ...`

## Writing a month page

```
---
month: YYYY-MM
covered_through: YYYY-MM-DD
projects: [<projects with commits>]
generated_by: scientia
tags: [scientia/journal]
---
# <Month YYYY>

## Overview
<3-6 bullets: what the month's work was about, one area per bullet>

## <Work item>
<project> · <issue ids, if any> · <status>

<2-5 lines: what was done and why, in the human's terms>

## Notes
```

- The Overview is a very high-level account of what was worked on: the handful of areas,
  initiatives or problems that took the month, each with where it stands (shipped, in
  progress, investigated, abandoned). Name the work, not the activity: "Moved EBS
  last-look rejections from exceptions to alerts, shipped", not "12 commits to
  liberty". No counts, metrics or comparisons.
- Work items group the month's commits, not days. Group by issue id first; commits with
  no id join the item for the system, area of code or function they touch (a service, a
  bundle, a subsystem, a tool). Pick the grouping that tells the story best: one issue
  spanning two systems is one item; a system touched for five unrelated reasons is five.
  Name items by the work ("EBS last-look rejection alerts", "NY4 CME environment
  scaffolding"), and order them by weight of work, heaviest first.
- Read `git -C /src/<project> show --stat <sha>` or the diff only when the subject does
  not say what the change did or which area it belongs to.
- Keep issue ids, linking `[[...]]` when a vault note covers them. If `creds list` offers
  the issue tracker, resolve an id's title only where the subjects are too terse to
  summarise the item; do not look up every id.
- Automated or bulk commits the human authored (regenerated config, dependency bumps,
  formatting) collapse into one `## Maintenance` item at the end.
- Link project names as `[[Projects/<project>/Overview|<project>]]` when that note exists.
  Never put a wikilink inside backticks: Obsidian renders it as literal text.
- No commit shas or commit lists; the human finds commits from the issue ids and dates.
- `## Notes` belongs to the human: carry its content over unchanged when rebuilding, and
  create it empty on a new page.
- Set `covered_through` to the last day included, and add the month to the `## Journal`
  list in `00 Index.md`.

Report in one line per month touched: month, work items, commits summarised.
