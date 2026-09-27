# THE MODEL VERSE — MASTER EXECUTION PLAN
## Visual Engine 2.0: Dynamic Semantic Choreography & Pedagogy Overhaul

> **Version:** 2.0.0-alpha  
> **Status:** Active / In Progress  
> **Last Updated:** 2026-09-26  
> **Author:** The Model Verse Engineering Team & Research Agents  

---

## 1. Executive Summary & Vision

**The Goal:** Transform *The Model Verse Shorts* from a formulaic, template-slotted animation generator into a **world-class, autonomous 3Blue1Brown-style visual pedagogical engine**.

### Core Quality Philosophy:
1. **Invariant Preservation**: Every visual element (position, stroke width, color, trajectory) must strictly encode a mathematical, physical, or algorithmic property. Zero decorative clutter.
2. **Zero "SaaS Slide Deck" Cards**: Replace generic rounded rectangular cards, bullet points, and marketing badges with living geometric manifolds, state machines, and dynamic diagrams.
3. **Auditory-Visual Complementarity**: Spoken voiceover carries narrative intuition; screen graphics carry geometry, spatial mechanics, and structural transformations; text is strictly reserved for mathematical notation, variables, and state badges.
4. **Absolute Semantic Synchrony (SVO Mapping)**: When the script says *"X explores Y and prunes Z"*, the animation must visibly expand candidate branches, evaluate kinematic invariants, and sever invalid nodes using the **Frame-Ahead Rule** (visuals trigger 33–66ms prior to phonetic word onset).
5. **Continuous Object Constancy (Morph, Don't Cut)**: Smooth topological homotopies (`Transform`, `ReplacementTransform`) preserve mental models without abrupt context breaks.
6. **Mobile 9:16 Safe-Zone Compliance**: All critical geometry is contained within $X \in [-3.2, 3.2]$, $Y \in [-5.5, 5.5]$ ($Y: 480\text{px} \dots 1180\text{px}$) to avoid YouTube Shorts and TikTok UI overlays.

---

## 2. Root-Cause Diagnosis (Engine 1.0 Autopsy)

| Component | Engine 1.0 Bottleneck | Engine 2.0 Solution |
| :--- | :--- | :--- |
| **Dispatcher** | Coarse 4-category enum (`CATEGORY_SCENE_MAP`) maps papers strictly to 4 rigid Python files regardless of topic. | **Dynamic Scene Compiler** based on an open Domain Paradigm Taxonomy. |
| **Scene Logic** | Hardcoded monolithic objects (e.g., $K_1 \dots K_5$ VRAM slots in `deepdive_scene.py`, 256 dots in `breakdown_scene.py`). | **Composable Primitive Registry**: modular, parameterizable visual actors. |
| **Math Integration** | Math formulas compiled to SVGs are ignored in `showdown_scene.py` or placed as static wallpaper. | **Active Mathematical Mobjects**: formulas drive transformations and parameter sliders. |
| **Pacing** | Blind linear scaling (`scale_times`) over entire beats; desynchronized from voiceover. | **Acoustic Forced Alignment**: word-level timestamps (WhisperX/Phonemes) trigger exact visual actions. |
| **Quality Control** | Audio and video are muxed blindly without semantic inspection. | **Closed-Loop VLM Critic**: Gemini Vision inspects keyframes against script before release. |

---

## 3. Architecture Blueprint: Visual Engine 2.0

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PAPER INGESTION & TAXONOMY CLASSIFICATION                           │
│    - arXiv PDF / LaTeX tarball extraction                              │
│    - Taxonomy Classification: Robotics, SAE, MoE, Search, etc.        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. SVO STORYBOARDING & VISUAL SCENE GRAPH (VSG)                        │
│    - 6-beat narrative script                                           │
│    - Subject-Verb-Object (SVO) semantic action triples                 │
│    - LaTeX mathematical binding specifications                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ACOUSTIC SYNTHESIS & WORD-LEVEL FORCED ALIGNMENT                    │
│    - Neural TTS voiceover (Kokoro / ElevenLabs)                        │
│    - Phoneme-level aligner (WhisperX / CTC) -> {word: t_start, t_end} │
│    - Procedural Lo-Fi ambient music + dynamic ducking                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. DYNAMIC MANIM 2.0 SCENE COMPILER                                    │
│    - Reusable 3b1b Primitive Registry (Trees, Kinematics, SAEs, MoE)   │
│    - Event Scheduler with Frame-Ahead Rule (t_trigger = t_word - 40ms) │
│    - Parameterized Blackboard Canvas in 9:16 Vertical Space            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. CLOSED-LOOP VLM QUALITY AUDITOR & ARTIFACT PACKAGING                │
│    - Headless fast keyframe extraction (Beats 1 to 6)                  │
│    - Gemini Vision semantic QA inspection (Checks: No-Cards, Sync)    │
│    - Master broadcast MP4 muxing + YouTube Shorts Publishing          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Phase Implementation Roadmap

### Phase 1: Modular 3b1b Primitive Registry (Canvas Building Blocks)
- [x] **1.1 Robotics & Planning Primitives (`manim_engine/primitives/robotics/`)**
  - [x] `CoupledStateSpace`: Split canvas manager coordinating discrete task logic (top) and continuous configuration space (bottom).
  - [x] `ConstraintProjectionSheaf`: Translucent volumetric beam connecting discrete actions to admissible continuous subspaces.
  - [x] `ParametricKinematicArm`: Forward kinematics analytical arm with capsule hulls and $SE(2)$ end-effector triads.
  - [x] `GeometricRefinementPulse`: Collision explosion, witness generation, and backward invalidation shockwaves.
  - [x] `ASTMorphTree`: Data-driven Abstract Syntax Tree with syntax-specific nodes (Hexagons, Pills, Diamonds, Holes).
  - [x] `SandboxIsolationPod`: Clean-room containment chamber with test suite assertion ledger.
- [x] **1.2 Deep Learning & Mechanistic Interpretability Primitives (`manim_engine/primitives/neural/`)**
  - [x] `SAEConstellation`: Residual stream coordinate plane, entangled vector with interference rings, starburst dictionary, top-$k$ sparsity sieve.
  - [x] `TransformerAttentionGrid`: Multi-head Q/K/V split, $N \times N$ attention heatmap grid, curved routing ribbons with Value packets.
  - [x] `SparseMoELattice`: Expert constellation, router radar scan, top-$k$ laser dispatch, shared foundation core, load-balancing manometers.
  - [x] `ContrastiveHypersphere` & `ScoreBasedDiffusionField`: Repulsion/attraction springs and vector field particle flow.
- [x] **1.3 Algorithmic & Search Primitives (`manim_engine/primitives/search/`)**
  - [x] `DynamicSearchTree`: Frontier expansion, parent rewiring, MCTS 4-beat cycle (Select, Expand, Simulate, Backprop).
  - [x] `BranchAndBoundLaser`: Incumbent ceiling bar, lower bound badges, guillotine laser slice, $15\%$ frosted ghost pruning.
- [x] **1.4 Comparative & Metric Primitives (`manim_engine/primitives/metrics/`)**
  - [x] `DynamicLeaderboard`: Animated comparative score ladders with delta badges.
  - [x] `DualMetricGauge`: Radial visit/value meters and quantitative payoff tickers.

### Phase 2: Declarative Visual Scene Graph (VSG) & SVO Scripting
- [x] **2.1 Formalize VSG Pydantic Schema (`pipeline/vsg_schema.py`)**
  - [x] Define `VisualEntity`, `SVOContext`, `VisualAction`, `VisualMicroBeat`, `MacroBeat`, and `VisualStoryboard`.
- [x] **2.2 Upgrade Script Generator (`pipeline/script_generator.py`)**
  - [x] Shift Gemini prompt from passive string metadata to SVO semantic triples (`subject`, `action_verb`, `target_entity`, `anchor_word`).
  - [x] Bind mathematical LaTeX formulas directly to visual transformation targets.
- [x] **2.3 Retire Monolithic Scene Templates (`manim_engine/scenes/dynamic_scene.py`)**
  - [x] Create `DynamicCompositeScene` capable of interpreting any valid VSG specification.
  - [x] Replace `CATEGORY_SCENE_MAP` in `run_pipeline.py` and `auto_produce.py` with the dynamic compiler.

### Phase 3: Acoustic Forced Alignment & Exact Kinetic Pacing
- [x] **3.1 Integrate Phoneme / Word-Level Aligner (`pipeline/aligner.py`)**
  - [x] Extract word timestamps from Kokoro audio synthesis or via lightweight WhisperX/CTC alignment.
  - [x] Generate structured word-level alignment map: `{word: str, t_start: float, t_end: float}`.
- [x] **3.2 Implement Frame-Ahead Event Scheduler (`manim_engine/scheduler.py`)**
  - [x] Schedule visual transformations at $t_{\text{trigger}} = \max(0, t_{\text{word\_start}} - 0.04\text{s})$.
  - [x] Synchronize procedural SFX cues (whoosh, click, sever slice, sub impact) to visual transients within $\pm 30\text{ms}$.

### Phase 4: Native ArXiv Vector Figure Extraction
- [x] **4.1 ArXiv Source Tarball Ingestion (`pipeline/arxiv_vector_extractor.py`)**
  - [x] Download e-print bundles via `https://arxiv.org/e-print/{arxiv_id}` with authenticated User-Agent.
  - [x] Parse LaTeX source to locate figures (`\includegraphics`) and inline TikZ environments.
- [x] **4.2 Vector Conversion & Standalone SVG Compilation**
  - [x] PyMuPDF vector extraction (`page.get_svg_image(text_as_path=True)`).
  - [x] Compile PDF/EPS figures to standalone SVGs.
- [x] **4.3 Manim CE Animation Harness**
  - [x] Auto-recolor black paper vector paths for `#0A0D14` blackboard styling.
  - [x] Animate authentic paper figures inside `DynamicCompositeScene` via `get_arxiv_vector_figure()`.

### Phase 5: Closed-Loop VLM Critic & Quality Gate
- [x] **5.1 Headless Fast-Render Inspection Harness**
  - [x] Implement fast draft rendering (`manim -ql -s`) for keyframe validation in under 2 seconds.
- [x] **5.2 Gemini Vision Semantic Critic (`pipeline/vlm_critic.py`)**
  - [x] Evaluate keyframes against beat script for:
    - Semantic alignment (does graphic represent the spoken concept?).
    - No-bullet-points compliance (is content geometric/mechanical?).
    - Safe-zone boundary compliance.
  - [x] Embedded automated quality audit gate into production pipeline (`auto_produce.py`).

### Phase 6: Closed-Loop VLM Self-Healing & Auto-Repair Loop (Option A)
- [x] **6.1 Spatial Collision & Safe-Zone Detection**
  - [x] Extract entity bounding boxes from keyframes and check AABB collisions ($p_x > 0 \land p_y > 0$).
  - [x] Enforce 9:16 safe corridor ($X \in [-3.2, 3.2], Y \in [-4.0, 5.5]$).
- [x] **6.2 Deterministic Spatial Repulsion & Layout Patch Solver (`pipeline/layout_solver.py`)**
  - [x] Compute Minimum Translation Vector (MTV) separation displacements.
  - [x] Auto-scale entities exceeding safe boundaries ($s \in [0.65, 1.0]$).
  - [x] Generate declarative `VisualPatchProposal` objects without raw LLM code drift.
- [x] **6.3 Structured VLM Critic Patch Output (`pipeline/vlm_critic.py`)**
  - [x] Extend `VLMCritic` to propose structured layout delta patches if score $< 8.5/10$.
  - [x] Patchable parameters: `shift_y`, `scale_factor`, `font_size_scale`, `element_offsets`.
- [x] **6.4 Fast Headless Beat Re-render & Rollback Governor (`pipeline/auto_produce.py`)**
  - [x] Hot-patch storyboard layout parameters without full scene re-generation.
  - [x] Fast-render keyframe (<150ms) and re-audit via subprocess `manim -ql` + `ffmpeg -ss` timestamp frame extraction.
  - [x] Monotonic acceptance: if score drops, rollback to previous best candidate. Cap at max 2 iterations.

---

## 5. Milestone Tracking & Verification Metrics

| Milestone | Target Completion | Verification Criteria | Status |
| :--- | :--- | :--- | :--- |
| **M1: 10-Agent Research Synthesis** | 2026-09-26 | Complete taxonomy, SVO schemas, and 3b1b heuristics documented. | **DONE** |
| **M2: Core Primitives Library** | Phase 1 | `manim_engine/primitives/` compiles cleanly; test scenes render without cards. | **DONE** |
| **M3: Dynamic Scene Compiler** | Phase 2 | `auto_produce.py` renders any paper without using the 4 rigid templates. | **DONE** |
| **M4: Word-Level Audio Sync** | Phase 3 | Visual actions trigger within 40ms of spoken words in inspection keyframes. | **DONE** |
| **M5: End-to-End V2 Validation** | Phase 4 & 5 | Re-render TAMP & SAE papers; pass Gemini Vision quality audit; publish to YT. | **DONE** |
| **M6: Closed-Loop Auto-Repair** | Phase 6 | Sub-8.5 visual flaws automatically patched with verified convergence & zero drift. | **DONE** |


