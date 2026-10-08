# Work Breakdown Structure (WBS): Project Aether

```
1.0 Project Aether
├── 1.1 Phase 0: AetherBench Evaluation Framework [COMPLETED]
│   ├── 1.1.1 Benchmark Scenario Schema Design [DONE] (JSON/Pydantic)
│   ├── 1.1.2 250 Stress-Test Scenarios [DONE] (Character, Physics, Optics, Motion)
│   ├── 1.1.3 Synthetic Defect Ground-Truth Dataset Creation [DONE]
│   └── 1.1.4 Automated Benchmark Runner & Scorer [DONE]
├── 1.2 Phase 1: Model Laboratory & Empirical Profiler
│   ├── 1.2.1 Provider Client Wrappers (Google Veo 3.1, Kling 3.0, Runway Gen-4.5)
│   ├── 1.2.2 Open-Weights ComfyUI Bridge (CogVideoX, HunyuanVideo)
│   ├── 1.2.3 Batch Execution across AetherBench
│   └── 1.2.4 Empirical Capability Matrix & Cost/Latency Profiler
├── 1.3 Phase 2: Aether World Model (Scene State Graph) [COMPLETED]
│   ├── 1.3.1 Hierarchical Scene Graph Schema [DONE] (Scene, Character, Prop, Camera, Light)
│   ├── 1.3.2 State Mutation & Delta Engine [DONE]
│   ├── 1.3.3 Multi-Shot Continuity Validator [DONE]
│   └── 1.3.4 Serialization, Persistence & Graph Query Interface [DONE]
├── 1.4 Phase 3: Complexity Planner & Shot Compiler [COMPLETED]
│   ├── 1.4.1 Complexity Classifier (Levels 0 through 5) [DONE]
│   ├── 1.4.2 Representation Package Definition [DONE] (Depth, Normal, Keyframe, Motion)
│   ├── 1.4.3 Shot Compiler for Google Veo 3.1 [DONE]
│   ├── 1.4.4 Shot Compiler for Kling 3.0 & Runway Gen-4.5 [DONE]
│   ├── 1.4.5 Shot Compiler for Open Video ControlNet Payloads [DONE]
│   └── 1.4.6 TeaCache, PAB & Few-Step Flow Distillation Node Configurations [DONE]
├── 1.5 Phase 4: Critic Council & Quality Gatekeeping [COMPLETED]
│   ├── 1.5.1 Visual & Artifact Critic Agent (VLM) [DONE]
│   ├── 1.5.2 Temporal Critic [DONE] (OpenCV Optical Flow + SSIM Differential)
│   ├── 1.5.3 Continuity Critic [DONE] (Cross-referencing State Graph)
│   ├── 1.5.4 Lip-Sync & Acoustic Performance Critic [DONE]
│   ├── 1.5.5 Binary Hard Gates & Soft Scoring Evaluation Engine [DONE]
│   └── 1.5.6 Multi-Critic VLM Prefix & KV Context Caching Pipeline [DONE]
├── 1.6 Phase 5: Model Tournament & Dynamic Router
│   ├── 1.6.1 Parallel Candidate Generation Orchestrator
│   ├── 1.6.2 Candidate Ranking & Selection Engine
│   └── 1.6.3 Policy Learning Engine for Adaptive Routing
├── 1.7 Phase 6: Surgical Repair Engine [COMPLETED]
│   ├── 1.7.1 Defect Localization & Bounding Box Extractor [DONE]
│   ├── 1.7.2 Temporal Mask Generation Engine [DONE]
│   ├── 1.7.3 Regional Inpainting & Latent Stitching [DONE]
│   └── 1.7.4 Audio-Only Remaster & Lip-Sync Retargeting [DONE]
├── 1.8 Phase 7: Spatial Engine (Headless 3D Previs)
│   ├── 1.8.1 Headless UE5 / Blender Automation CLI
│   ├── 1.8.2 Automated Low-Poly Scene & Asset Assembly from State Graph
│   ├── 1.8.3 Camera Trajectory & Lighting Rig Exporter
│   └── 1.8.4 Multi-Pass Render Pipeline (RGB Clay, Depth, Normals, Masks)
├── 1.9 Phase 8: Audio Synthesis & Spatial Mastering
│   ├── 1.9.1 Multi-Voice Dialogue Engine (ElevenLabs Neural Routing)
│   ├── 1.9.2 Foley & Acoustic Sound Effect Aligner
│   ├── 1.9.3 Soundtrack Composition & Pacing Engine
│   └── 1.9.4 3D Spatial Audio Positioning & Mastering
├── 1.10 Phase 9: Dream-RSI Teacher Engine & Recursive Self-Improvement [COMPLETED]
│   ├── 1.10.1 Discovery Trace Tree Schema & Episode Serializer [DONE] (Node States, Actions, Defects, Scores)
│   ├── 1.10.2 Replay Simulator World Pool Constructor [DONE] (Historical Tree Indexing)
│   ├── 1.10.3 Dreaming-Based Policy Optimizer [DONE] (Evaluating Complexity & Routing Heuristics at Zero API Cost)
│   └── 1.10.4 Production Knowledge Ledger & Dynamic Studio Policy Redeployment [DONE]
└── 1.11 Phase 10: Autonomous Director Integration [COMPLETED]
    ├── 1.11.1 Master Pipeline CLI & Daemon Orchestrator [DONE]
    ├── 1.11.2 End-to-End Regression Test Suite [DONE]
    └── 1.11.3 Production Deployment & Auto-Publishing Integration [DONE]
```
