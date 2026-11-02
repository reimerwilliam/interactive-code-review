#!/usr/bin/env python3
"""Post approved review comments and replies to the user's pending GitHub review.

Usage:
    post-pending-review.py <publish.json> [--dry-run]

publish.json:
    {
      "owner": "OWNER", "repo": "REPO", "number": 123,
      "comments": [{"id": "2.1-a", "path": "src/file.ts", "line": 42, "body": "..."}],
      "replies": [{"thread": "PRRT_...", "body": "..."}]
    }

Every inline target is checked against the PR's diff before anything is posted.
--dry-run only runs the checks and prints what would be posted.
Requires the GitHub CLI (`gh`), authenticated, with network access.
"""

import argparse
import json
import re
import subprocess
import sys

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:3])} failed: {result.stderr.strip()}")
    return result.stdout


def graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        args += [flag, f"{key}={value}"]
    result = subprocess.run(args, capture_output=True, text=True)
    payload = json.loads(result.stdout or "{}")
    if result.returncode != 0 or payload.get("errors"):
        raise RuntimeError(payload.get("errors") or result.stderr)
    return payload["data"]


def load_publish_list(path):
    with open(path, encoding="utf-8") as file:
        publish = json.load(file)
    missing = [key for key in ("owner", "repo", "number") if key not in publish]
    if missing:
        sys.exit(f"{path} is missing: {', '.join(missing)}")
    publish.setdefault("comments", [])
    publish.setdefault("replies", [])
    return publish


def commentable_lines(owner, repo, number):
    """Map each file path to {new-side line number: content} for lines inside diff hunks."""
    diff = run(["gh", "pr", "diff", str(number), "--repo", f"{owner}/{repo}"])
    files = {}
    current = None
    new_line = 0
    for raw_line in diff.splitlines():
        if raw_line.startswith("diff --git"):
            current = None
        elif raw_line.startswith("+++ "):
            target = raw_line[4:]
            current = files.setdefault(target[2:], {}) if target.startswith("b/") else None
        elif raw_line.startswith("@@"):
            match = HUNK_HEADER.match(raw_line)
            new_line = int(match.group(1)) if match else 0
        elif current is not None and raw_line[:1] in (" ", "+"):
            current[new_line] = raw_line[1:]
            new_line += 1
    return files


def check_targets(publish):
    owner, repo, number = publish["owner"], publish["repo"], publish["number"]
    problems = []

    head_sha = run(["gh", "api", f"repos/{owner}/{repo}/pulls/{number}", "--jq", ".head.sha"]).strip()
    try:
        local_sha = run(["git", "rev-parse", "HEAD"]).strip()
    except RuntimeError:
        local_sha = None
    if local_sha != head_sha:
        print(f"WARN  local HEAD {local_sha} differs from PR head {head_sha}; line numbers come from the PR diff")

    files = commentable_lines(owner, repo, number)
    for comment in publish["comments"]:
        label = f"{comment.get('id', '?')} {comment['path']}:{comment['line']}"
        lines = files.get(comment["path"])
        if lines is None:
            problems.append(f"{label}: file is not in the PR diff")
            print(f"FAIL  {label}: file is not in the PR diff")
        elif comment["line"] not in lines:
            problems.append(f"{label}: line is outside every diff hunk")
            print(f"FAIL  {label}: line is outside every diff hunk")
        else:
            print(f"ok    {label}: {lines[comment['line']].strip()}")
    return problems


def get_pending_review(owner, repo, number):
    data = graphql(
        """query($owner: String!, $repo: String!, $number: Int!) {
          viewer { login }
          repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
            id
            reviews(states: PENDING, first: 5) { nodes { id author { login } comments(first: 100) { totalCount } } }
          } } }""",
        owner=owner, repo=repo, number=number,
    )
    viewer = data["viewer"]["login"]
    pull_request = data["repository"]["pullRequest"]
    mine = [review for review in pull_request["reviews"]["nodes"] if review["author"]["login"] == viewer]
    return pull_request["id"], (mine[0] if mine else None)


def post(publish):
    owner, repo, number = publish["owner"], publish["repo"], publish["number"]
    pull_request_id, review = get_pending_review(owner, repo, number)
    if review is None:
        created = graphql(
            """mutation($pr: ID!) { addPullRequestReview(input: {pullRequestId: $pr}) { pullRequestReview { id } } }""",
            pr=pull_request_id,
        )
        review_id = created["addPullRequestReview"]["pullRequestReview"]["id"]
        print(f"created pending review {review_id}")
    else:
        review_id = review["id"]
        print(f"using pending review {review_id} ({review['comments']['totalCount']} existing comments)")

    failures = []
    for comment in publish["comments"]:
        label = f"{comment.get('id', '?')} {comment['path']}:{comment['line']}"
        try:
            graphql(
                """mutation($review: ID!, $path: String!, $line: Int!, $body: String!) {
                  addPullRequestReviewThread(input: {pullRequestReviewId: $review, path: $path, line: $line, side: RIGHT, body: $body}) { thread { id } } }""",
                review=review_id, path=comment["path"], line=comment["line"], body=comment["body"],
            )
            print(f"ok    {label}")
        except RuntimeError as error:
            failures.append(label)
            print(f"FAIL  {label} {error}")

    for reply in publish["replies"]:
        try:
            graphql(
                """mutation($review: ID!, $thread: ID!, $body: String!) {
                  addPullRequestReviewThreadReply(input: {pullRequestReviewId: $review, pullRequestReviewThreadId: $thread, body: $body}) { comment { id } } }""",
                review=review_id, thread=reply["thread"], body=reply["body"],
            )
            print(f"ok    reply on {reply['thread']}")
        except RuntimeError as error:
            failures.append(reply["thread"])
            print(f"FAIL  reply on {reply['thread']} {error}")

    _, review_after = get_pending_review(owner, repo, number)
    count = review_after["comments"]["totalCount"] if review_after else 0
    print(f"pending review comment count: {count}")
    return failures


def main():
    parser = argparse.ArgumentParser(description="Post approved comments to the user's pending GitHub review.")
    parser.add_argument("publish_json", help="path to publish.json in the PR's review folder")
    parser.add_argument("--dry-run", action="store_true", help="check targets and print, but post nothing")
    args = parser.parse_args()

    publish = load_publish_list(args.publish_json)
    problems = check_targets(publish)

    if args.dry_run:
        for reply in publish["replies"]:
            print(f"reply on {reply['thread']}: {reply['body'][:80]}")
        print(f"{len(publish['comments'])} comments, {len(publish['replies'])} replies, {len(problems)} problems")
        sys.exit(1 if problems else 0)

    if problems:
        sys.exit("Not posting: fix the targets above first.")
    failures = post(publish)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
