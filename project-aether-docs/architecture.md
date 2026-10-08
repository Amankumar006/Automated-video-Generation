# Project Aether v2: Technical Architecture Specification

## 1. Architectural Overview & Design Principles
Project Aether v2 is structured as a decoupled, 6-pillar autonomous virtual studio engine. It separates high-level narrative intent from deterministic spatial geometry, probabilistic generative rendering, multimodal quality assurance, and long-term production meta-learning.

```
HUMAN INTENT / TOPIC
         │
         ▼
┌──────────────────────────────┐
│  PILLAR 1: CREATIVE BRAIN    │
│  Scripting, Pacing & Directing
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  PILLAR 2: WORLD STATE GRAPH │
│  Persistent Scene / Prop Memory
└──────────────┬───────────────┘
               │
        ┌──────┴──────────────────────────┐
        ▼                                 ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│ PILLAR 3: COMPLEXITY PLANNER │   │ PILLAR 3: SPATIAL REASONER   │
│ Level 0-5 Structure Router   │   │ Headless UE5 / Blender Passes│
└──────────────┬───────────────┘   └──────────────┬───────────────┘
               │                                  │
               └─────────────────┬────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PILLAR 4: SHOT COMPILER & MODEL TOURNAMENT                      │
│ - Translates Spatial Rep Pack to Provider Specs (Veo/Kling/Runway/Open)
│ - Empirical Capability Routing / Gated Candidate Generation     │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PILLAR 5: CRITIC COUNCIL & HARD/SOFT QUALITY GATES              │
│ - Hybrid Stack: Computer Vision (Optical Flow/SSIM) + VLM Agents│
│ - Hard Gates: Anatomy, Identity, Lip-Sync, Continuity (PASS/FAIL)
│ - Soft Scoring: Cinematography, Emotional Depth, Atmosphere     │
└──────────────┬──────────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
     [ FAIL ]      [ PASS ]
        │             │
        ▼             ▼
┌──────────────┐ ┌────────────────────────────────────────────────┐
│  PILLAR 6:   │ │ POST-PRODUCTION, EDITING & MASTERING           │
│  REPAIR      │ │ Multi-track Spatial Audio, Upscaling, Grading  │
│  PLANNER     │ └──────────────────────┬─────────────────────────┘
│  (Surgical)  │                        ▼
└───────┬──────┘ ┌────────────────────────────────────────────────┐
        │        │ PILLAR 6: TEACHER AGENT (META-LEARNING)        │
        │        │ Codifies Production Rules into Memory Ledger   │
        └───────►└────────────────────────────────────────────────┘
```

---

## 2. The 6 Architectural Pillars

### Pillar 1: The Creative Brain (Script & Director)
* **Responsibility:** Ingests raw concepts, papers, or prompts; outputs an emotionally paced cinematic script and structured shot list.
* **Outputs:** Defines beat sequences, shot timing, focal intentions, lighting cues, dialogue audio tracks, and environmental parameters.

### Pillar 2: The Aether World Model (State Graph)
* **Responsibility:** Guarantees temporal and narrative continuity across any number of cuts.
* **Data Schema:**
  ```yaml
  scene:
    id: "SC_014"
    location: "abandoned_cleanroom"
    time: "23:42"
    environment:
      lighting: "emergency_red_pulsing"
      particulates: "steam_leak"
      floor: { wetness: 0.85, reflections: true }
    characters:
      maya:
        position: [3.2, 0.0, 6.7]
        facing_angle: 128
        wardrobe:
          jacket: { id: "leather_004", state: "left_sleeve_torn" }
        injuries: ["blood_cheek_right"]
        props:
          right_hand: "spectrometer_device_01"
    camera:
      previous_lens_mm: 35
      eyeline_vector: [-0.4, 0.1, 0.9]
  ```

### Pillar 3: Complexity Planner & Spatial Reasoner
* **Complexity Classification Engine:**
  * **Level 0 (Pure Text Prompt):** Atmospheric cutaways, cloudscapes, abstract concepts.
  * **Level 1 (Image / Reference Conditioned):** Establishing shots, static portraits.
  * **Level 2 (First / Last Keyframes):** Straightforward camera pans, simple character actions.
  * **Level 3 (2D Pose & Trajectory):** Talking heads, walking towards camera, gestural dialogue.
  * **Level 4 (3D Geometric Blocking):** Multi-character blocking, camera crane moves.
  * **Level 5 (Full Deterministic Simulation):** Complex physical collisions, fluid dynamics, stunts.
* **Spatial Representation Package (UE5 / Blender Headless):**
  * RGB Clay Render, Photorealistic Reference, Depth Map, Surface Normals, Object Segmentation Masks, Motion Vectors, Optical Flow, Camera Extrinsics/Intrinsics, Skeleton Rigs.

### Pillar 4: Shot Compiler & Model Tournament
* **Shot Compiler:** Adapts the abstract shot definition and Spatial Package into target API schemas:
  * *Google Veo 3.1:* First frame + Last frame + Native audio flags + Prompt.
  * *Kling 3.0:* Reference image + Static/Dynamic motion brush masks + Lip-sync audio track.
  * *Runway Gen-4.5:* Image reference + Director camera prompt + Prompt.
  * *Open-Weights (CogVideoX / HunyuanVideo via ComfyUI):* Direct Video ControlNet (Canny / OpenPose) conditioning.
* **Model Tournament:** Generates parallel candidates during calibration phases, scoring empirical capability profiles across varying shot difficulty metrics.

### Pillar 5: Critic Council & Quality Gatekeeping
* **Multi-Critic Topology:**
  * **Visual Critic (VLM):** Surface texture fidelity, lighting direction, rendering artifacts.
  * **Temporal Critic (Hybrid CV + VLM):** Optical flow motion jitter, frame-to-frame SSIM variance, morphing.
  * **Physics Critic:** Gravity, fluid consistency, anatomical deformation.
  * **Continuity Critic:** Validates observed frame data against the Aether World State Graph.
  * **Performance & Lip-Sync Critic:** Sync offset, phonetic mouth matching, emotional expression.
* **Binary Hard Gates:**
  * `ANATOMICAL_INTEGRITY`: PASS / FAIL
  * `CHARACTER_IDENTITY`: PASS / FAIL
  * `PROP_CONTINUITY`: PASS / FAIL
  * `LIP_SYNC_ALIGNMENT`: PASS / FAIL
* **Soft Scores:** Cinematography (0-10), Visual Aesthetic (0-10), Narrative Pacing (0-10). Acceptance requires all Hard Gates = PASS and Soft Score >= Project Threshold.

### Pillar 6: Repair Planner & The Dream-RSI Teacher Engine
* **Repair Planner:** Calculates minimal corrective interventions (regional temporal inpainting, audio remastering, spatial previs fallback) without naive prompt re-rolling.
* **The Dream-RSI Teacher Engine (Recursive Self-Improvement via Replay Worlds):**
  Directly adopting the **Dream-RSI** framework (arXiv:2609.14858v1), the Teacher does not merely log passive text notes. It closes a 3-stage recursive self-improvement loop:
  1. **Stage 1 (Online Exploration & Trace Logging):** Active policies guide real-world render rollouts, recording decisions into structured **Discovery Trace Trees** $\mathcal{T}_t$.
  2. **Stage 2 (Replay Simulator Pool Construction):** Historical discovery trees are indexed into an immutable Replay World Pool $\mathcal{H}_t = \mathcal{H}_{t-1} \cup \{\mathcal{T}_t\}$.
  3. **Stage 3 (Dreaming-Based Policy Improvement):** The Teacher "dreams" offline, generating $M$ candidate exploration, routing, and repair policies. It executes each candidate over the replay simulator to simulate trajectories at **zero external API cost**, optimizing the Dream-RSI Pareto objective:
     $$V_{im} = \max_{v \in \mathcal{T}_{im, k^*}} s_v - \beta_1 N_{im} + \beta_2 \frac{N_{im}}{\max\{1, k_{im}^*\}}$$
     *(where $s_v$ is visual/continuity quality, $N_{im}$ is computational work/API tokens, and the third term rewards parallel batch efficiency).*
  4. **Redeployment:** The winning policy $\pi_{t+1}$ is codified into the `ProductionKnowledgeLedger` and redeployed online to drive the next generation cycle.

---


---

## 4. Frontier Cost & Inference Efficiency Stack (2025–2026)

To scale production without cost exhaustion, Aether incorporates four state-of-the-art cost reduction and acceleration technologies:

### 1. DiT Acceleration: TeaCache & Pyramid Attention Broadcast (PAB)
* **Application:** Open-weights diffusion transformer generation (CogVideoX, HunyuanVideo, Wan2.1 in ComfyUI).
* **Mechanism:**
  * **TeaCache (Timestep Embedding Aware Cache):** Skips redundant transformer forward passes when consecutive denoising states have near-identical embeddings, yielding a **1.5× to 4.4× speedup** with zero model retraining.
  * **Pyramid Attention Broadcast (PAB):** Reuses attention maps across the stable middle 70% of denoising steps, achieving up to a **10.5× speedup** in attention layers.
* **Impact:** Slashes cloud GPU rental costs per shot by **65%–80%**.

### 2. Multi-Critic VLM Context Caching (Gemini & Anthropic)
* **Application:** Pillar 5 Critic Council inspections.
* **Mechanism:** Video frame tensors, scene schemas, and static evaluation rubrics are positioned at the head of prompt payloads using explicit `cache_control` breakpoints (Anthropic) and Gemini Context Caching.
* **Impact:** Subsequent queries across the 6 specialized critics hit the precomputed Key-Value (KV) cache, delivering a **90% discount on input token costs** and reducing Time to First Token (TTFT) by 80%.

### 3. Rectified Flow Step Distillation (Few-Step Sampling)
* **Application:** Model payload compilation.
* **Mechanism:** Configures 4-to-8 step distilled Flow Matching checkpoints (Flow-OPD, AnyFlow) and Consistency Model LoRAs instead of traditional 30–50 step diffusion loops.
* **Impact:** Reduces Neural Function Evaluations (NFEs) by **4×–8×**, reducing execution latency from 90s to under 15s per clip.

### 4. Speculative Video Rendering (Hierarchical Pyramidal Gating)
* **Application:** Production pipeline & Gatekeeper.
* **Mechanism:** 
  1. Aether first generates a rapid low-resolution draft (480p at 15 FPS) in ~4 seconds.
  2. The draft is immediately audited by the Critic Council Hard Gates.
  3. If anatomical deformities, identity breaks, or prop violations occur, the shot is rejected or repaired immediately.
  4. Only shots that **PASS** all Hard Gates trigger expensive high-resolution (1080p/4K) latent upscaling.
* **Impact:** Eliminates 75% of wasted high-resolution compute on flawed generations.

---

## 5. Ground-Truth API Constraints & Technical Feasibility
1. **Commercial Model Limitations:** Commercial closed APIs (Veo, Runway, Kling) do not expose raw depth/normal ControlNet tensors. The Shot Compiler solves this by converting 3D previs into photorealistic first/last frame pairs, relying on the model for interpolation while preserving geometry.
2. **Open-Weights Complement:** For shots requiring absolute mathematical adherence to camera paths or limb poses, Aether routes workloads to local/cloud ComfyUI instances running CogVideoX / HunyuanVideo with specialized ControlNet nodes.
3. **Hybrid Verification:** High-speed temporal anomalies (e.g., a 3-frame glitch) are invisible to standard VLM calls. Aether combines OpenCV optical flow and frame differential metrics with VLM semantic reasoning.
