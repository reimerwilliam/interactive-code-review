# Review: PR #<number> (<ticket, or "no ticket">)

- PR: <url>
- Ticket: <url, or "none: the requirements checklist is built from the PR description">
- Related: <linked tickets>
- Branch: `<head>` → `<base>`
- Head at setup: `<sha>`
- Round: <1 / 2 (previous review: <state, date>)>
- Working agreement: <who reads first>. Nothing is posted without explicit approval.
- Standards: <"the skill's defaults" (blocker / suggestion / nit / question, plus `note`; severity tag on its own line after a blank line), or the convention from the overrides or the project>
- Overrides in effect: <one line each, or "none">
- Archive: `review-archive.md` in this folder (completed rounds; created when the first round is archived).

Keep this doc live-only: completed work moves to the archive at the end of each round, or once the doc passes ~250 lines.

## Where we are

- <2–4 plain sentences: current round, PR head, what's blocking>

## To do

1. [ ] <next action, in plain words>

## Decisions

One line each; evidence lives in the Phase 0 section (or the archive).

| # | Topic | Decision |
| - | ----- | -------- |
| Q1 | <topic> | _pending_ |

## Held

- <item in plain words, why it's held, what unblocks it>

## Progress

- [ ] Phase 0: Spec decisions and requirements checklist
- [ ] Comment inventory (always; refresh before Phase 5)
- [ ] Phase 1: Reconcile existing threads (optional; skip if <reason>)
- [ ] Phase 2.1: <layer>
- [ ] Phase 2.2: <layer>
- [ ] Phase 2.n: Tests and docs sweep
- [ ] Phase 3: Cross-cutting (optional)
- [ ] Phase 4: Runtime checks (optional)
- [ ] Phase 5: Publish

## Phase 0: Spec decisions

| # | Question | Decision |
| - | -------- | -------- |
| Q1 | <question> | _pending_ |

### Evidence

- Q1: <facts and file references only>

## Requirements checklist

Source: <ticket, or PR description and linked issues>. Status: `?` not checked, `OK`, `PARTIAL`, `MISSING`, `N/A`. Use the source's own wording; mark requirements that aren't stated directly as _(inferred)_.

| ID | Requirement | Layer(s) | Status | Notes |
| -- | ----------- | -------- | ------ | ----- |
| S1 | <scenario, in the source's words> | 2.x | ? | |
| T1 | <technical rule> | 2.x | ? | |

## Comment inventory

Every existing comment, from any reviewer or bot. Check findings against this before drafting.

| Author | Location | Topic | Status | Layer |
| ------ | -------- | ----- | ------ | ----- |
| <login> | `<path:line>` | <one line> | open / resolved / outdated / pending | 2.x |

## Phase 1: Reconcile existing threads (optional)

Resolved (verified fixed):
- <thread>

Replies (approved wording, in pending review; resolve after submit):
- <thread id>: > <reply>

Kept open, re-evaluated in layers:
- <thread> → 2.x

Left for the author:
- <thread>

Reviewer's pending comments:
- <comment>: <keep / remove before submit>

## Publish list (round <n>)

Still needed before posting:
- [ ] Wording approved
- [ ] Agent-proposed severities confirmed
- [ ] Event and its effect on the reviewer's previous review stated (round 2+)
- [ ] `publish.json` built from the quoted blocks and dry run clean
- [ ] <other blockers to posting>

### Review summary (review body)

> <one or two sentences: thanks, the main takeaway, the event>

### Replies on existing threads

- `<path:line>` (<topic>): **<severity>**
  > <short reply>

### New inline comments

1. **<ID>** `<path:line>` <severity>

### Held for the next round (not posted)

- <IDs and topics>

## Findings

### 2.1 <layer>

Status: <brief given / in triage / triaged>.

Reviewer notes: <one line per note, keyed to F/Q numbers>

**2.1-a <SEVERITY>: <title>** (<checklist IDs>): `<path:line>`

> <comment body following the review standards; only quoted blocks are posted>
>
> [<severity>]

_Reviewer context: <private notes, never posted>_

Facts (one list: what was checked while preparing, and the answers given):
- <fact with file:line>

Open decisions for 2.1:
- <wording / severity / placement still open>

## Meta (PR hygiene)

- <stale description, out-of-scope changes, config documentation>
