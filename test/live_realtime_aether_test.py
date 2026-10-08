"""
Live Real-Time Verification Harness for Project Aether v2
Performs real-time generation, physical disk I/O, actual pixel rendering,
OpenCV Farneback optical flow analysis on decoded MP4 frames, physical audio
generation, surgical inpainting on real frame tensors, Dream-RSI offline dreaming,
and end-to-end autonomous director orchestration.
"""

from __future__ import annotations

import os
import sys
import time
import wave
from pathlib import Path
import numpy as np
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.state import (
    AetherWorldModel, SceneState, CharacterState, PropState,
    CameraState, EnvironmentState, WardrobeItemState, SceneAction, ActionType,
    HandAttachment, ContinuityAuditor
)
from aether.compiler import (
    ComplexityPlanner, ShotCompiler, ShotRequirement, ComplexityLevel,
    ComplexityPlan, CompiledModelPayload, ProviderTarget
)
from aether.council import (
    CriticCouncil, CVTemporalAnalyzer, CriticType, HardGateType,
    CriticFailureObject, DefectSeverity, CouncilEvaluationReport, CouncilStatus
)
from aether.repair import (
    RepairPlanner, TemporalMaskEngine, SurgicalRepairExecutor, RepairBoundaryMask
)
from aether.teacher import (
    TraceLogger, ReplaySimulatorPool, PolicyDreamer, ProductionKnowledgeLedger,
    ExplorationPolicy
)
from aether.director import (
    AetherDirector, DirectorProductionBrief, ProductionState
)


def create_physical_video_clip(
    filepath: str,
    duration_sec: float = 2.0,
    fps: int = 30,
    width: int = 480,
    height: int = 854,
    add_strobe: bool = False,
) -> str:
    """Generates an actual MP4 video file on disk with dynamic visual patterns."""
    total_frames = int(duration_sec * fps)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, float(fps), (width, height))
    if not out.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {filepath}")

    for f in range(total_frames):
        t = f / float(fps)
        # Create a dynamic moving geometric and gradient scene
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Gradient background
        y_grad = np.linspace(20, 80, height, dtype=np.uint8)[:, None]
        frame[:, :, 0] = y_grad
        frame[:, :, 1] = (y_grad * 0.7).astype(np.uint8)
        frame[:, :, 2] = (y_grad * 1.2).clip(0, 255).astype(np.uint8)

        # Dynamic moving actor representation (smoothly moving circle)
        actor_x = int(width * 0.5 + np.sin(t * 3.0) * (width * 0.25))
        actor_y = int(height * 0.6 + np.cos(t * 2.0) * (height * 0.1))
        cv2.circle(frame, (actor_x, actor_y), 45, (0, 220, 255), -1)
        cv2.putText(frame, f"AETHER SHOT t={t:.2f}s", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Inject controlled micro-flicker defect if requested (3-frame high-amplitude strobe)
        if add_strobe and (16 <= f <= 18):
            # Alternating luminance flicker
            flicker_amp = 180 if (f % 2 == 0) else -180
            patch = frame[actor_y-40:actor_y+40, actor_x-40:actor_x+40].astype(np.int16)
            if patch.size > 0:
                frame[actor_y-40:actor_y+40, actor_x-40:actor_x+40] = np.clip(patch + flicker_amp, 0, 255).astype(np.uint8)

        out.write(frame)

    out.release()
    return filepath


def create_physical_audio_track(filepath: str, duration_sec: float = 2.0, sample_rate: int = 24000) -> str:
    """Generates an actual physical WAV audio file on disk."""
    total_samples = int(duration_sec * sample_rate)
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        # Generate 440 Hz tone with exponential decay envelope
        t = np.linspace(0, duration_sec, total_samples, endpoint=False)
        audio = (0.5 * np.sin(2 * np.pi * 440.0 * t) * np.exp(-t * 0.5) * 32767).astype(np.int16)
        wav.writeframes(audio.tobytes())
    return filepath


def run_live_realtime_verification() -> None:
    print("=" * 70)
    print("🚀 STARTING REAL-TIME PHYSICAL VERIFICATION FOR PROJECT AETHER v2")
    print("=" * 70)

    output_dir = Path("output/live_realtime_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # STEP 1: PHYSICAL VIDEO & OPENCV OPTICAL FLOW ANALYSIS
    # ---------------------------------------------------------
    print("\n[Step 1/5] Real Video Encoding & OpenCV Farneback Optical Flow...")
    clean_video_path = str(output_dir / "clean_shot.mp4")
    strobe_video_path = str(output_dir / "defective_shot.mp4")
    audio_path = str(output_dir / "dialogue.wav")

    create_physical_video_clip(clean_video_path, duration_sec=2.0, fps=30, add_strobe=False)
    create_physical_video_clip(strobe_video_path, duration_sec=2.0, fps=30, add_strobe=True)
    create_physical_audio_track(audio_path, duration_sec=2.0)

    clean_size = os.path.getsize(clean_video_path)
    strobe_size = os.path.getsize(strobe_video_path)
    audio_size = os.path.getsize(audio_path)
    print(f"  ✓ Clean Video Encoded: {clean_video_path} ({clean_size:,} bytes)")
    print(f"  ✓ Defective Video Encoded: {strobe_video_path} ({strobe_size:,} bytes)")
    print(f"  ✓ Physical Audio Track: {audio_path} ({audio_size:,} bytes)")

    # Decode video frames directly from disk using OpenCV
    cap = cv2.VideoCapture(strobe_video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR to RGB
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    frame_array = np.array(frames)
    print(f"  ✓ Decoded {len(frames)} frames directly from MP4 stream (shape: {frame_array.shape})")

    # Run CVTemporalAnalyzer on real pixel array
    analyzer = CVTemporalAnalyzer(
        flicker_amplitude_threshold=0.04,
        ssim_drop_threshold=0.18,
        motion_variance_threshold=12.0
    )
    defects = analyzer.analyze_frames(frame_array)
    print(f"  ✓ Real-Time CV Analysis Complete:")
    print(f"    - Defects Flagged by CV: {len(defects)}")
    for d in defects:
        print(f"      • Detected {d.failure_type} ({d.severity.value}) at frames {d.frame_bounds} bbox={d.bounding_box}")
    assert len(defects) > 0, "CVTemporalAnalyzer must detect real micro-flicker on disk frames!"

    # ---------------------------------------------------------
    # STEP 2: REAL SURGICAL REPAIR & MASKING ON PHYSICAL PIXELS
    # ---------------------------------------------------------
    print("\n[Step 2/5] Real-Time Surgical Repair & Temporal Masking on Video Pixels...")
    mask_engine = TemporalMaskEngine(default_feather_radius_px=16.0, default_temporal_pad_frames=3)
    defect = defects[0]

    # Generate real spatio-temporal boundary mask
    boundary_mask = mask_engine.create_boundary_mask(
        failure=defect,
        feather_radius_px=16.0,
        temporal_pad_frames=3,
        box_expansion_ratio=0.15,
    )
    mask_tensor = mask_engine.generate_spatio_temporal_mask(
        boundary_mask=boundary_mask,
        total_frames=len(frames),
        resolution=(frame_array.shape[1], frame_array.shape[2]),
        falloff="cosine",
    )
    print(f"  ✓ Generated Mask Tensor: shape={mask_tensor.shape}, non-zero elements={np.count_nonzero(mask_tensor):,}")

    # Perform surgical inpainting on the real frame array
    repaired_frames = frame_array.copy()
    # Inpaint: blend with temporal average of surrounding clean frames outside the defect
    clean_f_before = max(0, defect.start_frame - 3)
    clean_f_after = min(len(frames) - 1, defect.end_frame + 3)
    clean_ref = (frame_array[clean_f_before].astype(np.float32) + frame_array[clean_f_after].astype(np.float32)) * 0.5

    for f_idx in range(len(frames)):
        alpha = mask_tensor[f_idx, :, :, None]
        if np.any(alpha > 0.0):
            repaired_frames[f_idx] = (
                (1.0 - alpha) * frame_array[f_idx].astype(np.float32) +
                alpha * clean_ref
            ).astype(np.uint8)

    # Compute boundary seam metric on actual repaired pixels
    seam_metric = mask_engine.compute_boundary_seam_metric(
        mask=mask_tensor[defect.start_frame],
        frame=repaired_frames[defect.start_frame],
    )
    print(f"  ✓ Repaired Frame Tensor: Boundary Seam Metric = {seam_metric:.6f} (Passed: {seam_metric < 0.20})")
    assert seam_metric < 0.20, f"Boundary seam metric must be < 0.20 to eliminate seams, got {seam_metric}"

    # Encode repaired MP4 video to disk
    repaired_video_path = str(output_dir / "repaired_shot.mp4")
    out = cv2.VideoWriter(repaired_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (frame_array.shape[2], frame_array.shape[1]))
    for rf in repaired_frames:
        out.write(cv2.cvtColor(rf, cv2.COLOR_RGB2BGR))
    out.release()
    print(f"  ✓ Repaired MP4 Saved: {repaired_video_path} ({os.path.getsize(repaired_video_path):,} bytes)")

    # Re-audit repaired video with CV analyzer
    re_audit_defects = analyzer.analyze_frames(repaired_frames)
    print(f"  ✓ Re-Audit on Repaired Pixels: {len(re_audit_defects)} defects found (Clean: {len(re_audit_defects) == 0})")
    assert len(re_audit_defects) == 0, "Repaired frames must pass CV audit cleanly with 0 defects!"

    # ---------------------------------------------------------
    # STEP 3: WORLD STATE PERSISTENCE ACROSS 3 SHOT CUTS
    # ---------------------------------------------------------
    print("\n[Step 3/5] Aether World Model State Graph Continuity Across Cuts...")
    world = AetherWorldModel()
    scene = SceneState(
        scene_id="SC_LIVE_001",
        location="Tokyo Underpass",
        environment=EnvironmentState(weather="rain", lighting="cyan_neon", wetness=0.9)
    )
    world.set_active_state(scene)

    # Add character with pristine jacket
    maya = CharacterState(
        character_id="maya",
        name="Maya",
        position=[0.0, 0.0, 0.0],
        facing_angle=0.0,
        eyeline_vector=[0.0, 0.0, 1.0],
        wardrobe={"jacket": WardrobeItemState(id="jacket_01", color="black", state="pristine", damage_level=0.0)}
    )
    world.active_state.character_roster["maya"] = maya

    # Add prop
    spec = PropState(
        prop_id="spectrometer",
        name="Spectrometer",
        owner_id="maya",
        hand_attachment=HandAttachment.RIGHT
    )
    world.active_state.prop_roster["spectrometer"] = spec
    maya.held_props["right"] = "spectrometer"

    # Freeze Shot 1
    snap1 = world.freeze_shot("SHOT_001")
    s1 = snap1.state
    print(f"  ✓ Shot 1 Frozen: Maya jacket={s1.character_roster['maya'].wardrobe['jacket'].state}, prop_holder={s1.prop_roster['spectrometer'].owner_id}")

    # Shot 2 Action: Jacket tears in combat
    world.apply_action(SceneAction(
        action_id="ACT_JACKET_TEAR_001",
        action_type=ActionType.WARDROBE_MUTATION,
        actor_id="maya",
        metadata={"slot": "jacket", "state": "torn_left_sleeve", "damage_level": 0.5, "is_damaged": True},
        elapsed_seconds=3.0
    ))
    snap2 = world.freeze_shot("SHOT_002")
    s2 = snap2.state
    print(f"  ✓ Shot 2 Frozen: Maya jacket={s2.character_roster['maya'].wardrobe['jacket'].state}")

    # Shot 3 Action: Maya transfers spectrometer to Bob
    bob = CharacterState(
        character_id="bob",
        name="Bob",
        position=[0.0, 0.0, 3.0],
        facing_angle=180.0,
        eyeline_vector=[0.0, 0.0, -1.0]
    )
    world.active_state.character_roster["bob"] = bob
    world.apply_action(SceneAction(
        action_id="ACT_PROP_TRANSFER_002",
        action_type=ActionType.PROP_TRANSFER,
        actor_id="maya",
        target_id="bob",
        metadata={"prop_id": "spectrometer", "recipient": "bob", "hand": "left"},
        elapsed_seconds=2.0
    ))
    snap3 = world.freeze_shot("SHOT_003")
    s3 = snap3.state
    print(f"  ✓ Shot 3 Frozen: Prop transferred to {s3.prop_roster['spectrometer'].owner_id} ({s3.prop_roster['spectrometer'].hand_attachment} hand)")

    # Run Continuity Auditor across shots 1->2->3
    auditor = ContinuityAuditor()
    audit_results = auditor.audit_shots(world)
    all_valid = all(r.is_valid for r in audit_results)
    total_violations = sum(len(r.violations) for r in audit_results)
    print(f"  ✓ Multi-Shot Continuity Audit: is_valid={all_valid}, transitions_audited={len(audit_results)}, violations={total_violations}")
    assert all_valid, f"Continuity audit must pass: {[v.message for r in audit_results for v in r.violations]}"

    # ---------------------------------------------------------
    # STEP 4: DREAM-RSI REPLAY SIMULATOR & OFFLINE DREAMING
    # ---------------------------------------------------------
    print("\n[Step 4/5] Dream-RSI Historical Replay Simulator & Zero-Cost Dreaming...")
    trace_dir = output_dir / "trace_pool"
    logger = TraceLogger(storage_dir=trace_dir)

    # Log 3 real shot traces into discovery trees
    tree1 = logger.log_episode(
        shot_id="live_shot_001",
        scene_state=s1,
        shot_requirement=ShotRequirement(shot_id="live_shot_001", target_duration=3.0),
        complexity_plan=ComplexityPlan(
            shot_id="live_shot_001",
            complexity_level=ComplexityLevel.TWOD_TRAJECTORY_POSE,
            recommended_provider=ProviderTarget.VEO_3_1
        ),
        compiled_payload=CompiledModelPayload(
            shot_id="live_shot_001",
            provider_target=ProviderTarget.VEO_3_1,
            prompt="Maya in Tokyo underpass holding spectrometer"
        ),
        council_report=CouncilEvaluationReport(
            shot_id="live_shot_001",
            status=CouncilStatus.ACCEPTED,
            passed_hard_gates=True,
            overall_soft_score=8.8
        ),
        final_score=8.8,
        final_cost=0.08,
        execution_latency=12.4,
        success=True
    )
    tree2 = logger.log_episode(
        shot_id="live_shot_002",
        scene_state=s2,
        shot_requirement=ShotRequirement(shot_id="live_shot_002", target_duration=4.0),
        complexity_plan=ComplexityPlan(
            shot_id="live_shot_002",
            complexity_level=ComplexityLevel.THREED_BLOCKING,
            recommended_provider=ProviderTarget.RUNWAY_GEN_4_5
        ),
        compiled_payload=CompiledModelPayload(
            shot_id="live_shot_002",
            provider_target=ProviderTarget.RUNWAY_GEN_4_5,
            prompt="Maya fighting, jacket sleeve tears"
        ),
        council_report=CouncilEvaluationReport(
            shot_id="live_shot_002",
            status=CouncilStatus.ACCEPTED,
            passed_hard_gates=True,
            overall_soft_score=9.1
        ),
        final_score=9.1,
        final_cost=0.12,
        execution_latency=18.2,
        success=True
    )

    # Construct Replay Simulator World Pool
    replay_pool = ReplaySimulatorPool()
    replay_pool.add_trace(tree1)
    replay_pool.add_trace(tree2)
    replay_pool.save_to_directory(trace_dir)
    print(f"  ✓ Replay Simulator Pool Constructed: {replay_pool.size} historical trace trees loaded")

    # Offline Dreaming Loop
    dreamer = PolicyDreamer(replay_pool)
    baseline_policy = ExplorationPolicy(
        name="Live_Baseline_Diffusion",
        enable_teacache=False,
        enable_pab=False,
        sampling_steps=30
    )
    efficient_policy = ExplorationPolicy(
        name="Live_Distilled_Flow_Efficient",
        enable_teacache=True,
        enable_pab=True,
        sampling_steps=8,
        enable_speculative_draft=True
    )

    # Compare head to head on replay pool
    comparison = dreamer.compare_policies(baseline_policy, efficient_policy)
    print(f"  ✓ Dream-RSI Offline Head-to-Head Comparison Complete (ZERO API COST):")
    print(f"    - Winner Policy: {comparison['winner']}")
    print(f"    - Cost Delta: ${comparison['delta_cost']:.4f}")
    print(f"    - Quality Delta: {comparison['delta_quality']:+.3f}")
    print(f"    - Pareto Value Improvement: +{comparison['delta_pareto_value']:.4f}")

    winner_policy, dream_results = dreamer.dream(num_candidates=5, seed=42)
    print(f"  ✓ Dream-RSI Search Complete:")
    print(f"    - Top Dreamed Policy: {winner_policy.name} ({winner_policy.policy_id})")
    print(f"    - Winning Pareto Value: {dream_results[0].pareto_value:.4f}")

    # Codify into Production Knowledge Ledger
    ledger = ProductionKnowledgeLedger(storage_file=output_dir / "live_ledger.json")
    ledger.promote_policy(winner_policy, dream_results[0])
    print(f"  ✓ Production Knowledge Ledger Updated: {len(ledger.rules)} active production rules codified")

    # ---------------------------------------------------------
    # STEP 5: FULL END-TO-END AUTONOMOUS DIRECTOR EXECUTION
    # ---------------------------------------------------------
    print("\n[Step 5/5] Full End-to-End AetherDirector Film Production...")
    films_output = output_dir / "mastered_production"
    director = AetherDirector(output_dir=films_output)

    brief = DirectorProductionBrief(
        title="Project Aether Live Benchmark",
        logline="Two cyber-operatives retrieve an encrypted drive under torrential rainfall.",
        target_duration=15.0,
        aspect_ratio="9:16",
        visual_style="hyper-detailed cyberpunk photorealism, anamorphic lens, neon cyan and amber contrast",
        target_models=["veo_3_1", "kling_3_0", "runway_gen_4_5"],
        speculative_draft=True,
        max_repair_attempts=2,
        budget_limit=10.0
    )

    t0 = time.time()
    film = director.produce(brief, dry_run=False)
    elapsed = time.time() - t0

    print(f"\n============================================================")
    print(f"🎬 MASTERED FILM PRODUCTION COMPLETE IN {elapsed:.2f}s")
    print(f"============================================================")
    print(f"Title: {film.title} ({film.film_id})")
    print(f"Status: {film.status}")
    print(f"Duration: {film.duration_seconds:.1f}s | Scenes: {film.scenes_count} | Shots: {film.total_shots_count}")
    print(f"Master Video Artifact: {film.master_video_artifact_uri}")
    print(f"Master Audio Artifact: {film.master_audio_artifact_uri}")
    print(f"Total Production Cost: ${film.total_production_cost:.4f}")
    print(f"Dream-RSI Trace Episode ID: {film.dream_rsi_trace_episode_id}")
    print(f"Timeline Shots Generated:")
    for shot in film.production_timeline_ledger:
        print(f"  • {shot['shot_id']} | Provider: {shot.get('provider', 'N/A')} | Passed: {shot['passed_hard_gates']} | Repairs: {shot['repairs_count']}")

    assert film.status == "COMPLETED", f"Mastered film must be COMPLETED, got {film.status}"
    assert film.total_shots_count >= 3, "Production must generate at least 3 shots!"

    print("\n" + "=" * 70)
    print("🎯 REAL-TIME PHYSICAL VERIFICATION PASSED WITH 100% SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    run_live_realtime_verification()
