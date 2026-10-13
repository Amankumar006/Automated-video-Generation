# Phased Implementation Roadmap & Technical Risk Register
**Next-Generation Broadcast Video Generation Architecture for The Model Verse Shorts**

**Author**: `worker_m5` (Systems Architect & Implementation Strategist)  
**Date**: October 13, 2026  
**Document Version**: 1.0.0 (Final Architectural Specification)  
**Target Environment**: `themodelverse-shorts` Production Video Generation Engine  
**Companion Documents**: 
- `design_system_specification.md` (Design Tokens, Typography, Materials, Safe Zones)
- `cognitive_load_framework.md` (Anti-Confusion Standard, Semantic Alignment, Anti-Pattern Catalog)
- `engine_evaluation_benchmark.md` (Engine Comparative Benchmark Matrix & Profiles)
- `next_gen_architecture_spec.md` (Decoupled VSG-IR Blueprint & Two-Tier Gatekeeper Spec)

---

## Executive Summary & Transformation Goals

### 1. The Architectural Inflection Point
The Model Verse Shorts was conceived to translate dense frontier AI research papers into high-cadence short-form vertical videos (YouTube Shorts, TikTok, Instagram Reels). While programmatic vector graphics powered by Manim Community Edition (Python) initially provided mathematically clean curves, the production engine has reached a severe structural ceiling:

1. **Monolithic Procedural Coupling**: Narrative script state, audio timing alignment, Cairo polygon rasterization, Pango typographic layout, and FFmpeg muxing are tightly coupled in imperative Python scripts (`manim_engine/scenes/script_driven_scene.py`). Modifying visual styling or testing a layout requires re-rendering entire scenes.
2. **Prohibitive Render Latency**: Reconstructing Manim's procedural scene tree takes 15–25 seconds for a single frame snapshot and 8–15 minutes for a full 60-second 1080×1920 60fps short. This prevents real-time automated quality assurance and blocks CI/CD feedback loops.
3. **Typographic & Stylistic Deficits**: Manim lacks native CSS primitives (`backdrop-filter: blur()`, box-shadow, Flexbox/Grid flow, OpenType ligatures, subpixel font smoothing). Workarounds rely on fragile vector polygon slicing and Pango Cairo glyph hacks that suffer from integer advance width rounding artifacts ("T H E   M O D E L").
4. **Empirical Defect Escapes**: Layout placement relies on static coordinate offsets without collision avoidance, causing frequent collisions between central visual blueprints, math formulas ($y = -2.6$), and captions ($y = -3.85$). Obsolete safe-zone margins (`SAFE_Y_MIN = -5.8`) cause critical titles and formulas to be occluded by mobile platform UI chrome (Shorts title, channel handle, sound pill, and right-rail engagement icons).
5. **Decoupled Informational QA**: In `pipeline/run_pipeline.py`, the multimodal VLM critic executes *after* the final video has already been muxed. When API quota limits are hit, the critic falls back to a synthetic pass (`overall_score = 8.8`), allowing defective frames to reach broadcast output.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                TRANSFORMATION TRAJECTORY                                │
├────────────────────────────────────────────┬────────────────────────────────────────────┤
│ LEGACY MONOLITHIC MANIM ENGINE             │ NEXT-GEN DECOUPLED BROADCAST PIPELINE      │
├────────────────────────────────────────────┼────────────────────────────────────────────┤
│ • Full render: 480 – 900 s (8–15 min)      │ • Full render: 35 – 65 s (< 4 s on Lambda) │
│ • Single-frame seek: 15 – 25 s             │ • Single-frame seek: 0.08 – 0.20 s (CDP)   │
│ • Imperative Python / PyCairo polygons     │ • Declarative React 19 / TypeScript / CSS3 │
│ • Rigid coordinate offsets; text collisions│ • PBD collision solver + Flexbox/Grid flow │
│ • Obsolete safe zones (bottom UI clipping) │ • Universal 9:16 safe-zone enforcement     │
│ • Post-hoc informational QA (8.8 fake pass)│ • Synchronous two-tier blocking gatekeeper │
│ • Docker image: 2.8 – 3.8 GB (TeX Live)    │ • Docker image: 550 – 850 MB (Chromium)    │
└────────────────────────────────────────────┴────────────────────────────────────────────┘
```

### 2. Core Transformation Goals
1. **Latency Reduction**: Achieve $<45\text{s}$ full render times on 16-core local hardware and $<200\text{ms}$ single-frame seeking via Chrome DevTools Protocol (CDP), unlocking sub-second visual test loops.
2. **Defect Elimination**: Establish zero-tolerance deterministic gates: **0% safe-zone violations**, **0% text collisions**, and **$\ge 7.0:1$ WCAG AAA contrast compliance**.
3. **Broadcast-Grade Aesthetics**: Modernize visual styling to match top-tier tech media (Fireship, Apple Keynotes, Alex Bowers) using native CSS glassmorphism (`backdrop-filter: blur(24px)`), directional lighting, 4-tier surface elevation, and critically damped spring motion.
4. **Cognitive Load Optimization**: Enforce the **Rule of One** (exactly 1 focal target per beat, $\le 14$ words per card) and eliminate the "7-Element Trap" through progressive geometric reveals synchronized to speech anchor words.
5. **Decoupled Architecture**: Standardize on the **Video Scene Graph Intermediate Representation (VSG-IR)**—a backend-agnostic AST isolating script state from graphics renderers.

---

## Phased Architectural Roadmap

The transition follows a disciplined 4-phase, 8-week migration plan engineered for zero production downtime.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               8-WEEK PHASED IMPLEMENTATION TIMELINE                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ W1 │ W2 │ W3 │ W4 │ W5 │ W6 │ W7 │ W8 │ Milestone & Scope                                       │
├────┼────┼────┼────┼────┼────┼────┼────┼─────────────────────────────────────────────────────────┤
│█████████│    │    │    │    │    │    │ PHASE 1: Decoupled Foundation & Tier 1 Deterministic CV │
│         │█████████│    │    │    │    │ PHASE 2: Remotion Broadcast Adapter & Design Tokens     │
│         │    │    │█████████│    │    │ PHASE 3: Multimodal VLM Critic Council & Repair Loop    │
│         │    │    │    │    │█████████│ PHASE 4: Production Cutover & Hybrid Engine Orchestration│
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Decoupled Foundation & Tier 1 Deterministic CV Gatekeeper
*Timeline: Weeks 1–2 | Focus: Data Contracts, Deterministic QA Firewall, Pre-Render Validation*

#### 1.1 Objectives & Deliverables
- Establish the authoritative **Video Scene Graph Intermediate Representation (VSG-IR)** schema as the single source of truth between narrative generation and rendering.
- Build the **Tier 1 Deterministic Computer Vision (CV) Gatekeeper** operating locally in C++/OpenCV/NumPy ($<50\text{ms}$ per frame) with zero cloud API dependencies.
- Deploy pre-render static AST linting to intercept layout collisions before initiating rasterization.
- Maintain a parallel dual-engine harness where the legacy Manim engine consumes VSG-IR via a backward-compatible adapter.

#### 1.2 Core Components & Technical Specifications

##### 1.2.1 VSG-IR Contract Definition (`pipeline/vsg/schema.py` & `src/types/vsg-ir.d.ts`)
The VSG-IR is a strictly validated, JSON-serializable AST implemented via Pydantic v2 (Python) and Zod/TypeScript. It encapsulates:
- **Canvas Metadata**: Resolution ($1080 \times 1920$), frame rate ($60\text{fps}$), duration, audio stems (voiceover, ambient bed, ducking dB).
- **Theme Tokens**: Surface elevation colors (L0–L4), brand accents, typography scales, glassmorphism blur radii, and drop shadow matrices.
- **Narrative Beats**: Time ranges, spoken text, pedagogical intent, visual metaphor classification, and acoustic anchor words with millisecond-exact timestamps from forced phoneme alignment (WhisperX / Kokoro).
- **Scene Graph Nodes**: Hierarchical UI nodes (`MetricCard`, `ExpertRouterMatrix`, `CodeBlock`, `KineticCaptions`, `Badge`) with normalized spatial coordinates, auto-flow bounding constraints, and spring motion kinematics.

```
                       ┌─────────────────────────┐
                       │  pipeline/run_pipeline  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │  script_generator (LLM) │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ acoustic_aligner (Audio)│
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ visual_director (Plan)  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ╔═════════════════════════╗
                       ║   VSG-IR Contract AST   ║
                       ╚═════════════════════════╝
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
         ┌───────────────────────┐     ┌───────────────────────┐
         │ Pre-Render AST Linter │     │ Manim Legacy Adapter  │
         │ (AABB/Safe-Zone Check)│     │ (Backward Compatible) │
         └───────────┬───────────┘     └───────────┬───────────┘
                     │                             │
                     ▼                             ▼
         [ PASS: Proceed to Render ]   [ Legacy Manim Video MP4]
                     │
                     ▼
         ╔═════════════════════════════════════════╗
         ║ Tier 1 Deterministic CV Gatekeeper      ║
         ║ (Farneback, WCAG AAA, Safe-Zone Mask)   ║
         ╚═════════════════════════════════════════╝
```

##### 1.2.2 Tier 1 Deterministic CV Gatekeeper Engine (`pipeline/qa/tier1_cv_gatekeeper.py`)
Executes four local image processing heuristics on extracted frame buffers:

1. **Optical Flow Motion Jitter & Strobing Detector**:
   - Computes dense optical flow fields $\mathbf{u}(x, y) = (u, v)$ across consecutive frames using Gunnar Farneback's quadratic polynomial expansion:
     $$\text{cv2.calcOpticalFlowFarneback}(I_t, I_{t+1}, \text{pyr\_scale}=0.5, \text{levels}=3, \text{winsize}=15, \text{iterations}=3, \text{poly\_n}=5, \text{poly\_sigma}=1.2)$$
   - Tracks text edge stability via sparse Lucas-Kanade feature tracking (`cv2.calcOpticalFlowPyrLK`) on Shi-Tomasi corners (`cv2.goodFeaturesToTrack`).
   - Computes acceleration and jerk vectors:
     $$\mathbf{a}_t = \frac{\mathbf{u}_{t+1} - \mathbf{u}_t}{\Delta t}, \quad \mathbf{j}_t = \frac{\mathbf{a}_{t+1} - \mathbf{a}_t}{\Delta t}$$
   - **Thresholds**: Flags global strobing if frame-to-frame SSIM drops $> 0.22$ across $< 3$ frames without an intentional scene cut; flags motion jitter if flow acceleration variance $\sigma^2_a > 15.0\,\text{px}/\text{frame}^2$.

2. **WCAG AAA Relative Luminance & Pixel Contrast Ratio Analyzer**:
   - Decompresses non-linear 8-bit sRGB channels to linear photometric luminance:
     $$C_{\text{linear}} = \begin{cases} \frac{C_{\text{srgb}}}{12.92} & \text{if } C_{\text{srgb}} \le 0.04045 \\ \left(\frac{C_{\text{srgb}} + 0.055}{1.055}\right)^{2.4} & \text{if } C_{\text{srgb}} > 0.04045 \end{cases}$$
     $$L = 0.2126 R_{\text{linear}} + 0.7152 G_{\text{linear}} + 0.0722 B_{\text{linear}}$$
   - Evaluates contrast ratio $CR = \frac{L_1 + 0.05}{L_2 + 0.05}$ between foreground glyph clusters and immediate background envelopes.
   - **Thresholds**: Hard rejection if Body Text/Math $CR < 7.0:1$ (WCAG AAA); hard rejection if Large Headlines ($> 36\text{px}$) $CR < 4.5:1$; hard rejection if Subtitle Karaoke Pills $CR < 8.5:1$.

3. **Spatial Collision & AABB / PBD Minimum Translation Vector (MTV) Solver**:
   - Projects 2D Axis-Aligned Bounding Boxes $B_i = [x_{\min}, y_{\min}, x_{\max}, y_{\max}]$ for all nodes.
   - Computes intersection over union $\text{IoU}(B_i, B_j)$.
   - Computes Position-Based Dynamics (PBD) Minimum Translation Vectors (MTV):
     $$\mathbf{d} = \arg\min(|\Delta x|, |\Delta y|), \quad \Delta \mathbf{p}_i = -\frac{w_i}{w_i + w_j}\mathbf{d}, \quad \Delta \mathbf{p}_j = +\frac{w_j}{w_i + w_j}\mathbf{d}$$
   - **Thresholds**: Zero tolerance ($\text{IoU} = 0.0$) for collisions between text cards, header badges, formulas, and subtitle containers.

4. **Universal 9:16 Mobile Safe-Zone Mask Violation Checker**:
   - Applies an 8-bit binary exclusion mask $M(x, y)$ reflecting the union of YouTube Shorts, TikTok, and Instagram Reels interface overlays:
     - Top Exclusion Corridor: $Y \in [0, 220\,\text{px}]$ (status bar, search icons).
     - Bottom Exclusion Corridor: $Y \in [1420, 1920\,\text{px}]$ (creator handle, subscribe button, sound disc, navigation tabs).
     - Right Engagement Rail: $X \in [920, 1080\,\text{px}]$ between $Y \in [220, 1420\,\text{px}]$ (Like, Comment, Share button stack).
     - Sacred Usable Area: $X \in [120, 920\,\text{px}]$, $Y \in [220, 1420\,\text{px}]$ (dimensions: $800 \times 1200\,\text{px}$).
   - **Thresholds**: Any non-zero intersection between text/formula bounding boxes and $M(x, y)$ triggers an **Immediate Build Termination**.

#### 1.3 Verification & Exit Criteria
- `test_vsg_schema.py`: 100% round-trip serialization between Python Pydantic models and TypeScript schemas.
- `test_cv_heuristics.py`: Deterministic detection of simulated 1-frame jitter spikes, low-contrast text ($CR = 3.2:1$), overlapping boxes ($\text{IoU} = 0.12$), and bottom-zone clipping ($Y = 1550\,\text{px}$).
- Execution benchmark: Tier 1 CV suite analyzes 10 test frames in $<450\text{ms}$ total.

---

### Phase 2: Remotion Broadcast Adapter & Design System Token Integration
*Timeline: Weeks 3–4 | Focus: Modern Web Rendering, React 19 / Tailwind v4, Broadcast Aesthetics*

#### 2.1 Objectives & Deliverables
- Deploy the production **Remotion Broadcast Engine** in `src/` leveraging React 19, TypeScript, and Tailwind CSS v4.
- Build the core component primitive library implementing the broadcast design system specification (glassmorphic cards, typography scale, 5-band vertical layout, kinetic captions).
- Integrate `@react-three/fiber` for embedded 3D tensor and neural manifold visualizations.
- Implement synchronous font preloading and GPU-accelerated frame rendering via Chrome DevTools Protocol (CDP).

#### 2.2 Core Components & Technical Specifications

##### 2.2.1 Design System Token Integration (`src/styles/tokens.css` & `tailwind.config.ts`)
Translates the design specification into strict CSS variables and Tailwind utility classes:
- **Surface Elevation System**:
  - Level 0 (Void): `#05070E` (Obsidian Charcoal canvas).
  - Level 1 (Recessed): `#0B101D` with 30% dot matrix pattern.
  - Level 2 (Primary Glass Card): `rgba(15, 23, 42, 0.82)` with `backdrop-filter: blur(24px)`.
  - Level 3 (Elevated Pill): `rgba(30, 41, 59, 0.92)` with $1.5\text{px}$ linear gradient accent border.
  - Level 4 (Specular Glow): Radial aura centered at diagram focal point with $350\text{px}$ radius.
- **Curated Domain Palettes**:
  - Frontier AI: Electric Cyan (`#00F0FF` / `#38BDF8`) & Neon Mint (`#10B981`).
  - Deep Reasoning: Royal Violet (`#8B5CF6` / `#A855F7`) & Hyper Fuchsia (`#EC4899`).
  - Silicon & Hardware: Solar Amber (`#F59E0B` / `#FBBF24`) & Forge Orange (`#EA580C`).
  - Academic Research: Cobalt Blue (`#3B82F6`) & Emerald Mint (`#34D399`).
- **Typography Scale Hierarchy**:
  - Hero Stat: $96\text{px}$ / Weight 900 / Tracking $-0.045\text{em}$.
  - Headline H1: $56\text{px}$ / Weight 800 / Leading $1.15$ / Tracking $-0.030\text{em}$.
  - Subhead: $36\text{px}$ / Weight 700 / Leading $1.25$ / Tracking $-0.015\text{em}$.
  - Card Body: $28\text{px}$ / Weight 600 / Leading $1.35$ / Max words 14.
  - Code Snippet: $26\text{px}$ (JetBrains Mono) / Leading $1.45$ / Max 6 lines.
  - Kinetic Captions: $60\text{px}$ (Inter Black) / Active word highlight pill.

##### 2.2.2 Broadcast Component Primitive Library (`src/components/`)
1. `<GlassCard />`:
   - Utilizes CSS `backdrop-filter: blur(24px)` and dual-luminosity gradient border:
     $$\operatorname{border-image} = \operatorname{linear-gradient}(180^\circ, \operatorname{rgba}(255, 255, 255, 0.18)\ 0\%, \operatorname{rgba}(255, 255, 255, 0.03)\ 100\%)$$
   - Directional elevation shadow: `box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.65)`.
2. `<KineticCaptions />`:
   - Synchronized to word-level forced alignment timestamps from acoustic stems.
   - Grouped into 2–3 word cognitive chunks at $Y = 1300\,\text{px}$ (Band 4).
   - Active word scales $1.08\times$ with vibrant electric accent glow and zero text reflow jitter.
3. `<FormulaCard />`:
   - Pre-rendered server-side KaTeX SVG components embedded in glassmorphic capsules at $Y = 1050\,\text{px}$, bypassing client-side layout thrashing and Pango Cairo rendering defects.
4. `<SpatialStage3D />`:
   - Embedded `@react-three/fiber` canvas for 3D tensor cubes, attention routing paths, and isometric layer stacks ($+14^\circ$ pitch, $-8^\circ$ yaw).
5. `<MotionWrapper />`:
   - Implements Remotion `spring()` curves with critically damped defaults ($\text{mass}=1.0$, $\text{stiffness}=140$, $\text{damping}=16$) and $1.000\times \to 1.045\times$ continuous focal push-in.

##### 2.2.3 Spatial Layout & Safe-Zone Enforcement (`src/layouts/RootComposition.tsx`)
Enforces the 5-Band Vertical Partitioning inside the 1200px safe corridor:
- **Band 1 ($Y \in [220, 300\,\text{px}]$)**: Brand Watermark & Category Badge ($80\text{px}$ height).
- **Band 2 ($Y \in [310, 470\,\text{px}]$)**: Scene Headline H1 & Core Thesis ($160\text{px}$ height).
- **Band 3 ($Y \in [480, 1180\,\text{px}]$)**: Primary Visual Stage ($700\text{px}$ height).
- **Band 4 ($Y \in [1220, 1380\,\text{px}]$)**: Kinetic Spoken Caption Pill ($160\text{px}$ height).
- **Top & Bottom Exclusion**: Absolute zero content below $Y = 1420\,\text{px}$ or above $Y = 220\,\text{px}$.

#### 2.3 Verification & Exit Criteria
- `npm run build`: Zero TypeScript compilation errors across React 19 / Remotion packages.
- `npm run still`: Single-frame CDP render exports in $<180\text{ms}$.
- `npm run render`: 60-second test composition renders locally in $<55\text{seconds}$ @ 60fps.
- Visual inspection: Flawless glassmorphic blur, crisp subpixel font ligatures, and zero safe-zone breaches.

---

### Phase 3: Multimodal VLM Critic Gatekeeper & Layout Patching
*Timeline: Weeks 5–6 | Focus: Multi-Critic Council, Closed-Loop Repair, Quota Resilience*

#### 3.1 Objectives & Deliverables
- Deploy the **Tier 2 Multimodal VLM Critic Council** (`pipeline/qa/vlm_critic_council.py`) evaluating keyframes across four specialized rubrics.
- Implement the **Binary Hard-Gate Circuit Breaker** rejecting subjective quality defects and eliminating synthetic fallback passes (`overall_score = 8.8`).
- Build the **Closed-Loop Automated Layout Repair Loop** applying deterministic AST mutations (translation, scaling, text truncation) based on the **Visual Repair Diagnostic Ledger**.
- Integrate with `pipeline/quota_tracker.py` to ensure resilient multi-provider failover without pipeline crashes or false quality approvals.

#### 3.2 Core Components & Technical Specifications

##### 3.2.1 Tier 2 Multimodal VLM Critic Council Architecture
Frames that pass Tier 1 CV heuristics are submitted to four independent, specialized VLM evaluation personas:

```
                  ┌─────────────────────────────────────────┐
                  │ Keyframe Buffer (Passed Tier 1 CV Gate) │
                  └────────────────────┬────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ Critic A: Pedagogical │  │ Critic B: Typography  │  │ Critic C: Aesthetic   │
│ Semantic Alignment    │  │ & Cognitive Density   │  │ & Material System     │
│ (Mechanism accuracy,  │  │ (Hierarchy, <=12 words│  │ (Glassmorphism, depth │
│ 1s glance rule)       │  │ line wrap, font sizes)│  │ 60-30-10 palette rule)│
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │ Critic D: Audio-Visual│
                           │ Kinetic Pacing        │
                           │ (Frame-ahead sync,    │
                           │ 1.2s reading buffer)  │
                           └───────────┬───────────┘
                                       │
                                       ▼
                       ╔═══════════════════════════════╗
                       ║ Binary Hard-Gate Evaluator    ║
                       ║ Composite Score >= 8.5 / 10.0 ║
                       ║ All Individual Pillars >= Min ║
                       ╚═══════════════════════════════╝
                                       │
                       ┌───────────────┴───────────────┐
                    [ PASS ]                        [ FAIL ]
                       │                               │
                       ▼                               ▼
             ┌───────────────────┐           ┌───────────────────┐
             │ Approved for Final│           │ Generate Repair   │
             │ Video Assembly    │           │ Diagnostic Ledger │
             └───────────────────┘           └─────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌───────────────────┐
                                             │ Apply VSG-IR AST  │
                                             │ Patches (Iter<=3) │
                                             └─────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌───────────────────┐
                                             │ Re-render Beat via│
                                             │ Instant CDP Seek  │
                                             └───────────────────┘
```

##### 3.2.2 Critic Scoring Rubrics & Hard-Gate Thresholds

| Critic Pillar | Target Quality Standard | Minimum Passing Threshold | Hard-Gate Rejection Triggers |
| :--- | :--- | :--- | :--- |
| **Critic A: Semantic Alignment** | Geometry directly illustrates technical mechanism | **$\ge 8.5 / 10.0$** | **$< 7.5$**: Canned clipart, pie charts for deep learning, hallucinated math notation |
| **Critic B: Typography & Density** | Typographic scale, $\le 12$ words/card, no collisions | **$\ge 8.5 / 10.0$** | **$< 8.0$**: Text overlap, $> 14$ words, broken wrapping, unreadable small math |
| **Critic C: Aesthetic Finish** | 4-tier elevation, glassmorphism, 60-30-10 palette | **$\ge 8.0 / 10.0$** | **$< 7.0$**: Flat unstyled grey boxes, garish palettes, missing depth lighting |
| **Critic D: Audio-Visual Pacing** | Frame-ahead sync ($-0.04\text{s}$), $1.2\text{s}$ hold buffer | **$\ge 8.5 / 10.0$** | **$< 7.5$**: Visual motion lags audio $> 0.2\text{s}$, scene cut interrupts reading |
| **COMPOSITE VERDICT** | **$0.35 A + 0.25 B + 0.20 C + 0.20 D$** | **$\ge 8.5 / 10.0$** | **Composite $< 8.5$ OR any individual pillar failure** |

##### 3.2.3 Closed-Loop Automated Layout Repair Loop (`pipeline/qa/repair_engine.py`)
When a frame fails, the Gatekeeper emits a **Visual Repair Diagnostic Ledger** that prescribes deterministic AST mutations:
- **Spatial Translations**: Shifts colliding elements along the Minimum Translation Vector (MTV).
- **Auto-Rescaling**: Multiplies element dimensions by $0.90\times$ or $0.92\times$ if bounding box exceeds safe limits.
- **Copy Refactoring**: Truncates card subtitles exceeding 12 words to fit within cognitive caps.
- **Fast Beat Re-render**: Re-renders only the failing beat via Remotion's instant CDP seek engine ($<200\text{ms}$), capping repair attempts at $N = 3$ iterations.

##### 3.2.4 Resilient Multi-Provider Quota Failover
Integrates with `pipeline/quota_tracker.py` to prevent false approvals and pipeline hangs:
1. **Tier 1 Filtering First**: 100% of candidate frames undergo Tier 1 CV heuristics. Only 3–5 representative keyframes per short proceed to Tier 2 VLM evaluation.
2. **Provider Cascade**: Primary: Gemini 3.8 Flash $\to$ Secondary: Gemini 3.1 Flash Lite $\to$ Cloud Fallback: Ollama Cloud (`gemma4:31b:cloud` / `gpt-oss:120b:cloud`).
3. **No Synthetic Passes**: If all VLM providers hit rate limits or exhaustion, the system executes **Deterministic Solver Fallback**:
   - Applies strict geometric PBD bounding box relaxation.
   - Evaluates contrast and safe zones via Tier 1 CV.
   - Tags the audit ledger with `VERDICT: PASSED_DETERMINISTIC_FALLBACK` (audited score: actual CV metrics, never a synthetic `8.8` score).

#### 3.3 Verification & Exit Criteria
- `test_vlm_critic_council.py`: Validates structured JSON schema output across all 4 critics.
- `test_repair_loop.py`: Demonstrates that an injected text collision is resolved within 2 repair iterations.
- `test_quota_failover.py`: Confirms seamless cascading when primary Gemini API returns HTTP 429.

---

### Phase 4: Production Cutover & Hybrid Engine Orchestration
*Timeline: Weeks 7–8 | Focus: Traffic Routing, End-to-End Validation, Legacy Deprecation*

#### 4.1 Objectives & Deliverables
- Deploy the **Hybrid Engine Router** in `pipeline/run_pipeline.py` dynamically selecting the optimal rendering backend based on scene taxonomy.
- Execute canary traffic ramp: 20% $\to$ 50% $\to$ 80% $\to$ 100% broadcast standard.
- Deprecate and archive monolithic Manim scripts to `_archive/legacy_manim/`.
- Validate full end-to-end production pipelines across all test suites.

#### 4.2 Core Components & Technical Specifications

##### 4.2.1 Hybrid Engine Routing Matrix (`pipeline/engine_router.py`)
Analyzes the VSG-IR metadata and beat classification to route scenes:

```
                               ┌─────────────────────────┐
                               │       VSG-IR AST        │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │  Hybrid Engine Router   │
                               │ (pipeline/engine_router)│
                               └────────────┬────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
        [ Tech News / Deep Dive / ]   [ Continuous Calculus / ]   [ Algorithmic Code / ]
        [ Architecture Breakdown  ]   [ Pure Differential Eq  ]   [ AST Syntax Morphs  ]
                    │                       │                       │
                    ▼                       ▼                       ▼
        ╔═══════════════════════╗   ╔═══════════════════════╗   ╔═══════════════════════╗
        ║ Remotion Broadcast    ║   ║ Manim Legacy Adapter  ║   ║ Motion Canvas Adapter ║
        ║ Engine (React 19 / TS)║   ║ (Python Cairo Engine) ║   ║ (TypeScript / Canvas) ║
        ╚═══════════════════════╝   ╚═══════════════════════╝   ╚═══════════════════════╝
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Master Audio / Muxing   │
                               │ (FFmpeg Broadcast Pipe) │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ╔═════════════════════════╗
                               ║ Two-Tier QA Gatekeeper  ║
                               ║ (CV Heuristics + VLM)   ║
                               ╚═════════════════════════╝
                                            │
                                            ▼
                               [ Final Broadcast Video ]
```

##### 4.2.2 Engine Routing Rules

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   HYBRID ENGINE ROUTING MATRIX                                  │
├───────────────────────┬─────────────────────────┬───────────────────┬───────────────────────────┤
│ Narrative Taxonomy    │ Content Characteristics │ Designated Engine │ Architectural Rationale   │
├───────────────────────┼─────────────────────────┼───────────────────┼───────────────────────────┤
│ Frontier Architecture │ MoE routing, KV caches, │ Remotion          │ Native glassmorphism,     │
│ & Systems Breakdown   │ attention matrices, HUD │ (React 19 / TS)   │ 3D Three.js embeddings,   │
│                       │ metrics, paper figures  │                   │ responsive layout flow    │
├───────────────────────┼─────────────────────────┼───────────────────┼───────────────────────────┤
│ Industry Tech News &  │ Model releases, compute │ Remotion          │ Rapid turnaround (<45s),  │
│ Benchmark Showdowns   │ drag races, radar plots │ (React 19 / TS)   │ Shiki code highlighting,  │
│                       │ company announcements   │                   │ punchy kinetic motion     │
├───────────────────────┼─────────────────────────┼───────────────────┼───────────────────────────┤
│ Deep Algorithmic Code │ Complex token morphs,   │ Motion Canvas     │ Lezer AST parsing,        │
│ & Kernel Execution    │ GPU thread blocks,      │ (TypeScript)      │ instant canvas rendering, │
│                       │ memory access patterns  │                   │ sub-token interpolation   │
├───────────────────────┼─────────────────────────┼───────────────────┼───────────────────────────┤
│ Pure Mathematical     │ Riemannian manifolds,   │ Manim Legacy      │ Mathematical curve        │
│ Analysis & Calculus   │ continuous vector fields│ Adapter (Python)  │ precision, parametric     │
│                       │ topological transforms  │                   │ equations, LaTeX history  │
└───────────────────────┴─────────────────────────┴───────────────────┴───────────────────────────┘
```

##### 4.2.3 Canary Rollout Schedule & Cutover Milestones
- **Week 7 (Canary Phase)**:
  - Route 20% of pipeline jobs (`--engine=remotion`) to Remotion broadcast engine.
  - Run shadow Manim rendering in parallel; compare render times and visual QA scores.
  - Expand to 50% routing by mid-week after verifying zero regressions.
- **Week 8 (Full Cutover & Deprecation)**:
  - Transition 100% of production videos to Remotion as default (`--engine=auto`).
  - Move legacy monolithic Manim scripts (`script_driven_scene.py`, `bespoke_visual_synthesizer.py`) into `_archive/legacy_manim/`.
  - Maintain `ManimLegacyAdapter` exclusively for mathematical taxonomy exceptions.
  - Finalize all pipeline documentation and deployment scripts.

#### 4.3 Verification & Exit Criteria
- End-to-end execution: `python3 -m pipeline.run_pipeline --arxiv 2407.10405 --engine=auto` completes full video production in $<60\text{seconds}$ with $100\%$ QA pass rate.
- Automated regression suite: All test suites (`test/test_arxiv_figure_extraction.py`, `test/test_quota_failover.py`, `test/test_adversarial_pipeline_edge_cases.py`) pass with 0 failures.

---

## Technical Risk Register & Mitigation Playbooks

| Risk ID | Technical Risk Description | Severity | Likelihood | Mitigation Summary |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | Headless GPU acceleration failure in Docker CI | **CRITICAL** | Medium | Chromium ANGLE / Metal / SwiftShader fallback cascade |
| **RSK-02** | Web font rendering latency & Frame 0 FOUT | **HIGH** | High | Synchronous `@remotion/google-fonts` preloading |
| **RSK-03** | LaTeX equation rendering fidelity and parity | **HIGH** | Medium | Server-side KaTeX SVG injection with baseline clamping |
| **RSK-04** | VLM API quota exhaustion & latency overhead | **HIGH** | High | Tier 1 CV pre-filtering + cascading multi-provider failover |
| **RSK-05** | Node.js / Puppeteer memory leaks in worker pool | **MEDIUM** | Low | Worker tab recycling every 500 frames + GC allocation caps |
| **RSK-06** | Infinite oscillation in automated layout repair | **MEDIUM** | Low | Hard iteration cap ($N=3$) with deterministic card merging |

---

### Playbook 1: Headless GPU Acceleration in CI/Docker (RSK-01)

#### Failure Mode Analysis
In containerized environments (Docker, GitHub Actions, AWS ECS/Lambda), Chromium instances launched by `@remotion/renderer` frequently fail to access physical GPU devices (`/dev/dri`). This causes WebGL context crashes, black video frames, or catastrophic rendering slowdowns (10x latency spike) when software rasterizers fail to initialize.

#### Root Cause
Missing DRI device bindings, unconfigured shared memory (`/dev/shm`), and conflicting Chromium GPU sandbox flags in headless Linux containers.

#### Architectural Mitigation Playbook
1. **Container Configuration**:
   - Mount host `/dev/shm` with minimum 2GB size (`--shm-size=2gb`) to prevent Chromium IPC buffer exhaustion.
   - Install Mesa Vulkan / OpenGL drivers and SwiftShader CPU fallbacks in Dockerfile:
     ```dockerfile
     RUN apt-get update && apt-get install -y \
         libgl1-mesa-dri \
         libgl1-mesa-glx \
         libosmesa6 \
         mesa-vulkan-drivers \
         xvfb
     ```
2. **Chromium Launch Flag Strategy (`remotion.config.ts`)**:
   Implement a 3-tier fallback cascade:
   - **Tier A (Hardware Accelerated Linux/Docker)**:
     ```typescript
     Config.setChromiumOpenGlRenderer('angle');
     Config.setChromiumFlags([
       '--enable-gpu',
       '--enable-webgl',
       '--use-gl=angle',
       '--use-angle=gl',
       '--in-process-gpu',
       '--disable-dev-shm-usage',
       '--no-sandbox',
     ]);
     ```
   - **Tier B (macOS Silicon Hardware Encoding)**:
     Utilizes Apple Metal graphics via ANGLE Metal backend:
     ```typescript
     Config.setChromiumFlags(['--use-angle=metal', '--enable-zero-copy']);
     ```
   - **Tier C (SwiftShader Software Fallback)**:
     If hardware GPU initialization fails, catch the CDP error and fall back to Google SwiftShader CPU software rendering without aborting the pipeline:
     ```typescript
     Config.setChromiumFlags([
       '--disable-gpu',
       '--use-gl=swiftshader',
       '--disable-dev-shm-usage',
     ]);
     ```
3. **Verification Command**:
   ```bash
   npx remotion test-rendering --chromium-flags="--use-gl=angle"
   ```

---

### Playbook 2: Web Font Preloading & Frame 0 FOUT (RSK-02)

#### Failure Mode Analysis
When Chromium begins rendering Frame 0 ($t = 0.0\text{s}$), external web fonts (Inter, JetBrains Mono, STIX Two Math) loaded via standard CSS `@import` or Google Fonts may still be downloading. Chromium renders the initial frames using system fallback fonts (Helvetica, Times New Roman), then switches to the web font on Frame 6–10. This creates a jarring Flash of Unstyled Text (FOUT), text popping, and sudden layout reflows during the hook beat.

#### Root Cause
Asynchronous browser font loading operating independently of Remotion's frame rendering lifecycle.

#### Architectural Mitigation Playbook
1. **Local Synchronous Font Packaging**:
   - Bundle all production fonts as local WOFF2 assets in `public/fonts/` (Inter Display, JetBrains Mono, KaTeX Math). Banish remote CDN font fetching during render cycles.
2. **Remotion Font Preloader Integration (`src/index.ts`)**:
   - Utilize `@remotion/google-fonts` or native Web Font Loader wrapped in Remotion's `delayRender()` / `continueRender()` hooks:
     ```typescript
     import { delayRender, continueRender } from 'remotion';

     export const loadProductionFonts = async () => {
       const handle = delayRender('Loading production fonts');
       try {
         await document.fonts.ready;
         const fontInter = new FontFace('Inter', 'url(/fonts/Inter-Variable.woff2)', { weight: '100 900' });
         const fontMono = new FontFace('JetBrains Mono', 'url(/fonts/JetBrainsMono.woff2)');
         await Promise.all([fontInter.load(), fontMono.load()]);
         document.fonts.add(fontInter);
         document.fonts.add(fontMono);
         continueRender(handle);
       } catch (err) {
         console.error('Font preloading failed, proceeding with fallback', err);
         continueRender(handle);
       }
     };
     ```
3. **Pre-Render Font Readiness Assertion in CI**:
   - Before capturing keyframes or rendering video, assert `document.fonts.check('16px Inter') === true`.
4. **Verification Command**:
   ```bash
   npx remotion still RootComposition --frame=0 out_frame_0.png && \
   python3 -m pipeline.qa.check_font_glyphs out_frame_0.png --expected-font=Inter
   ```

---

### Playbook 3: LaTeX Equation Rendering Fidelity & Parity (RSK-03)

#### Failure Mode Analysis
Mathematical formulas are a core identity of The Model Verse Shorts. In the legacy engine, missing host `pdflatex` binaries forced the pipeline to fall back to Unicode approximations via `CleanText`, producing disjointed mathematical notation, missing fraction bars, and misaligned exponents. Conversely, client-side browser MathJax introduces heavy execution latency and layout thrashing.

#### Root Cause
Lack of a headless, self-contained mathematical typesetting pipeline that renders vector math without LaTeX system dependencies.

#### Architectural Mitigation Playbook
1. **Server-Side KaTeX Pre-Compilation (`pipeline/latex/katex_compiler.py`)**:
   - Pre-compile all LaTeX expressions in the VSG-IR into pure, standalone SVG strings or pre-rendered React KaTeX components during the scene graph compilation phase.
   - Run KaTeX headlessly via Node.js:
     ```typescript
     import katex from 'katex';
     const html = katex.renderToString(mathFormula, {
       displayMode: true,
       throwOnError: false,
       output: 'htmlAndMathml',
     });
     ```
2. **Fixed-Height Baseline Alignment (`<FormulaCapsule />`)**:
   - Encapsulate the formula inside a fixed-height glassmorphic tray ($120\text{px}$ height) with horizontal centering and automatic scale-to-fit:
     ```tsx
     <div className="w-[780px] h-[120px] flex items-center justify-center bg-slate-900/80 backdrop-blur-md rounded-2xl border border-white/10 px-6">
       <span className="scale-[clamp(0.7,calc(740px/var(--math-width)),1.1)] font-math" dangerouslySetInnerHTML={{ __html: compiledKaTeXHtml }} />
     </div>
     ```
3. **Mathematical Notation Style Standard**:
   - Standardize on `STIX Two Math` and `Computer Modern` glyph mappings.
   - Eliminate multiline formula overflow: any equation exceeding 6 terms must be split across sequential beats or stacked vertically.
4. **Verification Command**:
   ```bash
   pytest test/test_latex_rendering_parity.py
   ```

---

### Playbook 4: VLM API Quota Exhaustion & CI/CD Latency Overhead (RSK-04)

#### Failure Mode Analysis
Submitting all 3,600 frames of a 60-second video to multimodal VLM models creates massive API costs, triggers HTTP 429 rate limits, and adds 5–10 minutes of network latency to CI/CD pipelines. Furthermore, when quotas exhaust, legacy fallback code generates dummy passing scores (`8.8/10`), bypassing quality checks entirely.

#### Root Cause
Lack of pre-filtering heuristics, lack of keyframe selection intelligence, and flawed fallback error handling in `pipeline/vlm_critic.py`.

#### Architectural Mitigation Playbook
1. **Tier 1 CV Heuristics as Pre-Filter**:
   - Run Tier 1 CV heuristics locally across all video frames ($<50\text{ms}$ per frame).
   - Reject frames failing contrast, safe-zone, or collision checks immediately, terminating bad builds before making any cloud API calls.
2. **Intelligent Keyframe Selection (3–5 Frames per Video)**:
   - Extract exactly one frame per beat at the critical cognitive moment: $t = t_{\text{anchor}} + 0.8\text{s}$ (the point of maximum visual density after entrance animation settles).
   - Never submit every video frame to VLM critics.
3. **Cascading Provider Fallback Engine (`pipeline/quota_tracker.py`)**:
   - **Primary**: Gemini 3.8 Flash (`gemini-3.8-flash`) — fastest multimodal response ($<800\text{ms}$).
   - **Secondary**: Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite`) — higher rate limits.
   - **Cloud Fallback**: Ollama Cloud / OpenRouter (`gemma4:31b:cloud` or `gpt-oss:120b:cloud`).
4. **Strict Elimination of False-Pass Fallbacks**:
   - Ban synthetic `passed = True` / `overall_score = 8.8` responses in `vlm_critic.py`.
   - If all cloud APIs fail, switch to **Deterministic Layout Verification**:
     - Evaluate geometric bounds via PBD solver.
     - Evaluate contrast via WCAG AAA calculator.
     - Emit report with `audit_mode = "deterministic_offline_fallback"`.
     - Mark passing *only* if deterministic checks score 100%.
5. **Verification Command**:
   ```bash
   pytest test/test_quota_failover.py -k "test_vlm_critic_offline_fallback"
   ```

---

## Key Performance Indicators & Acceptance Criteria

### 1. Quantitative Performance & Latency Targets

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                PERFORMANCE KPI BENCHMARK TARGETS                                │
├──────────────────────────────────┬─────────────────┬─────────────────┬──────────────────────────┤
│ Metric                           │ Current (Manim) │ Target Standard │ Verification Procedure   │
├──────────────────────────────────┼─────────────────┼─────────────────┼──────────────────────────┤
│ Full Video Render (60s @ 60fps)  │ 480 – 900 s     │ < 45 s          │ Local 16-core M-series   │
│ Cloud Distributed Render         │ N/A (unstable)  │ < 4.0 s         │ @remotion/lambda pool    │
│ Single-Frame Seek Latency        │ 15.0 – 25.0 s   │ < 0.20 s        │ CDP frame capture        │
│ Tier 1 CV Gate Evaluation (frame)│ N/A             │ < 0.05 s        │ Local OpenCV / NumPy     │
│ Full Automated QA Audit (video)  │ 120 – 180 s     │ < 6.0 s         │ 5 keyframes + CV + VLM   │
│ Production Docker Image Footprint│ 2.8 – 3.8 GB    │ < 750 MB        │ Official Remotion base   │
└──────────────────────────────────┴─────────────────┴─────────────────┴──────────────────────────┘
```

### 2. Visual Defect Rate Targets

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   VISUAL DEFECT RATE TARGETS                                    │
├──────────────────────────────────┬─────────────────┬─────────────────┬──────────────────────────┤
│ Defect Category                  │ Current Rate    │ Target Standard │ Gating Enforcement       │
├──────────────────────────────────┼─────────────────┼─────────────────┼──────────────────────────┤
│ Mobile Safe-Zone Violations      │ 35 – 45%        │ 0.0% (Zero Tol) │ Tier 1 Binary Mask Gate  │
│ Text & Card Collisions (IoU > 0) │ 18 – 25%        │ 0.0% (Zero Tol) │ AABB / PBD Solver Gate   │
│ WCAG AAA Contrast Failures (<7:1)│ 12 – 18%        │ 0.0% (Zero Tol) │ Relative Luminance Gate  │
│ Motion Jitter / Strobing Spikes  │ 8 – 14%         │ 0.0% (Zero Tol) │ Optical Flow Jerk Gate   │
│ Wall-of-Text Cards (> 14 words)  │ 22 – 30%        │ 0.0% (Zero Tol) │ Pre-Render AST Linter    │
│ Audio-Visual Sync Lag (> 0.20s)  │ 20 – 30%        │ < 2.0%          │ Acoustic Anchor Linter   │
│ VLM Critic Composite Score       │ 6.8 / 10.0      │ >= 8.5 / 10.0   │ Tier 2 Multi-Critic Gate │
└──────────────────────────────────┴─────────────────┴─────────────────┴──────────────────────────┘
```

### 3. Retention Impact Expectations
Based on high-retention technical media analytics (Fireship, Apple, Alex Bowers):
- **First 3-Second Retention (Hook Bounce)**:
  - *Current Baseline*: 45–55% bounce within the first 3 seconds due to unreadable title cards, small text, and delayed visual hooks.
  - *Target Standard*: **$\ge 75\%$ retention past second 3**, achieved via high-impact stat metrics ($96\text{px}$), bold electric glows, and immediate acoustic-visual synchronization.
- **50% Completion Rate**:
  - *Current Baseline*: 18–26% viewer completion across 54-second shorts.
  - *Target Standard*: **$\ge 48\%$ completion rate**, achieved by eliminating the "7-Element Trap", enforcing the Rule of One focal target, and maintaining continuous $1.000\times \to 1.045\times$ focal breathing.
- **Audience Re-watch Rate**:
  - Expected $+35\%$ increase in replays driven by authentic mathematical diagrams, clean syntax code highlighting, and dense technical clarity.

---

## Migration & Compatibility Strategy

To ensure zero downtime, the migration preserves existing CLI entrypoints, configuration contracts, and automated workflows throughout the entire rollout.

### 1. Unified CLI Interface Compatibility
All existing pipeline invocation commands continue to function identically without breaking changes:
```bash
# Standard pipeline execution (automatically routes to optimal engine)
python3 -m pipeline.run_pipeline --arxiv 2407.10405

# Explicit engine selection overrides
python3 -m pipeline.run_pipeline --arxiv 2407.10405 --engine=remotion
python3 -m pipeline.run_pipeline --arxiv 2407.10405 --engine=manim
python3 -m pipeline.run_pipeline --arxiv 2407.10405 --engine=hybrid

# Dry-run validation mode (validates VSG-IR AST and Tier 1 CV without video muxing)
python3 -m pipeline.run_pipeline --arxiv 2407.10405 --dry-run
```

### 2. Backward Compatibility & Fallback Architecture
1. **VSG-IR as Bridge**:
   - The Narrative Planner (`script_generator.py` and `visual_director.py`) outputs standard VSG-IR JSON.
   - When `--engine=manim` is specified, `pipeline/adapters/manim_adapter.py` translates VSG-IR nodes into legacy `ScriptDrivenScene` primitives, guaranteeing that legacy scripts continue to render.
2. **Graceful Engine Failover**:
   - If Remotion rendering encounters an unexpected runtime fault in CI (e.g. Node.js environment error), the pipeline catches the exception, logs a diagnostic warning, and automatically re-routes the job to the legacy Manim adapter:
     ```python
     try:
         video_path = remotion_adapter.render(vsg_manifest)
     except RemotionRenderException as e:
         logger.warning(f"Remotion render failed ({e}), falling back to ManimLegacyAdapter...")
         video_path = manim_legacy_adapter.render(vsg_manifest)
     ```
3. **Environment Flags**:
   - The rollout is governed by runtime environment variables:
     - `THEMODELVERSE_DEFAULT_ENGINE=remotion` (defaults to Remotion when unset).
     - `THEMODELVERSE_QA_STRICT_MODE=true` (enforces hard-gate build termination on QA failure).
     - `THEMODELVERSE_ENABLE_REPAIR_LOOP=true` (activates closed-loop layout patching).

### 3. Step-by-Step Rollout Checklist

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PRODUCTION ROLLOUT CHECKLIST                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ ] Step 1: Install Node.js dependencies (@remotion/renderer, @remotion/cli, react@19)         │
│ [ ] Step 2: Validate VSG-IR JSON Schema against existing 20 paper blueprint datasets            │
│ [ ] Step 3: Integrate Tier 1 CV Gatekeeper into pipeline/run_pipeline.py as blocking gate      │
│ [ ] Step 4: Validate local Remotion still/video rendering on development workstations           │
│ [ ] Step 5: Configure Docker CI image with Chromium ANGLE / SwiftShader fallback               │
│ [ ] Step 6: Deploy 4-Critic VLM Council with quota_tracker failover cascade                     │
│ [ ] Step 7: Activate 20% canary routing in production pipeline                                  │
│ [ ] Step 8: Monitor retention analytics and QA defect logs for 7 consecutive days               │
│ [ ] Step 9: Expand canary routing to 100% broadcast standard                                    │
│ [ ] Step 10: Archive monolithic Manim scripts to _archive/legacy_manim/                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion & Architectural Sign-Off

This Phased Implementation Roadmap and Technical Risk Register provides a comprehensive, mathematically rigorous, and zero-downtime path to elevate The Model Verse Shorts into a premier broadcast-grade tech media engine. By decoupling narrative state via the VSG-IR, adopting Remotion as the primary web-native rendering standard, and fortifying the production pipeline with a Two-Tier Automated Visual QA Gatekeeper, the platform will:

1. **Cut render latency by 85–90%**, slashing full render times from ~12 minutes to $<45\text{seconds}$.
2. **Eliminate 100% of spatial collisions and mobile safe-zone occlusions** before video encoding.
3. **Deliver high-retention broadcast aesthetics** matching Fireship, Apple Keynotes, and Alex Bowers.
4. **Preserve full backward compatibility** throughout the 8-week phased transition.
