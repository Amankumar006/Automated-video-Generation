# Project Schedule: Project Aether

## 1. Timeline & Phased Roadmap

```mermaid
gantt
    title Project Aether Engineering Roadmap
    dateFormat  YYYY-MM-DD
    section Foundation
    Phase 0: AetherBench Framework       :done, p0, 2026-10-05, 1d
    Phase 1: Model Laboratory            :p1, after p0, 10d
    section Core Intelligence
    Phase 2: Aether World State Graph    :done, p2, 2026-10-05, 1d
    Phase 3: Complexity & Shot Compiler  :done, p3, 2026-10-05, 1d
    section Verification & Quality
    Phase 4: Critic Council & Gates      :done, p4, 2026-10-05, 1d
    Phase 5: Model Tournament            :p5, after p3, 7d
    Phase 6: Surgical Repair Engine      :done, p6, 2026-10-05, 1d
    section Spatial & Audio
    Phase 7: Headless 3D Spatial Engine  :p7, after p3, 12d
    Phase 8: Audio & Spatial Mastering   :p8, after p6, 7d
    section Autonomous Loop
    Phase 9: Dream-RSI Teacher Engine    :done, p9, 2026-10-05, 1d
    Phase 10: Autonomous Director Master :done, p10, 2026-10-05, 1d
```

---

## 2. Milestone Deliverable Dates
* **M0 (COMPLETED 2026-10-05):** AetherBench test suite with 250 test cases, registry, evaluator, and 56 unit tests operational.
* **M1 (Day 17):** Empirical capability profiles across Veo, Kling, Runway, and CogVideoX documented.
* **M2 (COMPLETED 2026-10-05):** Persistent Aether World Model passing multi-shot continuity tests with 55 unit tests.
* **M3 (COMPLETED 2026-10-05):** Shot Compiler translating State Graph into provider-specific payloads (Veo 3.1, Kling 3.0, Runway Gen-4.5, ComfyUI) with 52 unit tests.
* **M4 (COMPLETED 2026-10-05):** Critic Council operational with CV optical flow, micro-flicker subgrid detection, 6 specialized critics, and 52 unit tests.
* **M5 (COMPLETED 2026-10-05):** Surgical Repair Engine operational with feathering, temporal padding, minimum intervention triage, and 46 unit tests.
* **M6 (Day 64):** Headless UE5/Blender exporting valid Spatial Representation Packages.
* **M7 (COMPLETED 2026-10-05):** Dream-RSI Teacher Engine operational with Replay Simulator Pool, offline Policy Dreamer, Frontier Efficiency Stack, and 39 unit tests (300 total Aether tests passing).
* **M8 (COMPLETED 2026-10-05):** End-to-end Autonomous Director operational across CLI and daemon, with 328 total unit and integration tests passing.

---

## 3. Critical Path Analysis
The critical path runs directly through:
`AetherBench (P0) -> State Graph (P2) -> Shot Compiler (P3) -> Critic Council (P4) -> Repair Engine (P6) -> Autonomous Director (P10)`

Any delay in State Graph schema finalization directly delays Shot Compiler and 3D spatial integration.
