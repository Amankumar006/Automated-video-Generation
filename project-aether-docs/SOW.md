# Statement of Work (SOW): Project Aether

## 1. Project Overview & Objectives
* **Project Title:** Project Aether - Autonomous Cinematic Video Generation Engine
* **Branch:** `feature/project-aether`
* **Objective:** Design, build, and deploy an end-to-end autonomous video production system that replaces manual and rigid programmatic video generation with an intelligent, persistent virtual studio capable of producing broadcast-quality, temporally consistent cinematic shorts and films.

---

## 2. Scope of Work & Deliverables

### Deliverable 1: AetherBench Evaluation Suite (Phase 0) [DELIVERED & VERIFIED]
* **Scope:** 250 standardized, difficult cinematic benchmark scenarios covering multi-character interactions, hand-object handoffs, high-speed camera tracking, glass/reflections, physical simulations, and rapid lighting transitions.
* **Format:** JSON schema defining scene variables, character descriptors, expected physical constraints, and automated evaluation metrics.

### Deliverable 2: Model Laboratory & Empirical Profiler (Phase 1)
* **Scope:** Test runner executing AetherBench against Google Veo 3.1, Kling 3.0, Runway Gen-4.5, and CogVideoX/HunyuanVideo.
* **Deliverable:** Empirical capability matrix mapping shot parameters to model success probabilities, costs, and latencies.

### Deliverable 3: Aether World Model & State Graph (Phase 2) [DELIVERED & VERIFIED]
* **Scope:** Python/Pydantic state engine tracking persistent scene metadata, character models, wardrobe states, prop possession, lighting vectors, and eyeline coordinates across multi-shot sequences.
* **Deliverable:** `AetherWorldModel` module with graph query, delta mutation, and serialization APIs.

### Deliverable 4: Complexity Planner & Spatial Previs Engine (Phases 3 & 7)
* **Scope:** Rules engine classifying shots into Levels 0-5. Headless Unreal Engine 5 / Blender automation script exporting Spatial Representation Packages (first/last frames, depth, normals, motion vectors).
* **Deliverable:** `ComplexityPlanner` and `HeadlessSpatialBridge` modules.

### Deliverable 5: Shot Compiler & Multi-Model Tournament (Phases 3 & 5) [PARTIAL: Shot Compiler DONE]
* **Scope:** Translation layer converting abstract shot requirements and 3D passes into target API payloads. Dynamic tournament runner for candidate generation.
* **Deliverable:** `ShotCompiler` with provider plugins for Google GenAI (Veo), Kling, Runway, and ComfyUI.

### Deliverable 6: Critic Council & Quality Gatekeeping (Phase 4) [DELIVERED & VERIFIED]
* **Scope:** Multi-agent inspection suite combining computer vision heuristics (Optical Flow, SSIM) with multimodal LLMs.
* **Deliverable:** `CriticCouncil` implementing Hard Gates (Anatomy, Identity, Continuity, Lip-Sync) and Soft Aesthetics scoring.

### Deliverable 7: Surgical Repair Planner & Dream-RSI Teacher Engine (Phases 6 & 9) [DELIVERED & VERIFIED]
* **Scope:** Minimal corrective intervention planner for regional temporal inpainting and audio remastering. Implementation of the **Dream-RSI Recursive Self-Improvement Engine** (arXiv:2609.14858v1) converting accumulated render traces into a Replay Simulator Pool and running offline policy dreaming to optimize routing and repair heuristics at zero API cost.
* **Deliverable:** `RepairPlanner`, `DiscoveryTraceTree`, `ReplaySimulatorWorld`, `PolicyDreamer`, and `ProductionKnowledgeLedger` modules.

### Deliverable 8: Autonomous Director Pipeline (Phase 10) [DELIVERED & VERIFIED]
* **Scope:** Unified CLI and daemon enabling prompt-to-mastered-film execution without human intervention.
* **Deliverable:** `pipeline/aether_director.py` and automated test verification suite.

---

## 3. Milestones & Acceptance Criteria
| Milestone | Description | Acceptance Criteria |
|---|---|---|
| **M1: Benchmark & Lab** | AetherBench & Model Lab | [PARTIAL: AetherBench DONE] 250 test cases operational; Model Lab in progress. |
| **M2: Memory & Compilation** | State Graph & Shot Compiler | [COMPLETED 2026-10-05] State Graph and Shot Compiler operational with 107 combined tests passing. |
| **M3: Verification & Gating** | Critic Council & CV Stack | [COMPLETED 2026-10-05] Critic Council and CV optical flow/flicker stack operational with 52 unit tests. |
| **M4: Surgical Repair** | Repair Planner & Inpainting | [COMPLETED 2026-10-05] Surgical Repair Planner and TemporalMaskEngine operational with 46 unit tests passing. |
| **M5: Spatial Engine** | Headless 3D Previs Integration | UE5/Blender exports valid Spatial Representation Packages from State Graph inputs. |
| **M6: Autonomous Director** | End-to-End Orchestrator | [COMPLETED 2026-10-05] Autonomous Director CLI and Orchestrator operational with 328 passing tests. |

---

## 4. Boundaries & Assumptions
* **In-Scope:** Narrative planning, persistent state tracking, 3D previs conditioning, multi-model generation routing, multimodal verification, surgical repair, spatial audio mixing, and meta-learning.
* **Out-of-Scope:** Real-time game engine rendering (interactive frame rates < 30ms), physical camera hardware control, human actor motion capture studio setup.
* **Dependencies:** Valid API credentials for Google Gemini/Veo, ElevenLabs, Runway, and Kling; local or cloud GPU compute (NVIDIA RTX 4090 or cloud A100/H100) for headless 3D and open-weights ComfyUI workloads.
