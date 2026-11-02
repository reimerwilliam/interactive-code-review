# Working with a pending GitHub review

All commands need network access. `OWNER`, `REPO` and `NUMBER` are placeholders.

## Read threads with resolution state

```bash
gh api graphql -f query='query { repository(owner:"OWNER", name:"REPO") { pullRequest(number:NUMBER) {
  reviewThreads(first:100) { nodes { id isResolved isOutdated path line originalLine
    comments(first:20) { nodes { author{login} createdAt body pullRequestReview{ state } } } } } } } }'
```

`pullRequestReview.state == PENDING` marks the user's own unsubmitted comments.

## Find the user's pending review

```bash
gh api graphql -f query='query { repository(owner:"OWNER", name:"REPO") { pullRequest(number:NUMBER) {
  reviews(states:PENDING, first:5) { nodes { id author{login} comments(first:1){ totalCount } } } } } }'
```

If there's none, create one with `addPullRequestReview` (without `event`), so it stays pending.

## Add to the pending review

Inline comment (the line must be inside a diff hunk on the PR head; check first):

```graphql
mutation($review: ID!, $path: String!, $line: Int!, $body: String!) {
  addPullRequestReviewThread(input: {pullRequestReviewId: $review, path: $path, line: $line, side: RIGHT, body: $body}) {
    thread { id comments(first:1) { nodes { state } } }
  }
}
```

Reply on an existing thread:

```graphql
mutation($review: ID!, $thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewId: $review, pullRequestReviewThreadId: $thread, body: $body}) {
    comment { id state }
  }
}
```

Pass bodies with `-f body="..."` and integers with `-F line=123`.

## Verify target lines before posting

- Confirm the local `HEAD` equals the PR head SHA (`gh api repos/OWNER/REPO/pulls/NUMBER --jq .head.sha`).
- Each target line must sit inside a hunk of the PR's diff (`gh pr diff NUMBER`), on the new side: for `@@ -a,b +c,d @@`, `c <= line <= c+d-1`. Print the line's content to confirm it's the code the comment is about.
- Prefer the line of the declaration or call the comment discusses over a docstring line.

The posting script's `--dry-run` does these checks for every comment in `publish.json`.

## Posting script

[`scripts/post-pending-review.py`](scripts/post-pending-review.py) posts everything in one go. It reads `publish.json` from the PR's review folder, finds or creates the user's pending review, adds the inline comments and replies, records failures, and prints the pending comment count at the end.

Build `publish.json` from the review doc's quoted blocks (copy the text, don't retype it):

```json
{
  "owner": "OWNER",
  "repo": "REPO",
  "number": 123,
  "comments": [
    { "id": "2.1-a", "path": "src/file.ts", "line": 42, "body": "Could we ...?\n\n[suggestion]" }
  ],
  "replies": [
    { "thread": "PRRT_...", "body": "Thanks, this reads much better now!" }
  ]
}
```

Run it from the project root:

```bash
python3 <skill-dir>/scripts/post-pending-review.py ai-plans/code-review/PR-123/publish.json --dry-run
python3 <skill-dir>/scripts/post-pending-review.py ai-plans/code-review/PR-123/publish.json
```

`<skill-dir>` is the folder this file is in, or the replacement script in `ai-plans/code-review/overrides/scripts/` if the overrides provide one.

## Known limitations

- **A review body can't be set on a pending review that was created without one** ("Could not edit a review with a missing body"). The reviewer pastes the summary in GitHub's "Finish your review" dialog.
- **Submitting doesn't resolve threads.** Resolve them afterwards:
  ```bash
  gh api graphql -f query='mutation { resolveReviewThread(input:{threadId:"THREAD_ID"}) { thread { isResolved } } }'
  ```
- **To move a pending comment,** add the new one first, then delete the old one with `deletePullRequestReviewComment(input:{id})`.
- **Re-count after any batch.** The reviewer may be editing or deleting comments on GitHub at the same time.
- **A Comment review doesn't replace a reviewer's earlier "changes requested".** Only Approve or a new Request changes changes their review state, so on round 2+ a Comment keeps the PR blocked where branch protection counts it.
- **After submit, check every reply landed**, not just the inline count: a reply can disappear from the submitted review (for example, deleted by the reviewer). Query each replied thread's comments.
