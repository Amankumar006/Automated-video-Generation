"""
Archived tests for Project Aether adapter and multi-engine bridge.
"""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
ARCHIVE_ROOT = PROJECT_ROOT / "_archive"
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))

from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ShotRequirement,
)
from aether.director.orchestrator import AetherDirector
from aether.director.schemas import (
    DirectorProductionBrief,
    FilmScene,
    ProductionState,
)
from aether.shared_contract import (
    DualEnginePipelineConfig,
    EducationalAssetConditioningPackage,
    EducationalAssetRole,
    HybridRenderMode,
    ScriptToFilmSceneAdapter,
)
from pipeline.arxiv_vector_extractor import extract_paper_figures


@pytest.fixture(scope="session")
def real_arxiv_id() -> str:
    return "2407.08608"


@pytest.fixture
def mock_base_6beat_spec() -> Dict[str, Any]:
    return {
        "id": "flashattention_3_architecture",
        "title": "FlashAttention-3: Asynchronous Hardware GEMM",
        "category": "architecture_breakdown",
        "hook_tag": "BREAKTHROUGH HARDWARE ATTENTION",
        "arxiv_id": "2407.08608",
        "beats": [
            {
                "beat_id": 1,
                "text": "GPUs spend forty percent of their cycles waiting for memory transfers.",
                "visual_focus": "Hardware stall heat map showing idle tensor cores",
                "camera_action": "zoom_in",
                "expected_duration": 4.5,
            },
            {
                "beat_id": 2,
                "text": "The memory wall forces compute units to idle between layer activations.",
                "visual_focus": "Memory bandwidth bottleneck illustration",
                "camera_action": "pan_left",
                "expected_duration": 5.0,
            },
            {
                "beat_id": 3,
                "text": "FlashAttention-3 introduces hardware-asynchronous tile scheduling directly on Hopper.",
                "visual_focus": "FlashAttention-3 asynchronous ping-pong architecture diagram",
                "camera_action": "dolly_in",
                "expected_duration": 6.5,
            },
            {
                "beat_id": 4,
                "text": "Here is the exact TMA warpgroup cooperative pipelining kernel.",
                "visual_focus": "Hopper async copy code snippet",
                "camera_action": "static",
                "expected_duration": 5.0,
            },
            {
                "beat_id": 5,
                "text": "Throughput leaps from six hundred to nearly twelve hundred TFLOPS.",
                "visual_focus": "Radar comparison showing 1.8x speedup against FA2 and cuDNN",
                "camera_action": "zoom_out",
                "expected_duration": 5.5,
            },
            {
                "beat_id": 6,
                "text": "Hardware-native attention fundamentally rewrites LLM inference efficiency.",
                "visual_focus": "Summary card with call to action",
                "camera_action": "static",
                "expected_duration": 4.0,
            },
        ],
    }


def test_tier1_aether_adapter_spec_to_brief_conversion(mock_base_6beat_spec: Dict[str, Any]):
    brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(
        spec=mock_base_6beat_spec,
        visual_style="dark cinematic tech documentary",
        target_models=["veo_3_1", "kling_3_0"],
    )

    assert isinstance(brief, DirectorProductionBrief)
    assert brief.title == mock_base_6beat_spec["title"]
    assert brief.aspect_ratio == "9:16"
    assert len(brief.scenes) == 6

    scene_ids = [s.scene_id for s in brief.scenes]
    assert scene_ids == [
        "SC_001_HOOK",
        "SC_002_BOTTLENECK",
        "SC_003_MECHANISM",
        "SC_004_CODE",
        "SC_005_SHOWDOWN",
        "SC_006_OUTRO",
    ]

    expected_dur = sum(b["expected_duration"] for b in mock_base_6beat_spec["beats"])
    assert brief.target_duration == pytest.approx(expected_dur, abs=0.1)


def test_tier2_conditioning_package_bounds_validation():
    with pytest.raises(ValueError, match="must contain exactly 4 floats"):
        EducationalAssetConditioningPackage(
            asset_id="test_bad_len",
            file_uri="figure.png",
            spatial_bounds=[0.1, 0.2, 0.3],
        )

    with pytest.raises(ValueError, match="coordinates must be in"):
        EducationalAssetConditioningPackage(
            asset_id="test_bad_coord",
            file_uri="figure.png",
            spatial_bounds=[-0.1, 0.2, 0.8, 0.9],
        )

    pkg = EducationalAssetConditioningPackage(
        asset_id="test_legal",
        file_uri="figure.png",
        spatial_bounds=[0.1, 0.2, 0.8, 0.9],
    )
    assert pkg.spatial_bounds == [0.1, 0.2, 0.8, 0.9]


def test_tier3_aether_conditioning_package_bundling_paper_figures(
    real_arxiv_id: str,
    mock_base_6beat_spec: Dict[str, Any],
):
    figs = extract_paper_figures(real_arxiv_id, max_figures=2)
    assert len(figs) >= 1

    spec = copy.deepcopy(mock_base_6beat_spec)
    spec["paper_figures"] = figs

    packages = ScriptToFilmSceneAdapter.extract_conditioning_assets(spec)
    assert len(packages) >= 1

    primary_pkg = packages[0]
    assert primary_pkg.source_beat_id == 3
    assert primary_pkg.role == EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE
    assert primary_pkg.file_uri

    brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(
        spec=spec,
        conditioning_assets=packages,
    )

    beat_3_scene = next(s for s in brief.scenes if s.scene_id == "SC_003_MECHANISM")
    shot_req = beat_3_scene.shot_list_requirements[0]

    assert shot_req.first_frame_uri == primary_pkg.file_uri
    assert shot_req.metadata.get("reference_image_uri") == primary_pkg.file_uri
    assert shot_req.metadata.get("conditioning_asset_id") == primary_pkg.asset_id


def test_tier3_dual_engine_pipeline_config_beat_allocation():
    cfg = DualEnginePipelineConfig(
        default_mode=HybridRenderMode.PURE_AETHER_3D,
        beat_modes={
            1: HybridRenderMode.PURE_AETHER_3D,
            3: HybridRenderMode.PURE_MANIM_2D,
            4: HybridRenderMode.HYBRID_COMPOSITE,
            5: HybridRenderMode.DUAL_STREAM_PIP,
        },
    )

    assert cfg.get_beat_mode(1) == HybridRenderMode.PURE_AETHER_3D
    assert cfg.get_beat_mode(2) == HybridRenderMode.PURE_AETHER_3D
    assert cfg.get_beat_mode(3) == HybridRenderMode.PURE_MANIM_2D
    assert cfg.get_beat_mode(4) == HybridRenderMode.HYBRID_COMPOSITE
    assert cfg.get_beat_mode(5) == HybridRenderMode.DUAL_STREAM_PIP
    assert cfg.is_hybrid() is True


def test_tier3_brief_to_spec_outline_round_trip(mock_base_6beat_spec: Dict[str, Any]):
    brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(mock_base_6beat_spec)
    outline = ScriptToFilmSceneAdapter.convert_brief_to_spec_outline(brief)

    assert outline["title"] == mock_base_6beat_spec["title"]
    assert len(outline["beats"]) == len(mock_base_6beat_spec["beats"])
    for i, b in enumerate(outline["beats"]):
        orig = mock_base_6beat_spec["beats"][i]
        assert b["beat_id"] == orig["beat_id"]
        assert b["expected_duration"] == pytest.approx(orig["expected_duration"])


def test_tier4_aether_director_consumes_adapted_brief_dry_run(
    mock_base_6beat_spec: Dict[str, Any],
    real_arxiv_id: str,
):
    figs = extract_paper_figures(real_arxiv_id, max_figures=2)
    spec = copy.deepcopy(mock_base_6beat_spec)
    spec["paper_figures"] = figs

    brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(
        spec=spec,
        visual_style="hyperrealistic technical cinematography",
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        director = AetherDirector(output_dir=Path(tmp_dir))
        film = director.produce(brief, dry_run=True)

        assert film is not None
        assert film.title == brief.title
        assert film.total_shots_count == 6
        assert director.status.state == ProductionState.COMPLETED
        assert director.status.shots_passed_count == 6
