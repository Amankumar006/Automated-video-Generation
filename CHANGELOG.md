# Changelog — The Model Verse Shorts

All notable changes, architectural pivots, bug fixes, and feature additions to this repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.2.0] - 2026-10-03

### 💻 GitHub Trending AI & Live Code Execution Trace Visualizer
- **GitHub Trending & Kernel Ingestion Engine (`pipeline/github_trending_fetcher.py`)**:
  - Automatically monitors viral open-source AI repositories (vLLM, SGLang, BitNet, llama.cpp, DeepSeek kernels) via GitHub Search API with fallback to curated high-impact execution kernels.
  - Curated kernels for SGLang (RadixAttention prefix tree cache), vLLM (PagedAttention discrete block allocation), BitNet (1-bit Ternary GEMM weights), DeepSeek (MLA compression), and llama.cpp (GGML quantized SIMD).
- **Chalkboard Code & AST Execution Visualizer (`manim_engine/primitives/code_execution_engine.py`)**:
  - Implemented `BlueprintChalkboardCodeBlock` with minimalist macOS window chrome, red/yellow/green traffic lights, filename pill, and language badge (`PYTHON`, `CUDA`, `C++`).
  - Tokenized syntax highlighting for keywords (`#C084FC`), functions (`#60A5FA`), strings (`#10B981`), comments (`#94A3B8`), and numbers (`#F59E0B`).
  - Active execution line glowing scan with indicator notch aligned to executing line.
  - Live hardware memory register status pill (e.g. `⚡ RADIX HIT: +2,048 TOKENS REUSED`).
  - High-contrast emerald bottom delta badge (`#10B981`) highlighting efficiency gains.
- **Pipeline Integration (`pipeline/visual_director.py`, `pipeline/daily_shorts_daemon.py`)**:
  - Automatically routes Beats 3 and 4 to `chalkboard_code_block` when code snippets are present.
  - Added `--source` flag to `daily_shorts_daemon.py` supporting `arxiv`, `github`, and `mixed` candidate discovery.
  - Guaranteed 9:16 vertical safe zone clearance ($> 1.0$ unit buffer above kinetic subtitles).
- **Testing & Verification**:
  - Added `test/test_github_trending_fetcher.py` and `test/test_code_execution_engine.py` (12 tests passing).
  - Headless keyframe visual verification completed (`test_chalkboard_code_block.png`).

---

## [5.1.0] - 2026-10-03

### 🏎️ Automated Multi-Model Showdown & Radar Comparison Engine
- **Benchmark Extractor (`pipeline/benchmark_extractor.py`)**:
  - Parses LaTeX benchmark tables from arXiv e-print bundles into normalized quantitative metrics.
  - Structured fallbacks for throughput (TFLOPS), speedup multipliers, latency, and accuracy.
- **Horizontal Benchmark Race Bars (`manim_engine/primitives/showdown_engine.py`)**:
  - Animated progress tracks with glowing heads and hero highlight rows (`#10B981`).
  - Side-by-side comparison of 3–4 models/kernels with victory delta badge.
- **Radar / Spider Pareto Frontier Plot (`BlueprintRadarParetoPlot`)**:
  - Concentric 5-axis radial radar plot evaluating multi-dimensional trade-offs (Throughput, VRAM Efficiency, Accuracy, Context Length, Cost).
  - Semi-transparent hero polygon fill with contrasting baseline overlays.
- **Visual Director Assignment**:
  - Beat 5 dynamically assigned to `horizontal_race_bars` or `radar_pareto_plot`.
- **Testing**: Added `test/test_showdown_engine.py` (6 unit tests, headless render verification).

---

## [5.0.0] - 2026-10-02

### 🌊 Continuous Micro-Motion Updaters & Zero-Frozen-Frame Architecture
- **Continuous Updaters**:
  - Replaced static diagram dead-frames (4–6s freezes) with continuous mathematical motion via Manim `add_updater` and `ValueTracker`.
  - Continuous wave phase-travel, streaming particle swarms, glowing halo pulses, and camera drift.
- **Physics Simulation Primitives (`manim_engine/primitives/physics_simulations.py`)**:
  - `BlueprintVectorFlowField`: Dynamic velocity streamlines and particle drift.
  - `BlueprintNeuralActivationWave`: Synaptic propagation waves across layered neural nodes.
  - `BlueprintAttentionPrismRefraction`: Optical beam splitting into Query, Key, and Value vectors.
  - `BlueprintOptimizationLandscape`: 2.5D loss landscape gradient descent trajectory rolling into minima.

---

## [4.5.0] - 2026-10-01

### 📈 Real-Time YouTube Retention Feedback Loop & Autonomous Upload Daemon
- **YouTube Retention Analytics (`pipeline/analytics_feedback.py`)**:
  - Direct integration with YouTube Data API v3 and OAuth2 token refresh.
  - Real-time video performance query calculating viewer retention curves, average view duration, and view velocity (views/hour).
  - Dynamic domain velocity multipliers (e.g. `hardware_efficiency: 1.44x`, `multimodal_diffusion: 1.29x`).
  - Automated pacing recommendations: optimal narration speed (1.12x TTS) and hook duration ($\le 7.2\text{s}$).
- **Autonomous Daily Shorts Daemon (`pipeline/daily_shorts_daemon.py`)**:
  - 5 research-backed pre-peak upload windows (01:00, 05:00, 09:00, 12:00, 16:00 UTC).
  - End-to-end headless execution from discovery to 1440p60 QHD rendering, thumbnail generation, and YouTube upload.

---

## [4.0.0] - 2026-09-29

### 📐 Composable Visual Blueprints & Authentic ArXiv Figure Extraction
- **Composable Visual Blueprints (`manim_engine/primitives/visual_compositions.py`)**:
  - Modular, full-screen 3Blue1Brown chalkboard layout registry replacing brittle SVG synthesizers.
  - `BlueprintPipelineStages`, `BlueprintSplitFlow`, `BlueprintCatalogRouting`, `BlueprintProjectionRays`, `BlueprintBarrierSeparation`, `BlueprintDecisionTree`, `BlueprintLayerStack`, `BlueprintConvergenceFunnel`.
- **Native ArXiv Vector Figure Extractor (`pipeline/arxiv_vector_extractor.py`)**:
  - Downloads arXiv LaTeX e-print bundles (`.tar.gz`) and extracts authentic publication figures (PDF, EPS, SVG).
  - Chalkboard path recoloring engine converting white backgrounds and black strokes into `#0A0D14` carbon aesthetics with `#38BDF8` cyan and `#34D399` emerald accents.

---

## [3.5.0] - 2026-09-28

### 🎨 Dynamic Beat Vector & SVG Synthesizer
- **Bespoke Beat Diagrams (`pipeline/svg_synthesizer.py`)**:
  - LLM-assisted vector synthesis generating script-specific SVGs for individual beats based on SVO actions and everyday analogies.
  - Deterministic procedural fallback algorithms guaranteeing zero rendering failures.
- **Auditory-Visual SFX Layering**:
  - Tactile Foley sound design integration (`public/sfx/`) with automated millisecond-level mixdown in `pipeline/audio_synthesizer.py`.

---

## [3.0.0] - 2026-09-27

### 🎙️ Script Pedagogy Critic & Autonomous Self-Refinement
- **Script Critic (`pipeline/script_critic.py`)**:
  - Automated Flesch-Kincaid grade level evaluation (target: Grade 6.0–8.0).
  - Anti-jargon dictionary banning heavy academic jargon ("orchestration", "competence-aware", "bootstrap").
  - Physical analogy enforcement ensuring intuitive metaphors (sculptor, library, clouds, mirror).
  - Autonomous closed-loop self-refinement rewriting beats until quality gates pass.

---

## [2.0.0] - 2026-09-26

### 🔬 Visual Engine 2.0 & Modular 3Blue1Brown Primitives
- **Modular 3b1b Primitives**:
  - Robotics & TAMP (`CoupledCanvas`, `ParametricKinematicArm`, `ASTMorphTree`, `SandboxIsolationPod`).
  - Deep Learning & SAEs (`SAEConstellation`, `TransformerAttentionGrid`, `SparseMoELattice`, `RoutingRibbon`).
  - Search & Metrics (`DynamicSearchTree`, `RadialScoreMeter`, `DualMetricGauge`).
- **Declarative Visual Scene Graph (VSG) (`pipeline/vsg_schema.py`)**:
  - Pydantic schema with SVO semantic triples and explicit LaTeX formula bindings.
- **Acoustic Forced Alignment (`pipeline/aligner.py`)**:
  - 200 Hz energy valley snapping with the **Frame-Ahead Rule** (-33ms to -66ms) for frame-accurate animation timing.

---

## [1.0.0] - 2026-09-24

### 🚀 Initial Autonomous Video Generation Engine
- Autonomous pipeline translating arXiv papers into YouTube Shorts.
- Kokoro-82M neural text-to-speech synthesis (`am_adam`).
- Manim Community Edition vector rendering at 1080x1920.
- Procedural audio mixing with background synthwave soundtracks.
