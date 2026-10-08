# Project Management Plan (PMP): Project Aether

## 1. Governance & Execution Methodology
Project Aether utilizes an **Empirical Test-Driven Autonomous Development** methodology. Development is structured around empirical validation rather than speculative prompt engineering.
* **Version Control:** Branch `feature/project-aether` off `main`. All changes validated via unit tests and automated regression suites before merging.
* **Execution Paradigm:** Agentic pair-programming with human architectural oversight. Autonomous subagents execute specialized workflows (Benchmarking, State Modeling, Verification, Repair).

---

## 2. Roles & Agent Responsibilities
| Role / Agent | Responsibility |
|---|---|
| **Human Architect / Director** | Vision guidance, quality standard setting, final sign-off. |
| **Antigravity Orchestrator** | High-level roadmap execution, task dispatching, system integration. |
| **State Modeler Agent** | Maintenance and expansion of `AetherWorldModel` and continuity schemas. |
| **Compiler & Bridge Agent** | Adapter integration for Veo, Kling, Runway, ComfyUI, and headless UE5. |
| **Critic Council Agents** | Visual, Temporal, Physics, and Continuity defect auditing. |
| **Repair Specialist Agent** | Localized masking, temporal interpolation, and inpainting workflows. |
| **Teacher Agent** | Memory ledger curation, pattern analysis, production policy updates. |

---

## 3. Quality Management Plan
Quality is enforced through a strict two-tiered gating protocol:
1. **Automated Unit & Integration Testing:** Every module must have 100% passing tests in `test/test_aether_*.py`.
2. **Aether Quality Gating (AQG):**
   * **Tier 1 (Hard Gates):** Zero tolerance for anatomical deformities, identity drift, lip-sync misalignment, or State Graph continuity violations. Failure triggers the Repair Planner.
   * **Tier 2 (Soft Scores):** Evaluated only after all Hard Gates pass. Multi-vector aesthetic and emotional scoring must achieve `>= 8.0 / 10.0`.

---

## 4. Cost, Compute & Quota Management
To avoid financial and latency exhaustion from unconstrained model generation:
* **Complexity-Gated Execution:** Pure text/image shots are never routed to expensive 3D or high-tier video models.
* **Restricted Tournaments:** Full multi-model tournaments are enabled only during Phase 1 profiling or when a primary model fails three consecutive repair cycles.
* **Local vs. Cloud Splitting:** Lightweight computer vision (Optical Flow, SSIM) runs locally. Heavy diffusion passes utilize cloud APIs or targeted GPU spot instances.

---

## 5. Skills & Tooling Integration Protocol
Following project guidelines, when external capabilities or automation routines are discovered (e.g., via the open ecosystem at [skills.sh](https://www.skills.sh/)):
1. Inspect the skill structure and logic.
2. Adapt the instructions into the Antigravity standard format (`SKILL.md` with YAML frontmatter).
3. Place within `.gemini/config/skills/<skill-name>/SKILL.md` or workspace configuration.
4. Verify execution without external unverified binary dependencies.

---

## 6. Dream-RSI Meta-Optimization & Cost Strategy
Following the breakthrough methodology of **Dream-RSI** (Zheng et al., 2026):
1. **The Core Financial Constraint:** Running trial-and-error meta-learning on live commercial video APIs (Veo 3.1, Kling 3.0, Runway Gen-4.5) is financially unsustainable.
2. **Offline Dreaming Protocol:** The system treats completed generation and repair episodes as an evolving **Replay Simulator Pool**. 
3. **Zero-API-Cost Policy Refinement:** Candidate exploration policies, complexity thresholds, and model routing heuristics are evaluated by replaying trajectories across pre-recorded discovery trees.
4. **Pareto Evaluation:** Policies are ranked on a Pareto curve balancing solution quality, total work (API probe cost), and parallel execution speedup. Only policies demonstrably superior in simulation are redeployed online.
