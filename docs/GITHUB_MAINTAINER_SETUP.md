# GitHub maintainer setup

This document records the repository settings that should be applied by a
GitHub administrator. The coding agent does not change these remote settings.

## Required baseline

1. Keep `main` as the default branch.
2. Require pull requests before merging into `main`.
3. Require the `Pull Request CI` workflow to pass before merging.
4. Require at least one approval and dismiss stale approvals after new commits.
5. Block force-pushes and branch deletion on `main`.
6. Keep Actions restricted to read-only permissions by default; deployment or
   persistence jobs must declare their narrower write permission explicitly.
7. Require Actions to use full-length commit-SHA pins. Dependabot is configured
   to propose updates for Python, npm, and GitHub Actions dependencies.

## Secrets and publishing

- Store provider credentials only in repository or environment secrets.
- Use separate environments for review, staging, and production publishing.
- Keep publishing workflows manually gated until credentials and privacy
  defaults are verified.
- Never place OAuth files, token JSON, generated videos, model weights, or
  personal absolute paths in commits.

## Review checklist

Before enabling required checks, confirm that a clean pull request passes:

```bash
make doctor
make test-python
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run lint
```

The local repository also provides [CODEOWNERS](../.github/CODEOWNERS), a pull
request template, issue forms, and [Dependabot configuration](../.github/dependabot.yml).
