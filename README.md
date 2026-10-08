# 📐 The Model Verse & Project Aether — Autonomous Video Production Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Manim CE](https://img.shields.io/badge/Manim%20CE-v0.19%2B-brightgreen.svg)](https://www.manim.community/)
[![Tests](https://img.shields.io/badge/tests-367%20passed-success.svg)](test/)
[![Style: 3Blue1Brown](https://img.shields.io/badge/style-3Blue1Brown%20Chalkboard-9cf.svg)](manim_engine/)
[![Aether: 3D Virtual Studio](https://img.shields.io/badge/Aether-3D%20Cinematic-purple.svg)](aether/)

The Model Verse is an autonomous video production platform housing two distinct, high-capability video generation engines operating independently and bridged by a clean, decoupled shared contract layer:

1. **The Model Verse Shorts Engine (`pipeline/` + `manim_engine/`)**: A deterministic, 2D programmatic mathematical and educational motion graphics studio rendering broadcast-grade, **3Blue1Brown-style vertical explainer videos (9:16 at 1440p60 QHD)** for YouTube Shorts, Instagram Reels, and TikTok.
2. **Project Aether (`aether/`)**: An autonomous, multi-shot 3D cinematic generative virtual studio utilizing state-of-the-art video foundation models (Google Veo 3.1, Kling 3.0, Runway Gen-4.5, CogVideoX), persistent 3D world state tracking, 6-tier complexity planning, speculative 480p draft gating, a 6-critic Council, surgical inpainting repair, and offline Dream-RSI meta-learning.

---

## 📖 Master Documentation

- 🏛️ **[`ARCHITECTURE.md`](ARCHITECTURE.md)** — Comprehensive dual-engine system architecture, 38-file comparative audit, and shared contract specifications.
- 🤖 **[`AGENTS.md`](AGENTS.md)** — Autonomous agent operating manual, roles, rules, and prompt directives.
- 📜 **[`CHANGELOG.md`](CHANGELOG.md)** — Chronological release history from v1.0 through v5.2.
- 🤝 **[`CONTRIBUTING.md`](CONTRIBUTING.md)** — Contributor guidelines, testing standards, and PR protocol.

---

## 🔗 Unified Yet Decoupled Architecture (`aether/shared_contract.py`)

The platform connects both engines without circular dependencies through a dedicated shared contract layer:

- **`ScriptToFilmSceneAdapter`**: Converts structured 6-beat educational scripts (`VideoSpec` generated from arXiv publications) directly into cinematic `DirectorProductionBrief` packages with rich scene staging, camera kinematics, and lighting parameters.
- **`EducationalAssetConditioningPackage`**: Bundles Manim-rendered SVGs, benchmark showdown radar plots, and native arXiv vector/raster figures as visual conditioning references for Aether Complexity Levels 1–4.
- **`DualEnginePipelineConfig` & `HybridRenderMode`**: Configures multi-engine render allocations, supporting pure 2D chalkboard animations, pure 3D cinematic sequences, or hybrid composites (e.g. 2D Manim mathematical HUD overlaid on 3D cinematic backdrops).

---

## ✨ Key Capabilities

### Engine 1: The Model Verse Shorts (2D Educational Motion Graphics)
1. **Authentic arXiv Vector & Raster Figure Extraction**: Automatically downloads e-print LaTeX source tarballs, extracts native publication figures (PDF/EPS/SVG), and renders 350 DPI unsharp-masked rasters for `#0A0D14` carbon chalkboard aesthetics.
2. **GitHub Trending & Live Code Execution Visualizer**: Ingests trending open-source AI kernels (vLLM, SGLang, BitNet, llama.cpp) and renders animated chalkboard code blocks with macOS window chrome, syntax highlighting, and live GPU register monitors.
3. **Multi-Model Showdown & Radar Comparison Engine**: Parses LaTeX benchmark tables into animated Horizontal Drag-Race Bars and 5-axis Spider/Radar Pareto Frontier plots.
4. **200 Hz Acoustic Forced Alignment & Foley Engine**: Tracks speech energy envelopes to snap word boundaries to audio dips with $\pm 75\text{ms}$ precision, enforcing the **Frame-Ahead Rule** (-33ms to -66ms) with procedural tactile sound design.
5. **Closed-Loop Spatial Layout Self-Healing**: Detects text/diagram collisions using headless VLM keyframe inspection and applies deterministic AABB spatial repulsion forces.

### Engine 2: Project Aether v2 (3D Autonomous Cinematic Virtual Studio)
1. **Persistent 3D World State Graph**: Maintains character rosters, wardrobe damage, prop possession, and camera kinematics across sequential shots with branching and rollbacks.
2. **6-Tier Complexity Planning (Levels 0–5)**: Classifies shots from prompt-only cutaways (L0) to reference conditioning (L1), keyframe interpolation (L2), 2D pose trajectories (L3), 3D spatial blocking (L4), and deterministic physics simulation (L5).
3. **Speculative 480p Draft Gating & Critic Council**: Rapidly pre-screens 480p low-latency drafts through 6 domain critics (Visual, Temporal, Continuity, Lip-Sync, Physics, Audio) and 5 binary hard gates before full 1080p latent upscaling.
4. **Spatio-Temporal Masking & Surgical Defect Repair**: Uses regional temporal diffusion inpainting and protected region masks to fix defects without re-rendering entire scenes.
5. **Dream-RSI Meta-Learning**: Optimizes multi-model compilation policies offline over historical replay DAG trees at zero generative API cost.

---

## 🚀 Quick Start

### 1. The Model Verse 2D Shorts Pipeline
```bash
# Ingest an arXiv paper and run full 2D Manim production
python3 pipeline/run_pipeline.py --arxiv 2407.08608

# Ingest mixed arXiv + GitHub trending breakthroughs and produce 1 reel
python3 pipeline/daily_shorts_daemon.py --run-now --source mixed --count 1

# Dry-run paper discovery, script synthesis, and pedagogy audit without rendering
python3 pipeline/daily_shorts_daemon.py --dry-run --count 1
```

### 2. Project Aether 3D Autonomous Cinematic Director
```bash
# Run autonomous director simulation on a narrative premise (dry-run mode)
python3 -m aether.director --brief "Autonomous robotics in silicon cleanroom" --dry-run

# Run Aether with budget limits and target model engines
python3 -m aether.director --brief "Quantum computing cryogenic breakthrough" --budget 50.0 --models veo_3_1 kling_3_0
```

### 3. Run Test Suite
```bash
# Run all unit and integration tests across both engines (367+ tests)
pytest

# Run only Project Aether tests
pytest test/test_aether_*.py

# Run only arXiv figure extraction tests
pytest test/test_arxiv_figure_extraction.py
```

---

## 📂 Repository Structure

- [**`aether/`**](aether/): Project Aether 3D cinematic virtual studio (world state graph, complexity compiler, council critics, surgical repair, Dream-RSI teacher, and shared contract adapter).
- [**`pipeline/`**](pipeline/): Ingestion, scriptwriting, pedagogy critic, visual director, acoustic aligner, YouTube publisher, and Aether director pipeline wrapper.
- [**`manim_engine/`**](manim_engine/): 3Blue1Brown chalkboard primitives, visual blueprints, showdown engine, code block visualizer.
- [**`public/`**](public/): Zero-license Foley SFX library, rendered video archive, math SVGs, and arXiv chalkboard figure cache.
- [**`test/`**](test/): Comprehensive automated test suite (367+ unit and integration tests).
