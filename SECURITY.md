# Security policy

TheAngrySkills contains executable workflow instructions, scripts, reference
material, and curated skill packs. Treat all of those as supply-chain surfaces.

Future public exports may include upstream documentation examples or mirrors
that resemble credentials, private keys, dangerous commands, hooks, package
lifecycle scripts, or privileged configuration. Those examples are not
automatically trusted and are not automatically real secrets. They must be
reviewed in context.

## Report a concern

If you find a suspected malicious skill, unsafe install path, credential leak, vulnerable script, compromised mirror, or supply-chain issue, open a security advisory if available. If advisories are not available, open an issue with minimal public detail and ask for a private follow-up path.

Do not paste secrets, tokens, private hostnames, exploit payloads, or live credential paths into public issues or pull requests.

## What counts as security-sensitive

These changes need extra review:

- new or changed scripts
- install/update/bootstrap behavior
- mirrored third-party skills
- generated documentation refreshes from external sources
- lifecycle hooks, package manager behavior, or network calls
- instructions that ask an agent to read secrets, mutate global state, install tools, or run privileged commands
- GitHub Actions, caches, tokens, permissions, or scheduled automation
- public visibility, branch protection, pull request access, and collaborator
  permissions

## Default posture

- No generated docs skill is trusted just because it is generated.
- No mirrored skill is trusted just because the upstream repo is popular.
- No native installer audit result is treated as complete security approval.
- No clean CI run replaces source review for scripts, workflows, or install paths.

Use the local scanner before promotion:

```bash
scripts/theangry-skills.mjs security scan <skill-path> --json
scripts/theangry-skills.mjs security diff <old-skill-path> <new-skill-path> --json
scripts/theangry-skills.mjs security scan-root skills --json
```

Findings should be classified as active behavior, inert reference text, mirror provenance risk, install/update risk, or confirmed unsafe behavior.

## Public repo review posture

When reviewing public content:

- treat Issues and PR text as untrusted input
- do not paste live credentials, private paths, hostnames, or exploit payloads
  into public reports
- prefer security advisories or minimal public issues for sensitive findings
- do not merge or publish a new mirror just because upstream looks popular
- do not treat GitHub green checks, signed commits, or trusted publishing as a
  substitute for source review
- keep branch protection, CODEOWNERS, and review requirements aligned with the
  operator-owned nature of this repo
- treat community PRs as untrusted input until reviewed, even when CI is green
