"""
Archived tests for Project Aether Ollama Cloud Integration.
"""

from unittest.mock import MagicMock
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
ARCHIVE_ROOT = PROJECT_ROOT / "_archive"
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.schemas import ComplexityLevel, ComplexityPlan, ShotRequirement
from aether.director.orchestrator import AetherDirector, generate_production_brief
from aether.director.schemas import DirectorProductionBrief, FilmScene
from aether.state.schemas import SceneState
from pipeline.ollama_client import OllamaResponse


def test_complexity_planner_evaluate_with_llm_mocked():
    planner = ComplexityPlanner()
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "complexity_level": 4,
            "rationale": ["Multi-character handoff", "Complex camera path"],
            "recommended_representations": ["previs_3d", "depth_map"],
            "recommended_provider": "kling_3_0",
        },
        model="gpt-oss:120b:cloud",
    )

    state = SceneState(scene_id="SC_001", location="stage")
    req = ShotRequirement(shot_id="SHOT_001", target_duration=5.0)

    plan = planner.evaluate_with_llm(
        scene_state=state,
        shot_requirement=req,
        client=mock_client,
    )

    assert plan.complexity_level == ComplexityLevel.THREED_BLOCKING
    assert "Multi-character handoff" in plan.rationale[0]
    assert plan.recommended_provider.value == "kling_3_0"


def test_aether_director_decompose_narrative_with_llm_mocked():
    director = AetherDirector()
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "scenes": [
                {
                    "scene_id": "SC_001",
                    "narrative_beat": "Establishing high tension in server room",
                    "location": "server_room",
                    "shot_list_requirements": [
                        {"shot_id": "SHOT_001", "target_duration": 4.0, "camera_movement": "dolly_in"},
                        {"shot_id": "SHOT_002", "target_duration": 6.0, "camera_movement": "pan_right"},
                    ],
                }
            ]
        },
        model="gpt-oss:120b:cloud",
    )

    brief = DirectorProductionBrief(
        title="Silicon Breach",
        logline="A rogue agent infiltrates an H100 GPU cluster.",
        target_duration=10.0,
    )

    scenes = director.decompose_narrative_with_llm(brief, client=mock_client)
    assert len(scenes) == 1
    assert scenes[0].scene_id == "SC_001"
    assert len(scenes[0].shot_list_requirements) == 2


def test_generate_production_brief_with_llm_mocked():
    mock_client = MagicMock()
    mock_client.generate_completion.return_value = OllamaResponse(
        data={
            "title": "Quantum Odyssey",
            "logline": "Scientists discover an anomaly in superconducting qubits.",
            "target_duration": 45.0,
            "aspect_ratio": "16:9",
            "visual_style": "cyberpunk noir",
            "target_models": ["veo_3_1"],
            "speculative_draft": True,
            "budget_limit": 50.0,
        },
        model="gpt-oss:120b:cloud",
    )

    brief = generate_production_brief(
        premise="Scientists discover an anomaly in superconducting qubits.",
        target_duration=45.0,
        aspect_ratio="16:9",
        client=mock_client,
    )

    assert brief.title == "Quantum Odyssey"
    assert brief.aspect_ratio == "16:9"
    assert brief.target_duration == 45.0
    assert brief.budget_limit == 50.0
