# 📐 The Model Verse — Autonomous AI Shorts Engine

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Manim CE](https://img.shields.io/badge/Manim%20CE-v0.19%2B-brightgreen.svg)](https://www.manim.community/)
[![Tests](https://img.shields.io/badge/tests-42%20passed-success.svg)](test/)
[![Style: 3Blue1Brown](https://img.shields.io/badge/style-3Blue1Brown%20Chalkboard-9cf.svg)](manim_engine/)

**The Model Verse** is a fully autonomous broadcast engine that transforms cutting-edge research publications (arXiv, Hugging Face) and viral open-source AI kernels (GitHub Trending) into broadcast-grade, **3Blue1Brown-style vertical explainer videos (9:16 at 1440p60 QHD)** for YouTube Shorts, Instagram Reels, and TikTok.

---

## 📖 Master Documentation

- 🤖 **[`AGENTS.md`](AGENTS.md)** — Autonomous agent operating manual, roles, rules, and prompt directives.
- 🏛️ **[`ARCHITECTURE.md`](ARCHITECTURE.md)** — Complete 7-stage pipeline architecture and system specifications.
- 📜 **[`CHANGELOG.md`](CHANGELOG.md)** — Chronological release history from v1.0 through v5.2.
- 🤝 **[`CONTRIBUTING.md`](CONTRIBUTING.md)** — Contributor guidelines, testing standards, and PR protocol.

---

## ✨ Key Capabilities (Visual Engine v5.2)

1. **GitHub Trending & Live Code Execution Visualizer**
   - Automatically ingests trending open-source AI repositories (vLLM, SGLang, BitNet, llama.cpp, DeepSeek MLA).
   - Renders animated chalkboard code blocks with macOS window chrome, multi-language syntax highlighting, active execution line sweeps, and real-time GPU register monitors.
2. **Automated Multi-Model Showdown & Radar Comparison Engine**
   - Parses benchmark tables from arXiv LaTeX source.
   - Renders animated Horizontal Drag-Race Bars and 5-axis Spider/Radar Pareto Frontier plots.
3. **Authentic arXiv Vector Figure Extraction**
   - Downloads e-print LaTeX source tarballs, extracts native publication figures (PDF/EPS/SVG), and recolors them for `#0A0D14` carbon chalkboard aesthetics.
4. **Real-Time YouTube Retention Feedback Loop**
   - Connects to YouTube Data API v3 to calculate real-time audience velocity, biasing daily candidate selection toward high-performing domains (`hardware_efficiency: 1.44x`) and optimizing narration pacing (1.12x TTS).
5. **Tactile Foley Sound Design & Micro-SFX Engine**
   - Automatically layers sub-bass drops, whooshes, mechanical clicks, and glass pings aligned to exact Manim visual animation triggers.
6. **Continuous Micro-Motion (Zero Frozen Frames)**
   - Continuous vector flow fields, synaptic propagation waves, optical attention prisms, and 2.5D loss landscape gradient descents.

---

## 🚀 Quick Start

### 1. Daily Autonomous Production Daemon
```bash
# Ingest mixed arXiv + GitHub trending breakthroughs and produce 1 reel
python3 pipeline/daily_shorts_daemon.py --run-now --source mixed --count 1

# Produce a specific arXiv paper
python3 pipeline/daily_shorts_daemon.py --run-now --arxiv 2407.08608

# Ingest only GitHub trending AI repositories
python3 pipeline/daily_shorts_daemon.py --run-now --source github --count 1

# Dry-run paper discovery, script synthesis, and pedagogy audit without rendering
python3 pipeline/daily_shorts_daemon.py --dry-run --count 1
```

### 2. Run Test Suite
```bash
pytest
```

---

## 📂 Repository Structure

- [**`pipeline/`**](pipeline/): Ingestion, scriptwriting, pedagogy critic, visual director, acoustic aligner, YouTube publisher.
- [**`manim_engine/`**](manim_engine/): 3Blue1Brown chalkboard primitives, visual blueprints, showdown engine, code block visualizer.
- [**`public/`**](public/): Zero-license Foley SFX library, rendered video archive, math SVGs, and brand assets.
- [**`test/`**](test/): Comprehensive automated test suite (42 unit and integration tests).
