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

The Kokoro voice models are downloaded on first use and are intentionally
ignored by Git. Do not commit model weights, OAuth tokens, generated videos,
or render caches.

## Validate the installation

```bash
make test-python
make test-web
make lint
make render-smoke
```

The Python suite includes network-aware integrations. For a fast local check,
run the focused tests first:

```bash
pytest -q test/test_github_trending_fetcher.py \
  test/test_code_execution_engine.py
```

## Run the engine

Dry-run discovery and script generation:

```bash
python3 pipeline/daily_shorts_daemon.py --dry-run --count 1 --source mixed
```

Render a specific paper locally:

```bash
python3 pipeline/run_pipeline.py --arxiv 2407.08608 --allow-stale
```

Publishing commands require valid provider credentials. Keep publishing
disabled while developing scenes or pipeline changes.
