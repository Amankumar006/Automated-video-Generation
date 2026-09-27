# Changelog — The Model Verse Shorts

All notable changes, architectural pivots, bug fixes, and feature additions to this repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-alpha] - 2026-09-26

### 🔬 Multi-Agent Research & Visual Engine 2.0 Kickoff
- **10-Agent Deep-Dive Investigation**: Deployed 10 specialized research subagents covering 3Blue1Brown visual pedagogy, SOTA paper-to-video systems (*TheoremExplainAgent*, *ManimAgent*, *Paper2Video*, *Preacher*), cognitive retention mechanics, SVO semantic compilers, robotics/TAMP visual metaphors, and mechanistic interpretability geometry.
- **Architectural Autopsy**: Uncovered critical root causes of visual-script disconnect:
  - `CATEGORY_SCENE_MAP` rigidly forced all papers into 4 pre-baked scene templates.
  - `deepdive_scene.py` hardcoded quadratic attention and GPU VRAM slots ($K_1 \dots K_5$) even for robotics/planning papers.
  - `showdown_scene.py` failed to display any of the 5 generated LaTeX formula SVGs, defaulting to generic text cards.
  - Linear temporal scaling (`scale_times`) caused audio-visual desynchronization.
- **Master Plan & Agent Governance**:
  - Published [`PLAN.md`](PLAN.md) detailing the 5-phase overhaul to Visual Engine 2.0.
  - Published [`AGENTS.md`](AGENTS.md) establishing strict coding standards, constraints, and primitive usage guides for all autonomous agents working on the codebase.
- **Phase 1: Modular 3b1b Primitive Registry (100% Implemented & Verified)**:
  - **Robotics & TAMP** (`manim_engine/primitives/robotics/`):
    - `CoupledCanvas`: Dual-manifold canvas coordinating discrete task logic ($Y \in [0.8, 5.0]$) and continuous C-space ($Y \in [-4.6, 0.4]$).
    - `CoupledNode`: Discrete action/predicate node with state styling.
    - `ConstraintProjectionSheaf`: Dynamic volumetric beam connecting discrete actions to continuous targets.
    - `GeometricRefinementPulse`: Collision explosion, witness generation, backward shockwave, and discrete pruning.
    - `ParametricKinematicArm`: Forward kinematics analytical arm with capsule hulls and $SE(2)$ end-effector frames.
    - `ASTMorphTree`: Syntax-specific AST node morphology (Hexagons for loops, Pills for functions, Diamonds for conditions, Holes for sketches) with auto-scaling text.
    - `SandboxIsolationPod`: Clean-room containment chamber with test suite assertion telemetry ledger.
  - **Deep Learning & Mechanistic Interpretability** (`manim_engine/primitives/neural/`):
    - `SAEConstellation`: Residual stream coordinate plane, entangled activation vector, overcomplete starburst dictionary, and top-$k$ sparsity sieve.
    - `FeatureProjectionChip`: HUD chips for isolated monosemantic features and intensity meters.
    - `TransformerAttentionGrid`: Parametric $N \times N$ attention heatmap grid with token sequence labels and colormap interpolation.
    - `RoutingRibbon`: Curved Bézier routing arcs with variable stroke widths and moving Value packets.
    - `SparseMoELattice`: Expert constellation, cyan Router Gate, top-$k$ laser dispatch, and gold Shared Expert foundation.
    - `LoadBalancingManometer`: Capacity buffer reservoir bars with crimson overflow limit line.
    - `ContrastiveHypersphere`: Unit circle $\mathbb{S}^1$ with positive alignment spring and negative Coulomb repulsion arrows.
    - `ScoreBasedDiffusionField`: Learned score vector field driving noisy particles to clean data modes.
  - **Algorithmic Search** (`manim_engine/primitives/search/`):
    - `DynamicSearchTree`: Parametric search tree with frontier expansion and MCTS 4-beat cycle (Select, Expand, Simulate ghost line, Backprop wave).
    - `MCTSNodeGauge`: Dual-ring node gauge (inner core color = expected value $Q$; outer radial arc = visit count $N$).
    - `BranchAndBoundLaser`: Global incumbent ceiling bar, local lower bound badge, guillotine laser slice, and $15\%$ frosted ghost pruning.
  - **Quantitative Metrics** (`manim_engine/primitives/metrics/`):
    - `RadialScoreMeter`: Circular gauge with radial progress arc and central metric counter.
    - `DualMetricGauge`: Side-by-side comparative meter comparing Contender A vs Contender B with central green delta badge.
  - **Headless Test Verification**:
    - Verified all primitives via `manim -ql -s` in `test/test_robotics_primitives.py`, `test/test_neural_primitives.py`, and `test/test_search_metrics_primitives.py`.
- **Phase 2: Declarative Visual Scene Graph (VSG) & SVO Scripting (100% Implemented & Verified)**:
  - **VSG Pydantic Schema (`pipeline/vsg_schema.py`)**:
    - Formalized data-driven scene graph schema featuring `VisualEntity`, `SVOContext` (`subject`, `action_verb`, `direct_object`, `anchor_word`), `ActionPayload`, `VisualAction`, `VisualMicroBeat`, `MacroBeat`, and `VisualStoryboard`.
    - Added `convert_legacy_spec_to_vsg()` which maps any legacy JSON spec to modern VSG and infers domain taxonomy.
  - **Upgraded Script Generator (`pipeline/script_generator.py`)**:
    - Added prompt directives for domain taxonomy classification (`robotics_tamp`, `neural_sae`, `neural_moe`, `neural_attention`, `algorithmic_search`, `quantitative_benchmark`).
    - Enforced per-beat `svo_action` semantic triples and explicit LaTeX binding to eliminate card/bullet text generation.
  - **Universal Scene Compiler (`manim_engine/scenes/dynamic_scene.py`)**:
    - Implemented `DynamicCompositeScene` capable of interpreting any valid VSG specification or legacy spec.
    - Supported 6 dynamic domain choreographies with smooth transitions, 3b1b styling, mobile 9:16 safe-zone framing, and particle pulses.
    - Verified headless keyframe renders across multiple domains: Robotics/TAMP, Neural SAE, Attention Mechanism, and Benchmark Showdowns.
  - **Dynamic Pipeline Integration**:
    - Updated `pipeline/run_pipeline.py` and `pipeline/auto_produce.py` to route all scenes through `DynamicCompositeScene` by default, eliminating rigid category scene mapping.
- **Phase 3: Acoustic Forced Alignment & Exact Kinetic Pacing (100% Implemented & Verified)**:
  - **Acoustic Forced Alignment Engine (`pipeline/aligner.py`)**:
    - Developed `AcousticForcedAligner` utilizing 200 Hz (5ms hop) Savitzky-Golay smoothed RMS energy envelopes combined with Espeak phonetic token weighting.
    - Implemented energy valley snapping to lock word boundaries onto actual acoustic dips between words with $\pm 75\text{ms}$ tolerance.
    - Formalized the **Frame-Ahead Rule**: $t_{\text{trigger}} = \max(0, t_{\text{word\_start}} - 0.04\text{s})$, pre-triggering visual transitions 1 frame ahead so motion lands precisely on phonetic onset.
  - **Kinetic Event Scheduler (`manim_engine/scheduler.py`)**:
    - Developed `KineticScheduler` computing optimal `pre_wait`, `action_run_time`, and `post_wait` budgets for every beat and anchor word.
    - Integrated procedural SFX cue generator (`generate_kinetic_sfx_cues`) mapping whooshes, clicks, laser strikes, and sub-impacts directly to acoustic action triggers.
  - **Audio Pipeline Integration**:
    - Updated `pipeline/audio_synthesizer.py` to automatically align every spoken beat during neural speech synthesis and record word-level timestamps in the spec JSON.
    - Integrated `KineticScheduler` into `DynamicCompositeScene` via `kinetic_pacing()`.
- **Phase 4: Native ArXiv Vector Figure Extraction (100% Implemented & Verified)**:
  - **ArXiv Tarball Ingestion & Vector Extraction (`pipeline/arxiv_vector_extractor.py`)**:
    - Built automated e-print tarball downloader fetching native LaTeX sources and figure directories from `arxiv.org/e-print/{arxiv_id}`.
    - Integrated PyMuPDF (MuPDF v1.28) for vector extraction, compiling raw PDF/EPS figures into standalone SVGs.
  - **Blackboard Recolor Engine (`recolor_svg_for_blackboard`)**:
    - Automated stripping of white paper backgrounds and intelligent re-mapping of black ink strokes to signature `#E2E8F0` chalk strokes with cyan (`#38BDF8`) and emerald (`#10B981`) accents.
  - **Dynamic Scene Integration**:
    - Connected `get_paper_vector_figure()` into `DynamicCompositeScene` via `get_arxiv_vector_figure()`, allowing authentic paper diagrams to be rendered as animated `SVGMobject` manifolds.
    - Successfully verified against arXiv paper `2609.30233` (extracting 3 native vector figures with ~300 sub-paths each).
- **Phase 5: Closed-Loop VLM Critic & Quality Gate (100% Implemented & Verified)**:
  - **Gemini Vision Pedagogical Auditor (`pipeline/vlm_critic.py`)**:
    - Built multimodal vision critic assessing rendered keyframes against narrative beat scripts, scoring semantic alignment, 3Blue1Brown chalkboard compliance, 9:16 mobile safe zones, and pedagogical clarity.
    - Successfully identified and pruned lingering SaaS card UI elements in `CoupledCanvas`, `CoupledNode`, `SandboxIsolationPod`, and replaced circular gauges in Beat 5 with `ComparativeCoordinateManifold` (calibrated axes, growing bars, analytical delta arrows).
    - Integrated native `ASTMorphTree` directly with `ConstraintProjectionSheaf` for robotics code policy synthesis in Beat 3.
  - **Pipeline Quality Gate (`auto_produce.py`)**:
    - Integrated automated Step 6.5 VLM Critic quality gate into the autonomous production pipeline to audit every produced short before broadcast distribution.
    - Successfully validated the end-to-end production of arXiv 2609.30233 (*Coding Agents for Generalized Task and Motion Planning*), producing high-contrast 3Blue1Brown chalkboard visuals across all 6 beats.
    - **YouTube Shorts Published**: Uploaded broadcast short to YouTube Shorts: [https://youtube.com/shorts/uZvyMMzU0Yk](https://youtube.com/shorts/uZvyMMzU0Yk) (Video ID: `uZvyMMzU0Yk`, Privacy: Unlisted, auto-posted engagement comment).
- **Phase 6: Closed-Loop VLM Self-Healing & Auto-Repair Loop (In Progress)**:
  - **3-Agent Research Synthesis**:
    - Investigated multimodal actor-critic self-refinement and anti-oscillation bounds (Reflexion, ManimAgent).
    - Proved sub-second headless Manim keyframe rendering (~26ms - 117ms in-memory extraction).
    - Derived deterministic spatial repulsion solver using Minimum Translation Vectors (MTV) and 9:16 vertical safe corridor projections.
  - **Deterministic Layout Solver (`pipeline/layout_solver.py`)**:
    - Implemented Position-Based Dynamics (PBD) solver to detect collisions ($p_x > 0 \land p_y > 0$) and safe-zone clipping ($X \notin [-3.2, 3.2], Y \notin [-4.0, 5.5]$), outputting exact mathematical displacement vectors $(\Delta x, \Delta y)$ and scaling factors $s$.
  - **Structured Visual Patching in VLM Critic (`pipeline/vlm_critic.py`)**:
    - Upgraded Gemini Vision Critic prompt and output schema to return typed `VisualPatchProposal` objects when beat scores $< 8.5/10$.
  - **Self-Healing Loop in Auto-Producer (`pipeline/auto_produce.py`)**:
    - Connected iterative self-repair loop (max 2 iterations) hot-patching layout offsets and verifying convergence before final video multiplexing.

---

## [2.0.3-alpha] - 2026-09-27

### 🎙️ Script Pedagogy & Comprehensibility Critic (`pipeline/script_critic.py`)
- **Feynman & 3Blue1Brown Educational Quality Gate**:
  - Developed an automated linguistic and pedagogical script auditor (`ScriptCritic`) to guarantee voiceover accessibility for everyday YouTube Shorts viewers.
  - **Flesch-Kincaid & Reading Ease Analyzer**: Pure-Python phonetic syllable counter and readability engine enforcing middle-school grade level ($\le \text{Grade } 8.0$) and conversational ease ($\ge 60.0$).
  - **Jargon Detection & Academic Penalty**: Automatically scans scripts for 30+ ungrounded CS/math terms (`softmax`, `eigenvalues`, `swiglu`, `flops`, `tflops`, `matrix explosion`, `residual stream`, `kv-cache`, `sram`, `hyperplanes`) and rejects scripts containing ungrounded jargon.
  - **Everyday Analogy Detector**: Scans for and rewards concrete sensory/real-world metaphors (`tv static`, `foggy mirror`, `clouds`, `rabbit`, `sculptor`, `marble`, `chisel`, `library`, `autocomplete`, `recipe`, `kitchen`).
  - **YouTube Creative Director LLM Persona**: Integrated Gemini multimodal persona acting as a curious 14-year-old and seasoned Shorts creator to provide actionable qualitative rewrites and line critiques.
- **Pipeline Integration**:
  - Embedded Step 2.5 Script Quality Gate into `pipeline/auto_produce.py`, vetting scripts before expensive audio synthesis or video rendering.
  - Updated `SCRIPT_DIRECTIVES` in `pipeline/script_generator.py` to mandate everyday physical analogies and zero spoken tensor math.
- **Validation Suite**:
  - Authored unit test suite in `test/test_script_critic.py` (100% passing).
  - Empirical verification:
    - *How an AI Thinks in One Second* (Old): **4.2 / 10.0** (Grade 12.2, 6 critical jargon terms, 0 analogies) $\to$ **REJECTED**.
    - *How AI Creates Images From TV Static* (New): **9.6 / 10.0** (Grade 5.7, 0 jargon terms, 9 rich analogies) $\to$ **APPROVED**.

---

## [2.0.2-alpha] - 2026-09-27

### 🎬 Dynamic Visual Pedagogy Overhaul: "How an AI Thinks in One Second"
- **Dual-Coding Choreography Overhaul (`manim_engine/scenes/dynamic_scene.py`)**:
  - Completely overhauled `play_ai_thinking_in_one_second_choreography()` (lines 616–938) replacing generic placeholder cards with authentic 3Blue1Brown chalkboard geometry directly bound to the script's exact mechanical actions.
  - **Beat 1 (10ms - Embedding Disintegration)**: Prompt string (`"Why is the sky blue ?"`) dissolves into token IDs (`[15234], [374], ...`) and projects into a 3D coordinate frame representing $\mathbb{R}^{12288}$ manifold with coordinate vectors ($\vec{v}_{\text{why}}, \vec{v}_{\text{sky}}, \vec{v}_{\text{blue}}$) and formal embedding formula $\mathbf{x}_0 = \mathbf{W}_e \mathbf{t} + \mathbf{W}_{\text{pos}}$.
  - **Beat 2 (50ms - Attention Ignition & Quadratic Explosion)**: Query vector $\vec{q}_{\text{sky}}$ and Key vector $\vec{k}_{\text{blue}}$ projected with angular arc $\theta$, dot product scalar ($q \cdot k = 0.89$), an explicit $N \times N$ crimson all-to-all attention graph ($\mathcal{O}(N^2)$), and formula $\mathbf{A} = \text{softmax}(\mathbf{Q}\mathbf{K}^T / \sqrt{d_k})$.
  - **Beat 3 (200ms - FlashAttention & SRAM Tiling)**: Two-tier memory architecture contrasting On-Chip SRAM (19.2 TB/s bandwidth) with Off-Chip HBM3 (3.35 TB/s memory bottleneck), flanked by curved streaming conduits showing fused tiling without HBM round-trips.
  - **Beat 4 (FFN Depth - 80 Layers & SwiGLU Gating)**: 80-layer vertical residual stream ladder with SwiGLU gating bifurcation ($\mathbf{W}_{\text{up}} \cdot \mathbf{x}$ and $\sigma(\mathbf{W}_{\text{gate}} \cdot \mathbf{x})$ converging into $\otimes$ multiplier and feeding back into the residual stream).
  - **Beat 5 (900ms - Logit Collapse & Token Sampling)**: Softmax probability distribution bars over 128k vocabulary tokens, orange laser cursor pointing to `"Rayleigh"` (68%), next-token emission badge, and Softmax formula $P(w_{t+1}) = \text{softmax}(\mathbf{W}_u \mathbf{x}_L / T)$.
  - **Beat 6 (Outro - Channel Signature)**: Minimalist rotating concentric ring chalkboard outro card for The Model Verse.
- **YouTube Shorts Broadcast**:
  - Published to YouTube Shorts: [https://youtube.com/shorts/MC4zhxvwmPg](https://youtube.com/shorts/MC4zhxvwmPg) (Video ID: `MC4zhxvwmPg`, Privacy: `unlisted`).
  - Auto-posted pinned engagement comment: *"⚡ From token disintegration to 80-layer SwiGLU gating in under 1000ms: What part of the transformer inference pipeline surprised you most? Drop your thoughts below! 👇"*.
  - Configured 6 exact chapter markers, 20 targeted SEO tags, and full description metadata.

### 🐛 Critical Bug Fixes
- **Manim `CurvedArrow` Compatibility**: Fixed `TypeError: VMobject.scale() got an unexpected keyword argument 'scale_tips'` by replacing `GrowArrow` with `Create()` for all curved arrows.
- **Beat Timing Drift Elimination**: Eliminated +2.6s accumulated animation latency across beats by strictly subtracting animation runtimes from beat wait budgets (`self.wait(max(0.1, b_dur - anim_time))`), ensuring Beat 6 transitions on the exact word boundary.
- **Right-Edge Layout Overflow**: Repositioned Beat 4 multiplier node and labels within safe mobile margins ($X \in [-3.2, 3.2]$).
- **Bash LaTeX Expansion**: Sanitized formula generation script to prevent double-quote variable expansion (`$P` -> empty string) when generating Math SVGs.

---

## [2.0.1-alpha] - 2026-09-27

### Fixed — Phase 6 Self-Healing Loop Root Cause

- **`pipeline/fast_beat_renderer.py` — Complete Rewrite**:
  - **Bug**: `render_beat_keyframe()` instantiated `DynamicCompositeScene` in-process with `skip_animations=True`, which fast-forwarded the entire construct including `FadeOut(brand_card)` at the outro, yielding a near-black frame (mean brightness ~14). The VLM critic consistently scored these blank frames 1.0/10, causing every patch to be rolled back — the self-healing loop was effectively inert.
  - **Root Cause**: Manim scenes are not restartable mid-construct from within the same process. `skip_animations=True` executes all animation timelines, ending at the last cleared frame rather than any intermediate beat.
  - **Fix**: Replaced in-process Scene instantiation with a subprocess `manim -ql` call (same as `render_scene`) + `ffmpeg -ss <beat_midpoint>` frame seek. Added a content-hash-keyed disk cache (`pipeline/.draft_render_cache/`) to share the draft MP4 across all beats within a single repair iteration, avoiding redundant renders.
  - **Result**: Repaired frames now correctly show the beat's live scene content, enabling valid VLM monotonic acceptance comparison.

- **`pipeline/auto_produce.py` — Self-Healing Loop Corrections**:
  - **Patch Deduplication**: Multiple patches for the same `entity_id` within one beat now accumulate additively (`dx_new = dx_prev + dx_patch`, `scale = scale_prev * scale_patch`) instead of overwriting — eliminating the oscillation caused by the VLM returning conflicting `hero_visual` nudges.
  - **Cache Invalidation**: Draft render cache is cleared at the start of each repair iteration, ensuring the new `layout_overrides` spec version is always freshly rendered.
  - **Improved Diagnostics**: Added `traceback.print_exc()` on audit bypass, post-repair score logging, and skip-logic for beats already scoring ≥ 8.5.

---



## [1.2.0] - 2026-09-26

### Added
- **Multi-Model Fallback Cascade in `pipeline/script_generator.py`**:
  - Implemented automatic fallback across model families: `[MODEL_NAME, "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite-preview", "gemma-4-31b-it"]`.
  - Overcomes the 20 requests/day per-model Free Tier quota limit without downtime.
- **Explicit Template Argument in `pipeline/auto_produce.py`**:
  - Added `--template <path>` CLI flag to render specific JSON specs directly without re-synthesizing scripts.
- **YouTube Shorts Publishing Pipeline**:
  - Published SAE Latents Short: `final_sae_parts_of_speech_latents_architecture_breakdown.mp4` ([YouTube Shorts URL: https://youtube.com/shorts/lkfqGEE8YH8](https://youtube.com/shorts/lkfqGEE8YH8)).
  - Generated automated chapter markers, optimized tags, and community pinned comments.

### Fixed
- **Split-Screen Card Collision in `manim_engine/primitives/split_screen.py`**:
  - Added dynamic `.scale_to_fit_width(3.4)` bounding logic to contender titles, badges, and spec items to prevent text from overflowing cards or touching the central `VS` badge.
- **Publisher Bug in `pipeline/publisher.py`**:
  - Resolved `NameError: name 'video_file' is not defined` by passing correct `video_path`.

---

## [1.1.0] - 2026-09-25

### Added
- **Sparse Autoencoder (SAE) Latent Space Visualization**:
  - Implemented 2D Cartesian number plane feature projection with parts-of-speech cluster envelopes (`[NOUNS]`, `[VERBS]`, `[FUNCTION WORDS]`) in `breakdown_scene.py`.
- **Kokoro Neural Audio Synthesizer**:
  - Integrated Kokoro-82M neural voices (`am_adam`, `am_michael`) with selectable speech pacing (1.10x–1.12x).
  - Procedural Lo-Fi ambient synthesizer with dynamic audio ducking (10% speech, 32% pauses).
- **High-CTR YouTube Shorts Poster Generator**:
  - Automatically extracts the best frame, crops to vertical 9:16, composites brand badges, and formats LaTeX equations for click-through rate optimization.

---

## [1.0.0] - 2026-09-24

### Initial Release
- **Full Autonomous End-to-End Pipeline**:
  - `pipeline/auto_produce.py`: Single command transforms topic/arXiv into broadcast-ready MP4.
  - arXiv ingestion (`arxiv_fetcher.py`).
  - 6-beat narrative script generation via Gemini 2.5 Flash (`script_generator.py`).
  - 3Blue1Brown chalkboard Manim rendering (`#0A0D14` carbon theme, dot matrix grid).
  - Kinetic subtitle burn-in via FFmpeg.
  - Web Studio dashboard (`studio/run_studio.py`) with live background log streaming.
