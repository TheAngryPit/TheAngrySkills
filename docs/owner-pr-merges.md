# Owner-authored pull requests

The repository owner may merge their own pull requests without obtaining a
second person's approval. Other contributors still need the configured
approving review, including approval after the most recent reviewable push.
CI, security admission and required automated-review evidence remain part of
the maintainer's acceptance criteria for both paths.

## Identity and scope

This policy applies to `TheAngryPit/TheAngrySkills` while it is a personal
repository owned by `TheAngryPit`. The exception requires all of the following:

- GitHub identifies the authenticated account and the PR author as
  `TheAngryPit`; commit author names or email addresses are insufficient.
- The PR targets `main` from a branch in this repository, not a fork.
- The owner authorized merging this PR. An agent using the owner's CLI
  credentials does not receive a separate standing permission to merge.
- The current head is mergeable, the full Skill stack CI passed, all applicable
  required status checks passed, and review findings are resolved.
- The security comparison satisfies [PR safety minimums](pr-safety-minimums.md).
  An owner exemption from human approval does not waive that evidence.

GitHub sees the authenticated account, not the human or agent operating it.
Do not lend owner credentials to other contributors or substitute identities.
Bots and external contributors do not acquire the owner's exception through a
branch name, commit metadata, permission to push, or an owner-issued task.

## Existing GitHub configuration

On 17 November 2026, read-only API inspection confirmed a personal repository,
`TheAngryPit` as its only listed administrator, one required approving review,
`require_last_push_approval=true`, and `enforce_admins.enabled=false`.

GitHub's existing administrator exception therefore supports the owner path;
a normal CLI merge can still report `REVIEW_REQUIRED`. This is not a reason
to remove the review requirement for contributors. This PR documents the
operating policy; it does not modify settings through a workflow or API call.
If ownership, administrator access, rulesets or admin enforcement changes,
recheck the effective restrictions before relying on this snapshot.

Sources: [personal repository permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository),
[protected branches and administrator exceptions](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[GitHub CLI merge options](https://cli.github.com/manual/gh_pr_merge).

## Native owner merge procedure

First inspect the authenticated account, PR author, source/base repository,
exact head and live checks. For example, substitute the intended PR number:

```bash
gh api user --jq .login
gh pr view PR_NUMBER --repo TheAngryPit/TheAngrySkills \
  --json author,baseRefName,headRefOid,isCrossRepository,mergeable,reviewDecision
gh pr checks PR_NUMBER --repo TheAngryPit/TheAngrySkills --watch
```

Review the CI result and security evidence, rather than treating the approval
exception as permission to ignore a failed, missing or pending check. Once the
identity, authorization and evidence above are verified, use the native option
with the inspected full head SHA:

```bash
gh pr merge PR_NUMBER --repo TheAngryPit/TheAngrySkills \
  --squash --admin --match-head-commit FULL_HEAD_SHA
```

`--admin` is broader than a review-only exception: GitHub can use it to override
other branch requirements too. Its use under this repository policy is limited
to the missing second human approval after the other acceptance checks pass.
If GitHub refuses that authorized native operation, stop and report the rule;
do not disable protection, change accounts, or force-push a merge commit.
Verify the PR is merged and read back its merge commit before reporting success.

For other authors, use ordinary reviewed PR merges. Do not apply this procedure
to their PRs merely because the owner is available to perform the merge.
Auto-merge waits for the normal review requirements; enabling it alone does not
select the explicit owner exception.
