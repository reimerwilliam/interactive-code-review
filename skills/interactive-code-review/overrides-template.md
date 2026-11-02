# Overrides template

Copy this to `ai-plans/code-review/overrides/OVERRIDES.md` in a project, or let the skill's init step write it. Delete any section you don't need, and leave out anything that matches the skill's defaults.

Everything in `OVERRIDES.md` takes precedence over the skill. Instructions the reviewer gives in the chat take precedence over both.

---

# Interactive code review: overrides for <project>

## Project facts

### Review conventions

<Severity scale, where the tag goes, voice, and anything else the team expects in a review comment. For example: "Tags are `[blocker]`, `[suggestion]`, `[question]`, `[nit]`, `[possible blocker]` and `[info]`, on their own line at the end of the comment.">

### Project instructions to apply

<Rules files, docs, and review or domain skills the agent should apply during its own pass in each layer, beyond what the tool loads anyway. For example: "Load the `reviewer` skill in `.agents/skills/reviewer/` and calibrate severity with its `references/principles.md`.">

### Ticket tracker

<The system, any ID the tools need (for example a Jira `cloudId`), how PRs link to tickets, and where related documentation lives. Or "none: use the PR description".>

### Git host

<GitHub (the default), or another host and how to post there. If it isn't GitHub and there's no posting flow here, the skill stops at the approved publish list.>

### CI and test notes

<Quirks that affect findings (for example how tests are routed to CI jobs), the usual base branch, and the commands for running tests on changed files.>

### Layer shapes

<How PRs in this repo usually split into layers, in reading order.>

## Changes to the skill

<Free-form changes to how the skill runs. Name the skill section you're changing, so it's clear what's replaced. For example:
- "Setup: always run Phase 1; never only inventory the threads."
- "Ground rules: the agent reads first in every layer."
- "Where things live: put review folders in `docs/reviews/PR-<number>/` instead." (The overrides folder itself always stays at `ai-plans/code-review/overrides/`.)
- "Review standards: no severity tags; write the severity in the first word instead.">

## Replacement files

<Files in this folder that replace the skill's bundled files, so readers know they exist. For example: "`review-doc-template.md`: a shorter doc without the Phase 1 section.">
