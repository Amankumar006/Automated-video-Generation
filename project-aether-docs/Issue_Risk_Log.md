# Issue & Risk Log: Project Aether

## 1. Active Issues (Current Blockers & Tasks)
| Issue ID | Date Logged | Priority | Category | Summary & Description | Assigned Owner | Status | Target Resolution |
|---|---|:---:|---|---|---|:---:|---|
| **ISS-001** | 2026-10-04 | **HIGH** | Architecture | **Commercial Model ControlNet Gap:** Confirmed Runway Gen-4.5 and Google Veo 3.1 do not accept external depth/normal ControlNet maps directly via API. | Shot Compiler Team | **OPEN** | Finalize First/Last keyframe rendering strategy for closed APIs and ComfyUI/CogVideoX for open ControlNets. |
| **ISS-002** | 2026-10-04 | **HIGH** | Verification | **VLM Temporal Frequency Limitation:** Standard VLM video prompts miss 1-3 frame localized deformations. | Critic Council Team | **OPEN** | Implement OpenCV Farneback optical flow motion vector analyzer alongside Gemini VLM prompts. |
| **ISS-008** | 2026-10-05 | **HIGH** | Implementation | **Phase 6 Surgical Repair Planner:** Regional temporal inpainting, audio remastering, and spatial previs fallback based on CriticCouncil failure directives. | Repair Team | **RESOLVED** | Build `aether/repair/` surgical repair engine. |
| **ISS-005** | 2026-10-05 | **MEDIUM** | Implementation | **Phase 1 Model Laboratory Client Interfaces:** Need unified adapter interface for Veo 3.1, Kling 3.0, Runway, and ComfyUI. | Integration Team | **OPEN** | Implement `aether.models` provider wrappers. |

---

## 2. Change Log of Closed / Mitigated Issues
* **ISS-012 (Resolved 2026-10-05):** Phase 10 Autonomous Director Master Pipeline implemented with `aether/director/orchestrator.py`, unified CLI (`python3 -m aether.director`), speculative gating, continuity auditing, and 28 integration tests.
* **ISS-009 & ISS-011 (Resolved 2026-10-05):** Phase 9 Dream-RSI Teacher Engine implemented with Discovery Trace Trees, Replay Simulator World Pool, offline Policy Dreamer, Production Knowledge Ledger, and Frontier Efficiency Stack (TeaCache/PAB nodes and VLM Context Caching).
* **ISS-008 (Resolved 2026-10-05):** Phase 6 Surgical Repair Engine implemented with minimum intervention triage, feathering mask engine, audio remuxing, and auto-fallback execution.
* **ISS-008 (Resolved 2026-10-05):** Phase 6 Surgical Repair Engine implemented with `TemporalMaskEngine` (RSK-004 distance feathering and ramp padding), `RepairPlanner` (Minimum Necessary Intervention), and `SurgicalRepairExecutor`.
* **ISS-007 (Resolved 2026-10-05):** Phase 4 Critic Council implemented with hybrid CV (optical flow, 4x4 subgrid flicker detection), 6 specialized critics, and binary hard gatekeeping.
* **ISS-006 (Resolved 2026-10-05):** Phase 3 Complexity Planner & Shot Compiler implemented with Level 0-5 classification and provider compilers for Veo 3.1, Kling 3.0, Runway Gen-4.5, and ComfyUI (CogVideoX/HunyuanVideo).
* **ISS-004 (Resolved 2026-10-05):** AetherBench Test Suite Schema & Runner implemented in `aether/bench/` with 56 passing unit tests, full Pydantic validation, 250 benchmark scenario suite, and synthetic defect ground-truth dataset.
* **ISS-003 (Resolved 2026-10-04):** Initialized `feature/project-aether` branch, preserving `main` stability while establishing dedicated project documentation and agent instructions.
