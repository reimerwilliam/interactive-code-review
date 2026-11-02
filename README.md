# interactive-code-review

An [Agent Skill](https://agentskills.io) for reviewing a large or high-risk pull request together with an AI agent, step by step. The reviewer stays in charge: they read each layer first, decide severities and wording, and approve everything before it's posted. The agent gathers evidence, writes briefs, gives a second read, and drafts comments.

It works in any repo. Anything specific to a project goes in optional overrides inside that project (see below).

## Requirements

- The [GitHub CLI](https://cli.github.com/) (`gh`), authenticated, for reading PRs and posting the review.
- Python 3, for the posting script.
- An agent that supports Agent Skills: Cursor, Claude Code and Antigravity all do.

## Install

The skill is the folder `skills/interactive-code-review/`. Each tool reads global skills from its own folder, so install it once and link it into each one.

### With the `skills` CLI

```bash
npx skills add <owner>/interactive-code-review -g
```

This copies the skill to `~/.agents/skills/` and links it into the tools it detects. Afterwards, run `/skills` in Antigravity to check it's listed: the CLI may use an older Antigravity path than the one below.

### By hand (best while editing the skill)

Clone this repo, then link the skill folder into each tool:

```bash
SKILL="$PWD/skills/interactive-code-review"

mkdir -p ~/.agents/skills ~/.claude/skills ~/.gemini/config/skills
ln -s "$SKILL" ~/.agents/skills/interactive-code-review        # Cursor
ln -s "$SKILL" ~/.claude/skills/interactive-code-review        # Claude Code
ln -s "$SKILL" ~/.gemini/config/skills/interactive-code-review # Antigravity (app and CLI)
```

Edits in the repo then show up in every tool straight away.

## Use

Start it with `/interactive-code-review <PR number or URL>`. It only runs when asked.

## Where review files go

Reviews are written into the project being reviewed, one folder per PR:

```text
ai-plans/code-review/
  overrides/              optional: your customisations for this project
    OVERRIDES.md
  PR-<number>/
    review.md             the working doc
    review-archive.md     completed rounds
    publish.json          what gets posted
  RETRO.md                optional
```

Whether `ai-plans/` is committed or git-ignored is up to you; the skill never changes `.gitignore` and never commits review files.

## Overrides

`ai-plans/code-review/overrides/` lets you change anything about the skill for one project without editing the skill:

- `OVERRIDES.md` holds project facts (review conventions, ticket tracker, CI quirks, usual layer shapes) and free-form changes to any part of the skill. See [overrides-template.md](skills/interactive-code-review/overrides-template.md).
- A file in `overrides/` with the same name as one of the skill's files replaces it: `review-doc-template.md`, `github-pending-review.md`, or `scripts/post-pending-review.py`.

Instructions you give in the chat come first, then the overrides, then the skill. If a project has no overrides, the skill offers to create them on first use, from what it can find in the repo.
