# Production Completion Checklist

This checklist records the autonomous production pass for the content-diversification and Instagram distribution work.

## Completed

- [x] Analyze four reference Reel formats and map them to production formats.
- [x] Rotate creative treatment independently from research source.
- [x] Pass the selected creative format into script and visual generation.
- [x] Verify the Instagram account and Meta access token without exposing credentials.
- [x] Enable scheduled Instagram publishing through `ENABLE_INSTAGRAM_AUTOPUBLISH`.
- [x] Rebase production state before applying generated artifacts, preventing concurrent-run conflicts.
- [x] Install the Pocket TTS fallback in pull-request CI.
- [x] Keep deterministic vision-fallback scores non-zero while failing semantic QA honestly.
- [x] Track the required Kimi topic poster as a reproducible test asset.

## Release gates

- Pull request CI must pass Python tests, the Manim smoke render, frontend checks, and security checks.
- A maintainer must merge the pull request into `main`; scheduled Instagram publishing starts only from the merged workflow.
- The first scheduled production run should be reviewed from its uploaded artifact and Instagram permalink.

## Safety

Instagram publishing is controlled by the repository variable `ENABLE_INSTAGRAM_AUTOPUBLISH`. Set it to `false` to pause scheduled cross-posting without changing code or secrets.
