"""
The Model Verse — Legacy Spec to VSG-IR AST Converter
Transforms legacy dictionary script specs into strictly validated VSG-IR v1.0.0 AST models.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pipeline.vsg.schema import (
    VideoSceneGraphIR,
    ProjectMetadata,
    CanvasMetadata,
    AudioMetadata,
    ThemeTokens,
    THEME_CYBER_CYAN,
    THEME_NEON_VIOLET,
    THEME_SOLAR_AMBER,
    THEME_DARK_OBSIDIAN,
    BeatAST,
    TimeRange,
    NarrativeInfo,
    AcousticAnchor,
    LayoutContainer,
    VisualNode,
    NodeType,
    MotionTrack,
    EnterMotion,
    BoundingBoxPx,
    BandType,
    MotionType,
    AspectRatio
)

logger = logging.getLogger("vsg_converter")


def map_metaphor_to_node_type(metaphor: str, category: str = "") -> NodeType:
    """Heuristic mapping from visual metaphor string to high-fidelity NodeType."""
    m_lower = (metaphor or "").lower()
    c_lower = (category or "").lower()

    if any(k in m_lower for k in ["moe", "expert", "router", "gateway"]):
        return NodeType.MOE_ROUTER_MATRIX
    elif any(k in m_lower for k in ["attention", "matrix", "heatmap", "transformer"]):
        return NodeType.ATTENTION_HEATMAP
    elif any(k in m_lower for k in ["code", "kernel", "cuda", "syntax", "python"]):
        return NodeType.SYNTAX_CODE_BLOCK
    elif any(k in m_lower for k in ["race", "showdown", "benchmark", "bars", "drag", "bar_chart"]):
        return NodeType.HORIZONTAL_RACE_BARS
    elif any(k in m_lower for k in ["flow", "pipeline", "trajectory", "diagram", "split", "graph"]):
        return NodeType.VECTOR_FLOW_DIAGRAM
    elif any(k in m_lower for k in ["metric", "counter", "stat", "pill"]):
        return NodeType.METRIC_PILL
    else:
        return NodeType.GLASS_HUD_CARD


def spec_to_vsg(
    spec: Dict[str, Any],
    master_audio_path: Optional[str] = None,
    fps: int = 60
) -> VideoSceneGraphIR:
    """
    Transforms a legacy video production spec dictionary into a validated VideoSceneGraphIR AST.
    """
    project_id = str(spec.get("id", "short_proj"))
    title = str(spec.get("title", "Technical Deepdive"))
    category = str(spec.get("category", "architecture_breakdown"))
    domain_taxonomy = str(spec.get("domain_taxonomy", category))

    # Calculate total duration from beats
    raw_beats = spec.get("beats", [])
    total_duration = 0.0
    for b in raw_beats:
        end_time = float(b.get("end") or (total_duration + b.get("audio_duration", 2.0)))
        if end_time > total_duration:
            total_duration = end_time

    if total_duration <= 0.0:
        total_duration = max(len(raw_beats) * 2.5, 6.0)

    total_frames = int(round(total_duration * fps))

    # Canvas & Audio Metadata
    canvas = CanvasMetadata(
        width_px=1080,
        height_px=1920,
        fps=fps,
        duration_seconds=round(total_duration, 2),
        total_frames=total_frames
    )

    audio = AudioMetadata(
        master_voiceover_path=master_audio_path or spec.get("master_audio_path", "audio/master_voice.wav"),
        background_music_path=spec.get("background_music_path"),
        sample_rate_hz=24000,
        music_ducking_db=-18.0
    )

    project_meta = ProjectMetadata(
        project_id=project_id,
        title=title,
        domain_taxonomy=domain_taxonomy,
        aspect_ratio=AspectRatio.RATIO_9_16,
        canvas=canvas,
        audio=audio
    )

    # Theme selection based on category/domain
    if "hardware" in domain_taxonomy or "perk" in category:
        theme = THEME_SOLAR_AMBER
    elif "reason" in domain_taxonomy or "deep" in category:
        theme = THEME_NEON_VIOLET
    else:
        theme = THEME_CYBER_CYAN

    # Construct BeatAST items
    beats_ast: List[BeatAST] = []
    current_time = 0.0

    for idx, b in enumerate(raw_beats):
        b_id = int(b.get("beat_id", idx + 1))
        spoken_text = str(b.get("text", f"Beat {b_id} content."))
        duration = float(b.get("audio_duration") or b.get("slot_duration") or 2.5)

        start_sec = float(b.get("start", current_time))
        end_sec = float(b.get("end", start_sec + duration))
        if end_sec <= start_sec:
            end_sec = start_sec + 2.0

        current_time = end_sec

        start_frame = int(round(start_sec * fps))
        end_frame = int(round(end_sec * fps))
        if end_frame <= start_frame:
            end_frame = start_frame + 60

        time_range = TimeRange(
            start_sec=round(start_sec, 2),
            end_sec=round(end_sec, 2),
            start_frame=start_frame,
            end_frame=end_frame
        )

        visual_metaphor = str(
            b.get("visual_focus") or
            b.get("visual_blueprint", {}).get("layout") or
            "GlassHUDCard"
        )

        primary_node_id = f"node_b{b_id}_primary"

        narrative = NarrativeInfo(
            spoken_text=spoken_text,
            intent=str(b.get("intent") or f"Explain mechanism for Beat {b_id}"),
            visual_metaphor=visual_metaphor,
            primary_focus_node_id=primary_node_id,
            everyday_analogy=b.get("everyday_analogy")
        )

        # Acoustic anchors from word_timings if available
        anchors: List[AcousticAnchor] = []
        for wt in b.get("word_timings", []):
            w_text = wt.get("word", "").strip().upper()
            w_start = float(wt.get("start", start_sec))
            if w_text:
                anchors.append(AcousticAnchor(
                    word=w_text,
                    timestamp_sec=round(w_start, 3),
                    frame_trigger=int(round(w_start * fps))
                ))

        # Layout containers & visual nodes in Band 3 Stage
        node_type = map_metaphor_to_node_type(visual_metaphor, category)

        # Build props based on node_type
        node_props: Dict[str, Any] = {}
        if node_type == NodeType.MOE_ROUTER_MATRIX:
            node_props = {
                "tokenText": spoken_text.split()[-1] if spoken_text.split() else "token",
                "totalExperts": 256,
                "activeRouted": 8,
                "sharedExperts": 1
            }
        elif node_type == NodeType.ATTENTION_HEATMAP:
            node_props = {
                "tokens": spoken_text.split()[:5] if spoken_text.split() else ["Q", "K", "V", "Out"],
                "headCount": 8
            }
        elif node_type == NodeType.SYNTAX_CODE_BLOCK:
            node_props = {
                "filename": "kernel.cu",
                "language": "CUDA",
                "rawCode": b.get("code_snippet") or "warp_topk_gemm(tid, 256);"
            }
        elif node_type == NodeType.HORIZONTAL_RACE_BARS:
            node_props = {
                "title": f"Beat {b_id} Showdown",
                "benchmarkName": "Score",
                "items": [
                    {"name": "Frontier", "score": 92.4, "isHero": True, "pillTag": "SOTA"},
                    {"name": "Baseline", "score": 78.1}
                ]
            }
        elif node_type == NodeType.VECTOR_FLOW_DIAGRAM:
            node_props = {
                "title": visual_metaphor.replace("_", " ").title(),
                "steps": [
                    {"id": "1", "label": "Stage 1", "sublabel": "Ingestion"},
                    {"id": "2", "label": "Stage 2", "sublabel": "Kernel Compute", "isActive": True},
                    {"id": "3", "label": "Stage 3", "sublabel": "Output Dispatch"}
                ]
            }
        else:
            node_props = {
                "title": visual_metaphor.replace("_", " ").title(),
                "subtitle": b.get("intent", ""),
                "bodyText": " ".join(spoken_text.split()[:12]),
                "badge": category.upper()
            }

        primary_node = VisualNode(
            id=primary_node_id,
            node_type=node_type,
            props=node_props,
            bounds=BoundingBoxPx(
                x_min_px=140,
                y_min_px=500,
                width_px=760,
                height_px=650
            ),
            motion_track=MotionTrack(
                enter=EnterMotion(
                    type=MotionType.SPRING_DAMPED,
                    start_frame=start_frame,
                    duration_frames=30
                )
            )
        )

        stage_container = LayoutContainer(
            container_id=f"c_stage_b{b_id}",
            band=BandType.BAND_3_STAGE,
            bounds=BoundingBoxPx(
                x_min_px=140,
                y_min_px=480,
                width_px=760,
                height_px=700
            ),
            nodes=[primary_node]
        )

        beat_ast = BeatAST(
            beat_id=b_id,
            time_range=time_range,
            narrative=narrative,
            acoustic_anchors=anchors,
            layout_containers=[stage_container]
        )
        beats_ast.append(beat_ast)

    vsg = VideoSceneGraphIR(
        version="1.0.0",
        metadata=project_meta,
        theme=theme,
        beats=beats_ast
    )
    return vsg
