# Getting started

The Model Verse is a local-first video generation engine. Rendering and speech
generation work locally; publishing integrations are optional and require the
relevant provider credentials.

## Prerequisites

- Python 3.11 or 3.12
- Node.js 22 and npm
- `ffmpeg`, Cairo, Pango, LaTeX, `dvisvgm`, and `espeak-ng`

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev \
  texlive-latex-extra texlive-fonts-recommended dvisvgm espeak-ng
```

## Install

```bash
cp .env.example .env
make setup
```

This installs runtime dependencies from `requirements.txt`, contributor and
CI test tooling from `requirements-dev.txt`, and the exact Node dependency
tree recorded in `package-lock.json`.

Run the local environment doctor before a first render. It reports missing
native tools without inspecting or printing secret values:

```bash
make doctor
```

Missing LaTeX, `dvisvgm`, or `espeak-ng` tools block full rendering but do not
prevent source inspection or frontend work.

Generated videos, render frames, caches, and Python bytecode are never source
of truth. To inspect reclaimable generated paths, use the safe dry run:

```bash
make clean-generated
```

When the report is correct, `make clean-generated-apply` moves those paths to a
recoverable quarantine outside the repository. It does not permanently delete
anything and intentionally leaves source code, curated assets, model weights,
and historical documentation untouched.

Production CI uses Gemini 3.8 Flash TTS with the Charon informative voice for
English narration. Set `GEMINI_API_KEY`, `TTS_PROVIDER=gemini`,
`GEMINI_TTS_MODEL=gemini-3.8-flash-tts`, and `GEMINI_TTS_VOICE=Charon`.
Set `FAIL_ON_TTS_PROVIDER_FALLBACK=true` in production so a quota outage stops
the run instead of creating a mixed-voice short. Pocket remains available as an
explicit offline fallback for local development.

For a lightweight CPU-only English alternative, install Kyutai's official
`pocket-tts` binary and set `TTS_PROVIDER=pocket` plus
`POCKET_TTS_BIN=/absolute/path/to/pocket-tts`. The recommended local profile
is `POCKET_TTS_LANGUAGE=english_18m_2026-10`. Pocket TTS is the local offline
fallback; if it is unavailable, the pipeline fails clearly rather than
silently downloading another model.

## Validate the installation

```bash
make test-python
make test-web
make lint
make render-smoke
```

The Python targets use `.venv/bin/python` created by `make setup`. Check
resolved package consistency before testing with:

```bash
make deps-check
```

Optional advisory checks are separate and non-mutating:

```bash
.venv/bin/python -m pip install pip-audit
make deps-audit
```

Review dependency updates manually. Do not run `npm audit fix --force` without
reviewing its proposed major-version changes.

The Python suite includes network-aware integrations. For a fast local check,
run the focused tests first:

```bash
.venv/bin/python -m pytest -q test/test_github_trending_fetcher.py \
  test/test_code_execution_engine.py
```

## Run the engine

Dry-run discovery and script generation:

```bash
python3 pipeline/daily_shorts_daemon.py --dry-run --count 1 --source mixed
```

For the full pipeline validation mode, `run_pipeline.py --dry-run` is
repository-read-only: it writes temporary audio, captions, templates, visual
modules, and preview frames outside the checkout, then removes that workspace
when validation finishes.

```bash
python3 pipeline/run_pipeline.py --dry-run
```

Use `--validate-visuals` only when you explicitly want the dry run to invoke
the LLM-backed bespoke visual synthesizer and sandbox checks:

```bash
python3 pipeline/run_pipeline.py --dry-run --validate-visuals
```

Render a specific paper locally:

```bash
python3 pipeline/run_pipeline.py --arxiv 2407.08608 --allow-stale
```

Publishing commands require valid provider credentials. Keep publishing
disabled while developing scenes or pipeline changes.
