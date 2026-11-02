---
name: interactive-code-review
description: >-
  Runs a structured, human-in-the-loop code review of a large or high-risk PR where
  the reviewer stays involved in every step: requirements decisions, reconciling
  existing threads, layer-by-layer review (reviewer reads first, agent second),
  joint triage, and a single approved publish to a pending GitHub review. Works in
  any repo; project-specific behaviour comes from optional overrides in
  ai-plans/code-review/overrides/. Use when the user invokes /interactive-code-review
  or asks to review a PR together, step by step, without the agent doing the review alone.
disable-model-invocation: true
---

# Interactive Code Review

Status: **draft**. Refine after each use.

The agent is the reviewer's assistant, not the reviewer. It gathers evidence, writes briefs, answers questions, gives an independent second read, and drafts comments in the reviewer's voice. The reviewer decides scope, severity, wording, and what gets posted.

**Asking the reviewer:** where this skill says *ask*, use a structured multiple-choice question if your tool has one (for example `AskQuestion` in Cursor or `AskUserQuestion` in Claude Code). Otherwise ask in plain text with numbered options.

## Where things live

All review files live under `ai-plans/code-review/` at the project root (the root of the git repository):

```text
ai-plans/code-review/
  overrides/              optional: the reviewer's customisations (see Overrides)
    OVERRIDES.md
  PR-<number>/
    review.md             the working doc
    review-archive.md     completed rounds (created by the first archive)
    publish.json          posting input (Phase 5)
  RETRO.md                optional: retros across reviews
```

Whether `ai-plans/` is committed or git-ignored is the reviewer's choice. Don't add it to `.gitignore` or `.git/info/exclude`, and never stage or commit review files yourself. If the folder isn't ignored, mention once during setup that the review files will show up in `git status`.

## Overrides

The reviewer can change anything about this skill for a project, without editing the skill, through `ai-plans/code-review/overrides/`. If the folder doesn't exist, the skill runs with its defaults.

- **`OVERRIDES.md`** holds free-form instructions. It can add, change or remove any part of this skill: ground rules, review standards, phases, where the review files live, the posting flow. It also holds project facts the skill needs, under the headings in [overrides-template.md](overrides-template.md).
- **Replacement files:** a file in `overrides/` with the same relative path as a file bundled with this skill replaces the bundled one. That applies to `review-doc-template.md`, `github-pending-review.md` and `scripts/post-pending-review.py`. Any other files in `overrides/` are references that `OVERRIDES.md` can point to.
- **Precedence:** the reviewer's instructions in the chat come first, then the overrides, then this skill. The project's own agent instructions (`AGENTS.md`, `CLAUDE.md`, rules files) decide what counts as a problem in the code; the overrides decide how the review is run.
- **When to read them:** at setup, and at the start of every new chat that picks up an existing review. Record a one-line summary of each override in effect at the top of the review doc, so the reviewer can see what's active.
- If an override is ambiguous, or seems to conflict with a ground rule by accident, ask instead of guessing.

The `overrides/` folder always stays at `ai-plans/code-review/overrides/`, even if the overrides move the review folders somewhere else.

### Creating overrides (init)

When there's no `overrides/` folder, offer once during setup to create one. The reviewer can decline and continue with the defaults. Also do this whenever the reviewer asks to create or refresh the overrides.

1. Investigate without asking: the git host; how PRs link to tickets (recent PR descriptions); how recent review comments are tagged and phrased; the project's agent instructions, rules and any review-related skills; the CI config and the commands for running tests on changed files.
2. Show a proposed `OVERRIDES.md` in chat, with the evidence for each item. Leave out anything that matches this skill's defaults.
3. The reviewer confirms or edits it. Then write `ai-plans/code-review/overrides/OVERRIDES.md`, following [overrides-template.md](overrides-template.md).

## Ground rules

- **Never post, resolve, edit or delete anything on the git host without explicit approval.** Pending review comments count as posting.
- **Reviewer reads first, agent second** in each layer, unless the reviewer chooses otherwise or delegates a layer. This avoids anchoring.
- **Evidence, not verdicts, in briefs and decision questions.** Give the facts and code locations. Give a lean only when asked, or clearly labeled as a lean.
- **Answer the reviewer's questions before presenting findings,** in the same message and before any triage question. If something is unclear, explain it with a concrete flow (a request sequence, a timeline), not a restatement.
- **Write in plain language for the reviewer.** Briefs, findings, triage prompts and doc entries use full sentences and say what happens to the user or the system. Don't lean on internal labels (finding IDs, test step IDs, checklist IDs) or arrow chains; if a label is needed for cross-referencing, explain the item in words next to it. Anything meant for the author never contains internal labels.
- **Refresh before re-asking.** When an earlier decision or finding comes up again, give a short plain refresher first: what the question is, a concrete example (a timeline or request sequence), the options, and what has changed since.
- **Make every question self-contained.** The reviewer may not see the message before it. Each question names the file:line and says in one sentence what the item is. If the reviewer needs to read an explanation before deciding, ask in plain text instead.
- **Correct earlier conclusions plainly** when new evidence changes them, and offer to re-decide affected items.
- **Don't edit the review doc while the reviewer is editing it.** Re-read it right before posting.
- **Keep the review doc live-only.** The top of the doc says where we are, what's left to do, and the decisions (one line each). Everything completed and not needed for an open decision goes to `review-archive.md` in the same folder: at the end of each round, or as soon as the doc passes about 250 lines. See [Archiving the review doc](#archiving-the-review-doc).

## Review standards (defaults)

Use these unless the overrides replace them. Without overrides, if the project's agent instructions or a review skill in the project define a comment convention, follow that instead and say so during setup.

- **Severity scale:** blocker / suggestion / nit / question, plus `note` for undecided, held, or verify at runtime. Notes are never posted.
- **Comment format:** the body, a blank line, then the severity in lowercase brackets on its own line:

  ```text
  Could we move this into `utils/`, so ... ?

  [nit]
  ```

- **Voice:** collaborative, phrased as a question where possible ("Could we ...?"), one root cause per comment, no position words.
- **Review summary:** one or two sentences: thanks, the main takeaway, and the event ("No blockers from me so approving this with a couple of suggestions and nits."). Don't list every ask.
- **Replies on existing threads** have no severity tag.

## Setup (before any review)

1. Find the project root and read the overrides (see [Overrides](#overrides)). If there are none, offer to create them.
2. Gather context without reviewing:
   - the PR description, author, base branch, size, CI status (`gh pr view <number>`);
   - the linked ticket and any linked tickets, through whatever tracker access is available (the overrides say which). If there's no ticket, the PR description and any linked issues are the requirements source; say so in the doc;
   - all existing review comments and threads, from every reviewer and bot, resolved and outdated included, plus any pending review by the user.
   Check out the PR with `gh pr checkout <number>`, which also works for PRs from forks. Diff against the PR's real base branch (`gh pr view <number> --json baseRefName`), using the remote that hosts the base repo: `git diff <remote>/<base>...HEAD`. Usually that remote is `origin`, or `upstream` in a fork.
3. Report what shapes the plan: size (production vs test vs docs files), existing comments, failing CI, stale description, scope beyond the ticket.
4. Propose the phases below and let the reviewer choose (ask):
   - where to start;
   - whether to reconcile existing threads (Phase 1) or only inventory them;
   - who reads first in each layer.
   Drafts always live in the review doc, and the [review standards](#review-standards-defaults) apply without asking.
5. **Round 2 or later** (the reviewer already has a submitted review on the PR): propose Phase 1 first and skipping Phase 0's spec questions by default. Still build the requirements checklist.
6. Create `ai-plans/code-review/PR-<number>/review.md` from [review-doc-template.md](review-doc-template.md) (or its replacement in the overrides), creating the folders if needed. Work in this file from the start, so any later chat can pick it up.
7. Take the comment inventory (below).

## Comment inventory (always)

Don't raise anything another reviewer or bot has already raised. Do this even when the reviewer doesn't care about other people's threads.

1. List every existing comment in the doc: author, file:line, a one-line topic, and status (open / resolved / outdated / pending).
2. Tag each entry with the layer it belongs to, so it shows up in that layer's brief.
3. During the layers, check each finding against the inventory before presenting it. If it's already raised, say so ("already raised by <author> at <path:line>"), and don't draft a new comment. Only if the reviewer wants to add something new, draft a short reply on that thread containing just the addition.
4. Refresh the inventory before posting (Phase 5). New comments may have arrived since.

## Phase 0: Spec decisions and requirements checklist

1. Find questions where the answer would invalidate review work. Typical ones:
   - architecture versus project rules;
   - ambiguous or contradictory ticket values;
   - scope overlap with other tickets;
   - handling of personal data, when the PR touches any;
   - requirements the platform or runtime can't meet as written.
2. Present each with evidence only, and collect decisions (ask).
3. If the reviewer wants to discuss a decision:
   - check the codebase constraints first (runtime limits, caching, existing patterns);
   - present options with concrete implications;
   - if they need to consult someone, write a self-contained pros/cons summary they can forward.
4. Build a requirements checklist from the ticket (or the PR description when there's no ticket), one ID per scenario or rule, each mapped to the layer that will check it. Every finding later references a checklist ID. Keep the source's own wording, since near-synonyms in a ticket often name different things, and mark anything inferred rather than stated as **inferred**, including requirements that only follow from a general rule elsewhere in the ticket.
5. Whenever an acceptance criterion is in question later (a finding, a triage, a comment), re-fetch the ticket and quote the exact sentence instead of the checklist's summary.
6. Decisions can be reopened later. Mark them as such in the doc.

## Phase 1: Reconcile existing threads (optional)

Use it when existing threads matter to the reviewer, for example their own earlier review or threads they've agreed to follow up on. Skip it for a fresh review, or when the existing threads belong to someone else and the reviewer doesn't want to act on them. The inventory still applies either way.

1. For each open thread, show what was asked and what the code looks like now. "Outdated" only means the code moved, not that it was fixed.
2. Group the threads by evidence:
   - fixed in the code;
   - unchanged;
   - settled by Phase 0 or later changes;
   - needs the author to confirm;
   - the reviewer's own pending comments.
3. The reviewer decides per group: resolve, reply, keep open for the layers, or leave for the author.
4. Replies go into the reviewer's pending review. Submitting doesn't resolve threads; resolve them after submit.
5. Threads kept open are re-evaluated inside their layer, where the reviewer forms their own view first.

## Phase 2: Layer-by-layer review

Order the layers by data flow or dependency, so each layer builds on ones already reviewed. Use the overrides' layer shapes if there are any. Some typical shapes:

- **A web feature:** storage and data contract; transport (API, fetchers, client cache); flow detection and routing; lifecycle (writes and clears); read consumers.
- **A backend endpoint:** schema and migrations; domain logic; API surface and validation; integrations and side effects.
- **A library change:** public API and types; implementation; callers and compatibility.

End with a sweep of tests (unit and E2E) and docs. The highest-risk layer may need extra context reading.

**Loop for each layer:**

1. **Brief** (keep it short; facts you gathered while preparing go in the doc, not the brief):
   - what the layer should do;
   - the files in reading order, numbered **F1, F2, …**, with context-only files marked. A unit test file shares its source file's number instead of getting its own (`F1: ProductDetails.tsx & ProductDetails.test.tsx`);
   - a `git diff` command for the layer;
   - the checklist IDs it covers;
   - notes carried in from earlier layers;
   - existing comments from the inventory that touch this layer, so they aren't raised again;
   - three to five questions to keep in mind, numbered **Q1, Q2, …**. These are prompts, not verdicts.
   Reviewers often answer per file, so separate numbering lets each note map to one item.
2. **Reviewer reads** and shares notes, often as questions.
3. **Agent's own pass**, applying the project's agent instructions and any review skills the overrides name:
   - answer the reviewer's questions with evidence;
   - say where you agree, with extra evidence;
   - present findings beyond the notes, leaving out or labeling anything already in the inventory. Brief prompts the reviewer didn't address count as findings here.
   Check cross-layer impact before proposing a blocker. For example, a "fix" that would break other callers that rely on the current behavior.
4. **Triage** (ask) on the severity scale, after the answers and findings are in chat. Allow `note`. Each option carries the file:line.
5. **Record** in the doc:
   - drafts following the review standards;
   - each draft's file:line, picked now on the declaration or call the comment is about, never a comment or docstring line;
   - any answers worth keeping;
   - checklist status updates;
   - carry-overs to later layers.

If the reviewer delegates a layer, review it alone and mark the severities as **agent-proposed**.

**Comment conventions:**

- One comment per root cause; fold related findings together.
- Don't comment separately on test updates that follow from a requested behavior change. Fold any missing regression test into the behavior comment.
- If a finding is already in the inventory, don't post a new comment. At most, add a short reply on that thread with only what's missing, and only if the reviewer wants it.
- Avoid position words like "above", since the git host doesn't show comments in doc order.

## Phase 3 and Phase 4 (optional)

- **Phase 3, cross-cutting:** scenario walkthroughs, failure modes (a dependency down, expiry, tampered input, concurrency such as two tabs or two workers), and an inventory of personal data when the PR handles any.
- **Phase 4, runtime:** run the tests for changed files, compare CI failures with the base branch, and try the change on a preview deployment or locally.

The reviewer may defer both to the next round; a code review isn't QA. Record unverified candidates in the doc so they aren't lost.

When offering these phases, never use the phase names alone. Say what each would check on this PR (for example "the cart changing in another tab while checkout is open"), which items the layers already covered, and what the PR's QA status is.

## Phase 5: Publish

1. Settle every note: post, mention in the summary, hold for the next round, or drop.
2. Build a **Publish list** section in the doc containing only what gets posted:
   - the review summary;
   - replies on existing threads;
   - inline comments with file:line and severity, in posting order;
   - the held items.
3. The reviewer approves the wording, editing in place or in chat. Re-read the doc before posting.
4. **Round 2 or later:** say how the event interacts with the reviewer's previous review. On GitHub, a Comment review doesn't replace an earlier "changes requested", so only Approve (or a new Request changes) changes their state. Give it with the publish list, not only when asked.
5. Refresh the comment inventory, and drop or convert to replies any drafts that someone else has raised in the meantime.
6. Write `publish.json` in the PR's folder from the doc's quoted blocks instead of retyping the bodies, so the posted text can't drift from the approved text. Check every inline target with the posting script's dry run, which confirms the line sits inside a diff hunk and prints the code it points at. Then post to the pending review. See [github-pending-review.md](github-pending-review.md) and [scripts/post-pending-review.py](scripts/post-pending-review.py).
7. Verify the pending comment count afterwards. If it's off, find out why before assuming an error, since the reviewer may be editing on the git host at the same time.
8. Don't delete the reviewer's own pending notes unless asked.
9. After the reviewer submits, check what landed: the event, the summary, every inline comment and every reply. Resolve the agreed threads (or confirm they did). Then update the doc's progress, noting how the posted review differed from the publish list, and add a short "Next round: where to start" section. Then archive the round (below).

**Other git hosts:** the posting guide and script are for GitHub. On other hosts, stop at the approved publish list and let the reviewer post by hand, unless the overrides describe a posting flow.

## Archiving the review doc

1. Copy the whole doc to `review-archive.md` in the PR's folder first, so nothing is lost. If an archive already exists, append the new round to it instead.
2. Give the archive a header: it's a snapshot (date and time), not maintained, and what it contains (rounds, phases, findings, test logs).
3. Rewrite `review.md` with only what's live: where we are, to do, decisions (one line each), held items, drafts not yet posted or sent, the current requirements checklist, and any reference the open decisions depend on.
4. In the archive, mark sections that live on in the main doc as **stale copies**.
5. Verify approved or pending drafts moved word for word (diff the sections).

## Next round

Re-read the overrides, then open `ai-plans/code-review/PR-<number>/review.md` (not the archive), and start from its "Held" and "To do" sections and the author's replies. Check each posted comment against the new commits, then run the deferred Phase 3 and Phase 4 items. Look things up in the archive only when an item needs its history.

## Tooling

- `gh` needs network access. Request it if your environment sandboxes commands.
- Ticket trackers and documentation (Jira, Linear, Confluence, and so on) are reached through whatever tools or MCP servers are available. The overrides name the specifics, such as a site ID.
