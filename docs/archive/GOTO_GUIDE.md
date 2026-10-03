# 📐 THE MODEL VERSE — MASTER GOTO OPERATOR MANUAL & ARCHITECTURE GUIDE

> **The Model Verse (`themodelverse.in`)**  
> Autonomous Short Video Production Engine for Frontier AI Research.  
> Transforming dense arXiv papers into viral, broadcast-grade **3Blue1Brown-style 1080×1920 YouTube Shorts**.

---

## 📑 TABLE OF CONTENTS
1. [Executive Overview: Why 3Blue1Brown?](#1-executive-overview-why-3blue1brown)
2. [The 4 Production Categories](#2-the-4-production-categories)
3. [End-to-End Pipeline Architecture (Steps 1 to 7)](#3-end-to-end-pipeline-architecture)
4. [Operator Manual: How to Run & Utilize Every Feature](#4-operator-manual-how-to-run--utilize-every-feature)
   - [Method 1: Interactive Web Studio (GUI Cockpit)](#method-1-interactive-web-studio-gui-cockpit)
   - [Method 2: 1-Click Autonomous Producer CLI (`auto_produce.py`)](#method-2-1-click-autonomous-producer-cli-auto_producepy)
   - [Method 3: Daily Trending Scraper & Cron Auto-Pilot (`batch_digest.py`)](#method-3-daily-trending-scraper--cron-auto-pilot-batch_digestpy)
   - [Method 4: High-CTR Poster Generator CLI (`generate_thumbnail.py`)](#method-4-high-ctr-poster-generator-cli-generate_thumbnailpy)
5. [Action Items & Configuration Required from You](#5-action-items--configuration-required-from-you)
6. [Complete Codebase Map & Directory Structure](#6-complete-codebase-map--directory-structure)
7. [Command Reference & Cheat Sheet](#7-command-reference--cheat-sheet)

---

## 1. Executive Overview: Why 3Blue1Brown?

### The Core Problem: The "SaaS Card Trap"
Standard automated video generators churn out what technical viewers recognize as generic marketing slop:
- Rounded floating white boxes and fake browser windows.
- Robotic, mono-tone text-to-speech without emotion or musical pacing.
- Distracting stock video footages unrelated to the underlying mathematics.

### The Model Verse Standard
Frontier AI researchers, machine learning practitioners, and technical enthusiasts respect the visual elegance of **3Blue1Brown**:
- **Living Chalkboard Canvas**: Pure `#0A0D14` carbon background featuring an authentic coordinate dot matrix.
- **Computer Modern $\mathrm{\LaTeX}$ Formulas**: Mathematical expressions rendered via vector paths (`SVGMobject`) rather than blurry raster text.
- **Concrete Geometric Vector Entities**: Synaptic bipartite networks, 256-node expert constellations, dynamic laser routers, and SRAM memory caching blocks.
- **Sample-Accurate Sound Design**: Crisp neural speech (`am_adam`), procedural lo-fi ambient synthwave, and sample-accurate dynamic audio ducking (swelling during pauses, ducking during narration).
- **Zero SaaS Cards / Zero Fake Buttons**: Pure mathematical, chalkboard-native communication.

---

## 2. The 4 Production Categories

Every ingested AI paper is automatically analyzed, scored, and routed into one of 4 production visual categories:

### 1. `architecture_breakdown` (Flagship)
- **Focus**: Core neural network topologies, MoE partitioning, routing algorithms, layer hierarchies.
- **Key Visual Grammar**: 256-node expert constellation, Top-8 router lasers, shared expert $E_s$ golden foundation, parameter efficiency counters.
- **Case Study**: **DeepSeek-V3 MoE** (`671B` total parameters, only `37B` active per token).
- **Master Video**: `final_deepseek-v3_architecture_breakdown.mp4` (48.59s)
- **High-CTR Poster**: `public/thumbnails/deepseek-v3_poster.png`

### 2. `benchmark_news`
- **Focus**: SOTA leaderboard upsets, breakthrough test scores (AIME, SWE-bench, Codeforces), inference cost disruption.
- **Key Visual Grammar**: Dynamic animated leaderboard race, pure RL reasoning trees (GRPO), side-by-side cost disruption meters.
- **Case Study**: **DeepSeek-R1** (scoring 79.8% on AIME 2024, matching OpenAI o1 at 27x lower cost).
- **Master Video**: `final_deepseek-r1_benchmark_news_benchmark_news.mp4` (42.47s)
- **High-CTR Poster**: `public/thumbnails/deepseek-r1_benchmark_news_poster.png`

### 3. `mechanism_deepdive`
- **Focus**: Hardware-level optimizations, attention kernels, memory hierarchy, KV caching, GPU execution flow.
- **Key Visual Grammar**: The $\mathcal{O}(N^2)$ quadratic bottleneck trap, SRAM tile scheduling, Hopper asynchronous TMA matrix loads.
- **Case Study**: **FlashAttention-3 & KV Cache Explained** (`1.2 PFLOPS/s` peak FP8 throughput).
- **Master Video**: `final_flashattention-3_mechanism_deepdive_mechanism_deepdive.mp4` (70.84s)
- **High-CTR Poster**: `public/thumbnails/flashattention-3_mechanism_deepdive_poster.png`

### 4. `model_showdown`
- **Focus**: Direct head-to-head architectural and cost comparisons between two competing frontier models.
- **Key Visual Grammar**: Split-screen chalkboard contender cards, metric parity gauges, pricing collapse ratios.
- **Case Study**: **DeepSeek-V3 vs GPT-4o** ($96\%$ price savings with parity reasoning).
- **Master Video**: `final_deepseek_vs_gpt4_model_showdown.mp4` (39.77s)
- **High-CTR Poster**: `public/thumbnails/deepseek_vs_gpt4_poster.png`

---

## 3. End-to-End Pipeline Architecture

```
[ arXiv Paper / Hugging Face Daily Papers ]
                     │
                     ▼ (Step 1: Ingestion & Scoring)
         pipeline/batch_digest.py
                     │
                     ▼ (Step 2: Script Synthesis)
         pipeline/script_generator.py (Gemini 2.5 Flash)
                     │
                     ▼ (Step 3: Neural Voice & Dynamic Audio)
         pipeline/audio_synthesizer.py
         ├── Kokoro ONNX (am_adam, 24kHz)
         ├── scripts/synth_music_generator.py (Analog Pad Chords)
         ├── Dynamic Sidechain Ducking (-20 dB speech / -10 dB pause)
         └── Procedural SFX (Sub-impacts, Whooshes, Lasers)
                     │
                     ▼ (Step 4: Vector Blackboard Animation)
         manim_engine/scenes/*.py
         ├── Computer Modern LaTeX SVGs (public/math_svgs/)
         ├── Blackboard Coordinate Dot Matrix (#0A0D14)
         └── Manim Community Edition (1080x1920 @ 30fps)
                     │
                     ▼ (Step 5: Broadcast Muxing)
         pipeline/run_pipeline.py (FFmpeg)
         └── Kinetic Chalkboard Captions (Y = -4.8 Safe Zone)
                     │
                     ▼ (Step 6: High-CTR Poster Generation)
         pipeline/thumbnail_generator.py
         └── 1080x1920 Vertical Poster (Glowing Hook Pill + LaTeX Plate)
                     │
                     ▼ (Step 7: Automated Distribution)
         pipeline/publisher.py
         └── YouTube Data API v3 (Resumable upload + Thumbnail + Pinned comment)
```

### Detailed Breakdown of Every Step:

#### Step 1: Research Ingestion & Scoring (`pipeline/batch_digest.py`)
- Scrapes the **Hugging Face Daily Papers API** (community upvotes + discussion).
- Falls back automatically to the **arXiv API** querying recent preprints in `cs.AI`, `cs.LG`, and `cs.CL`.
- Scores each paper with a technical breakthrough heuristic:
  $$\text{Score} = \text{Keyword Weights} (\text{MoE}, \text{GRPO}, \text{FlashAttention}, \text{FP8}) + \text{Community Upvotes} \times 3$$
- Automatically classifies the paper into one of the 4 production categories.

#### Step 2: Script Synthesis (`pipeline/script_generator.py`)
- Powered by **Gemini 2.5 Flash**.
- Formulates a 6 to 7-beat mathematical script:
  - **Beat 1: The Hook**: A counter-intuitive technical question or breakthrough metric.
  - **Beat 2: The Core Tension**: The bottleneck or physical limit of existing architectures.
  - **Beat 3: The Innovation**: The mathematical mechanism that solves the bottleneck.
  - **Beat 4: The Execution / Proof**: How the data flow, router, or hardware kernel operates.
  - **Beat 5: The Payoff Metric**: The concrete quantitative improvement ($27\times$ cheaper, $94.5\%$ saved).
  - **Beat 6: Minimalist Chalkboard Brand Signature**: Follow `THE MODEL VERSE` (`themodelverse.in`).

#### Step 3: Neural Narration & Dynamic Audio Engineering (`pipeline/audio_synthesizer.py`)
- **Speech Narration**: Synthesized using **Kokoro ONNX** (`am_adam`, `1.12x` speed, `24,000 Hz` sampling rate).
- **Procedural Lo-Fi Ambient Synthwave**: Synthesized via pure NumPy detuned multi-oscillators traversing a contemplative chord progression:
  $$\mathrm{Dm9} \longrightarrow \mathrm{B\flat maj9} \longrightarrow \mathrm{Gm9} \longrightarrow \mathrm{Asus4 / A7}$$
  Includes a 0.28 Hz tape drift LFO, 55 Hz sub-bass sine foundation, and high-register crystalline harmonic bells.
- **Sample-Accurate Dynamic Sidechain Ducking**:
  - **Speech Active**: Soundtrack drops to **$-20\text{ dB}$ (10% volume)**, keeping neural speech 100% intelligible.
  - **Breath Pauses & Outro**: Soundtrack swells smoothly to **$-10\text{ dB}$ (32% volume)** during inter-beat breath gaps and the brand signature.
- **Procedural SFX**: Sub-bass impacts on core reveals, gentle whooshes on beat transitions, laser chirps on top-8 routing.
- **Ceiling Limiter**: Master ceiling capped at $-0.5\text{ dB}$ (`0.944`), guaranteeing **zero digital clipping**.

#### Step 4: 3Blue1Brown Manim Animation (`manim_engine/`)
- Pure Python vector graphics rendered via **Manim Community Edition**.
- Rendered in native vertical format: **1080×1920 portrait @ 30 FPS**.
- Strict Safe Zones:
  - Width: $X \in [-3.3, +3.3]$ (clears left/right edges)
  - Height: $Y \in [-5.8, +5.8]$ (clears top/bottom YouTube overlay UI)

#### Step 5: Broadcast Muxing & Kinetic Captions (`pipeline/run_pipeline.py`)
- FFmpeg merges the Manim MP4 with the master ducked audio.
- Adds word-by-word synchronized kinetic chalkboard subtitles clamped at $Y = -4.8$, well above the YouTube Shorts caption banner.

#### Step 6: 1080×1920 High-CTR Poster Generation (`pipeline/thumbnail_generator.py`)
- Automatically generates a 1080×1920 vertical poster:
  - **Top Bar**: Hexagon brand mark + Glowing Category Pill.
  - **Massive Headline**: 78px bold chalkboard typography with drop shadow.
  - **Glowing Hook Pill**: Outer Gaussian glow with vector icons (`27x CHEAPER THAN o1`, `94.5% COMPUTE SAVED`).
  - **Hero Focal Geometry**: Manim constellation, leaderboard, or hardware matrix.
  - **Frosted Math Plate**: Authentic Computer Modern $\mathrm{\LaTeX}$ formula SVG.
  - **Mobile UI Safe Zone**: Bottom $35\%$ darkened to ensure zero collision with YouTube mobile buttons.
- Exports both uncompressed **PNG** and web-optimized **JPEG** ($< 2\text{ MB}$).

#### Step 7: Autonomous YouTube Shorts Distribution (`pipeline/publisher.py`)
- Direct upload via **YouTube Data API v3**.
- Auto-generates viral SEO title, structured description with chapter timestamps, targeted hashtag set, and auto-posts a pinned discussion comment.
- Automatically uploads the custom 1080×1920 high-CTR poster thumbnail.

---

## 4. Operator Manual: How to Run & Utilize Every Feature

### Method 1: Interactive Web Studio (GUI Cockpit)

The Web Studio is a single-screen control center accessible directly in your browser.

```bash
# Start the Web Studio server
python3 studio/run_studio.py --port 8000
```
Then open: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

#### Studio Controls:
1. **Left Panel — Content & Script Lab**:
   - `Trending`: Click any paper scraped from Hugging Face / arXiv to populate the production form.
   - `Templates`: View all 6 pre-built script templates.
   - `Beats`: Inspect timestamps, voiceover text, and $\mathrm{\LaTeX}$ formulas beat-by-beat.
2. **Center Panel — 9:16 Broadcast Theater**:
   - Dropdown to select and play any of the 11 produced master shorts.
   - Clickable keyframe filmstrip: click any thumbnail to zoom into full resolution.
3. **Right Panel — Audio & Production Cockpit**:
   - A/B/C Audio Deck: Listen to speech, ambient synth, or ducked master mix independently.
   - Sliders: Adjust Duck Gain and Swell Gain.
   - Button **"🎹 Test Synth Ducking"**: Generates and plays an on-the-fly 6-second preview in $< 0.1\text{s}$.
   - Big Button **"⚡ Produce Broadcast Short"**: Triggers video production with real-time SSE terminal logs streaming in the bottom drawer!

---

### Method 2: 1-Click Autonomous Producer CLI (`auto_produce.py`)

Run autonomous video generation from your terminal:

```bash
# 1. Produce by Topic name (e.g. DeepSeek-R1):
python3 pipeline/auto_produce.py --topic "DeepSeek-R1" --category benchmark_news --quality -qm

# 2. Produce directly from an arXiv paper ID:
python3 pipeline/auto_produce.py --arxiv 2407.08608 --quality -qm

# 3. Super-fast 480p preview render (~15 seconds):
python3 pipeline/auto_produce.py --topic "FlashAttention-3" --quality -ql

# 4. Preview YouTube metadata without uploading (Dry-Run):
python3 pipeline/auto_produce.py --topic "DeepSeek-V3" --dry-run-publish

# 5. Disable ambient background music:
python3 pipeline/auto_produce.py --topic "DeepSeek-R1" --no-music
```

---

### Method 3: Daily Trending Scraper & Cron Auto-Pilot (`batch_digest.py`)

Automate daily research tracking and scheduling:

```bash
# 1. List today's top 10 trending AI papers with scores and categories:
python3 pipeline/batch_digest.py --list --limit 10

# 2. Automatically produce a short for the #1 top trending paper:
python3 pipeline/batch_digest.py --auto --quality -qm --dry-run-publish

# 3. Run automated daily cron check (safe for system crontab / launchd):
# Checks if a video was produced in the last 20 hours; if not, produces the #1 paper:
python3 pipeline/batch_digest.py --cron --publish --privacy unlisted
```

---

### Method 4: High-CTR Poster Generator CLI (`generate_thumbnail.py`)

Generate 1080×1920 YouTube Shorts posters on demand:

```bash
# 1. Generate posters for all available script templates:
python3 scripts/generate_thumbnail.py --all

# 2. Generate a custom poster with hook badge override:
python3 scripts/generate_thumbnail.py --topic "DeepSeek-R1" --badge "27x CHEAPER THAN o1"

# 3. Generate from an explicit spec JSON:
python3 scripts/generate_thumbnail.py --spec pipeline/templates/architecture_deepseek_v3.json
```
Generated posters are saved to `public/thumbnails/`.

---

## 5. Action Items & Configuration Required from You

### ✅ What is ALREADY Working (Zero Setup Required)
- **Neural Voice**: Kokoro ONNX model and 24kHz voice vectors are installed and loaded locally.
- **Audio Synthesizer & Ducking**: Runs 100% locally with zero external audio assets.
- **Manim Engine**: Mathematical chalkboard scenes and $\mathrm{\LaTeX}$ SVGs render locally via Pycairo/FFmpeg.
- **Web Studio**: The FastAPI server is currently running live on port `8000`.
- **Existing Library**: All 11 master videos, keyframe filmstrips, and 6 poster thumbnails are pre-rendered and ready to inspect.

---

### 🔑 External Credentials Required from You (When Needed)

#### 1. Gemini API Key (`GEMINI_API_KEY`)
- **When needed**: Only when you want to generate a **brand-new script** for an arbitrary paper that doesn't already have a template in `pipeline/templates/`.
- **How to provide**:
  ```bash
  export GEMINI_API_KEY="your-gemini-api-key-here"
  ```
  *(If omitted, the engine will automatically use existing cached templates in `pipeline/templates/` without making an API call).*

#### 2. YouTube Data API v3 OAuth (`client_secrets.json`)
- **When needed**: Only when you want the pipeline to **actually upload** videos to your live YouTube channel via `--publish`.
- **How to provide**:
  1. Open the [Google Cloud Console](https://console.cloud.google.com/).
  2. Enable the **YouTube Data API v3**.
  3. Create an **OAuth 2.0 Client ID** (Application type: *Desktop Application*).
  4. Download the JSON file and save it as:
     ```bash
     pipeline/client_secrets.json
     ```
  5. The first time you run with `--publish`, a browser tab will open asking you to authorize your YouTube channel once. Your token will be saved to `pipeline/youtube_token.json` for fully unattended publishing.
  6. *(You can test everything without credentials using `--dry-run-publish`, which generates the viral SEO title, tags, description, and pinned comment without uploading).*

---

## 6. Complete Codebase Map & Directory Structure

```
themodelverse-shorts/
├── GOTO_GUIDE.md                     # This master guide
├── pipeline/                         # Core backend pipeline
│   ├── config.py                     # Design tokens, color palette, audio settings
│   ├── auto_produce.py               # 1-Click autonomous producer CLI
│   ├── run_pipeline.py               # Manim rendering & FFmpeg broadcast muxer
│   ├── audio_synthesizer.py          # Kokoro TTS + Procedural SFX + Ducking mixer
│   ├── thumbnail_generator.py        # 1080x1920 High-CTR poster generator
│   ├── script_generator.py           # Gemini 2.5 Flash script synthesis
│   ├── batch_digest.py               # Daily trending paper scraper & cron daemon
│   ├── arxiv_fetcher.py              # arXiv metadata and abstract ingestion
│   ├── publisher.py                  # YouTube Data API v3 autonomous publisher
│   └── templates/                    # Production-ready short specs
│       ├── architecture_deepseek_v3.json
│       ├── benchmark_deepseek_r1.json
│       ├── mechanism_deepdive_flashattention-3.json
│       ├── mechanism_kv_cache.json
│       └── showdown_deepseek_vs_gpt4.json
├── studio/                           # Interactive Web Studio
│   ├── server.py                     # FastAPI REST API + SSE log streaming
│   ├── run_studio.py                 # Studio CLI launcher
│   └── static/                       # Chalkboard dark-mode Web UI
│       ├── index.html                # 3-column studio cockpit
│       ├── studio.css                # 3Blue1Brown chalkboard dark styling
│       └── studio.js                 # Video player, audio decks, SSE runner
├── scripts/                          # Standalone utilities
│   ├── generate_thumbnail.py         # Poster generator CLI
│   └── synth_music_generator.py      # Standalone procedural music & ducking engine
├── manim_engine/                     # Vector animation engine
│   ├── base_scene.py                 # 3b1b Blackboard camera & safe zones
│   ├── primitives/                   # Chalkboard visual components
│   │   ├── leaderboard.py            # Animated benchmark podiums & progress bars
│   │   ├── chalkboard_captions.py    # Synchronized kinetic caption rendering
│   │   ├── stat_counter.py           # Animated metric counters
│   │   └── split_screen.py           # Dual-model comparison layouts
│   └── scenes/                       # Full category animation scenes
│       ├── architecture_scene.py     # MoE 256 constellation & top-8 lasers
│       ├── benchmark_scene.py        # AIME leaderboard & cost shockwaves
│       ├── mechanism_scene.py        # Attention kernels & memory caching
│       └── showdown_scene.py         # Model vs model split-screen
├── public/                           # Production assets & outputs
│   ├── thumbnails/                   # Generated 1080x1920 posters
│   ├── math_svgs/                    # Authentic Computer Modern LaTeX formulas
│   ├── math_pngs/                    # Cached transparent formula plates
│   └── audio/                        # Rendered narration, soundtracks, master audio
├── kokoro_models/                    # Kokoro ONNX voice models (cached locally)
└── final_*.mp4                       # Broadcast master video outputs (11 ready)
```

---

## 7. Command Reference & Cheat Sheet

| Task | Command |
|---|---|
| **Open Web Studio** | Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| **Launch Studio Server** | `python3 studio/run_studio.py --port 8000` |
| **Produce DeepSeek-R1 Short** | `python3 pipeline/auto_produce.py --topic "DeepSeek-R1" --category benchmark_news` |
| **Produce DeepSeek-V3 Short** | `python3 pipeline/auto_produce.py --topic "DeepSeek-V3" --category architecture_breakdown` |
| **Produce FlashAttention-3 Short** | `python3 pipeline/auto_produce.py --topic "FlashAttention-3" --category mechanism_deepdive` |
| **Produce from arXiv ID** | `python3 pipeline/auto_produce.py --arxiv 2407.08608` |
| **List Today's Trending Papers** | `python3 pipeline/batch_digest.py --list` |
| **Daily Auto-Pilot Cron Run** | `python3 pipeline/batch_digest.py --cron --publish --privacy unlisted` |
| **Generate All Poster Thumbnails**| `python3 scripts/generate_thumbnail.py --all` |
| **Test YouTube Metadata Preview** | `python3 pipeline/auto_produce.py --topic "DeepSeek-R1" --dry-run-publish` |
| **Test Procedural Synth Music** | `python3 scripts/synth_music_generator.py` |
