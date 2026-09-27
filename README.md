# 📐 The Model Verse — Autonomous Short Video Engine

Transforming dense frontier AI research papers into broadcast-grade, **1080×1920 YouTube Shorts** in pure **3Blue1Brown mathematical chalkboard style**.

---

### 📖 Master Documentation
For the complete technical blueprint, roadmap, agent operating manual, and version history, see:
- 🗺️ **[PLAN.md](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/PLAN.md)** — Master execution plan & roadmap for Visual Engine 2.0.
- 🤖 **[AGENTS.md](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/AGENTS.md)** — Autonomous agent operating guide, constraints & primitive standards.
- 📜 **[CHANGELOG.md](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/CHANGELOG.md)** — Chronological release history & bugfix log.
- 📘 **[GOTO_GUIDE.md](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/GOTO_GUIDE.md)** — Comprehensive operator manual & quickstart.

---

### 🚀 Quick Start in 60 Seconds

#### 1. Launch the Interactive Web Studio
```bash
python3 studio/run_studio.py --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to browse trending papers, preview 9:16 videos, tune audio ducking, and trigger 1-click generation with live SSE terminal logs.

#### 2. Produce a Video via CLI
```bash
# Produce DeepSeek-R1 Short:
python3 pipeline/auto_produce.py --topic "DeepSeek-R1" --category benchmark_news --quality -qm

# Ingest an arbitrary arXiv paper:
python3 pipeline/auto_produce.py --arxiv 2407.08608 --quality -qm
```

#### 3. Generate High-CTR Posters
```bash
python3 scripts/generate_thumbnail.py --all
```

---

### 📂 Key Directory Links
- [**`pipeline/`**](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/pipeline/): Core backend automation (scripting, Kokoro audio, Manim rendering, YouTube publishing).
- [**`studio/`**](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/studio/): FastAPI Web Studio and chalkboard UI.
- [**`manim_engine/`**](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/manim_engine/): 3Blue1Brown blackboard animation scenes.
- [**`public/thumbnails/`**](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/public/thumbnails/): Generated 1080×1920 poster thumbnails.
- [**`public/math_svgs/`**](file:///Users/amankumar/Aman/Test-WOrkspace/themodelverse-shorts/public/math_svgs/): Computer Modern $\mathrm{\LaTeX}$ mathematical formulas.
