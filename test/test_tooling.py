from __future__ import annotations

from pathlib import Path
import json

from scripts.clean_generated import discover_generated_paths, move_to_quarantine
from scripts.doctor import check_repository


def test_generated_discovery_is_scoped_to_known_artifacts(tmp_path: Path) -> None:
    (tmp_path / "frames_old").mkdir()
    (tmp_path / "frames_old" / "frame.png").write_bytes(b"frame")
    (tmp_path / "final_demo.mp4").write_bytes(b"video")
    (tmp_path / "pipeline").mkdir()
    (tmp_path / "pipeline" / "important.py").write_text("print('keep')\n")
    (tmp_path / "README.md").write_text("keep\n")

    discovered = discover_generated_paths(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in discovered] == [
        "final_demo.mp4",
        "frames_old",
    ]


def test_quarantine_move_preserves_relative_paths_and_sources(tmp_path: Path) -> None:
    generated = tmp_path / "public" / "audio_cache"
    generated.mkdir(parents=True)
    (generated / "clip.wav").write_bytes(b"audio")
    source = tmp_path / "pipeline" / "keep.py"
    source.parent.mkdir()
    source.write_text("important\n")
    quarantine = tmp_path.parent / f"{tmp_path.name}-quarantine"

    paths = discover_generated_paths(tmp_path)
    moved = move_to_quarantine(tmp_path, paths, quarantine)

    assert not generated.exists()
    assert (quarantine / "public" / "audio_cache" / "clip.wav").read_bytes() == b"audio"
    assert source.read_text() == "important\n"
    assert moved == [quarantine / "public" / "audio_cache"]


def test_doctor_repository_checks_are_safe_without_reading_env_values(tmp_path: Path) -> None:
    for filename in ("requirements.txt", "package.json", "package-lock.json", "pytest.ini", ".env.example"):
        (tmp_path / filename).write_text("placeholder\n")
    (tmp_path / "public").mkdir()
    (tmp_path / ".env").write_text("TOKEN=must-not-be-printed\n")

    checks = {check.name: check for check in check_repository(tmp_path)}

    assert checks["file:.env.example"].ok
    assert checks[".env"].ok
    assert "must-not-be-printed" not in checks[".env"].detail


def test_pipeline_dry_run_does_not_modify_repository_outputs(monkeypatch, tmp_path: Path) -> None:
    from pipeline.run_pipeline import main as run_pipeline_main

    spec = {
        "id": "tooling_dry_run_isolation",
        "title": "Dry Run Isolation",
        "category": "mechanism_deepdive",
        "beats": [{"beat_id": 1, "text": "A signal moves.", "duration": 1.0}],
    }
    template = tmp_path / "source_template.json"
    original_template = json.dumps(spec, indent=2)
    template.write_text(original_template, encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["run_pipeline.py", "--topic", "tooling_dry_run_isolation", "--dry-run"],
    )
    monkeypatch.setattr("pipeline.run_pipeline.load_template", lambda _topic: (spec, template))
    monkeypatch.setattr(
        "pipeline.run_pipeline.synthesize_audio_for_spec",
        lambda *args, **kwargs: {
            "master_audio": str(tmp_path / "mock.wav"),
            "timing_data": [
                {
                    "beat_id": 1,
                    "duration": 1.0,
                    "slot_duration": 1.0,
                    "start": 0.0,
                    "end": 1.0,
                    "word_timings": [],
                }
            ],
        },
    )
    monkeypatch.setattr(
        "pipeline.bespoke_visual_synthesizer.bespoke_synthesizer.synthesize_visual_for_beat",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "pipeline.vlm_critic.vlm_critic.audit_batch_keyframes",
        lambda *args, **kwargs: {
            "passed_quality_gate": True,
            "average_score": 9.0,
            "unique_layouts_count": 1,
        },
    )

    run_pipeline_main()

    assert template.read_text(encoding="utf-8") == original_template
    assert not (Path.cwd() / "frames_tooling_dry_run_isolation").exists()
    assert not (Path.cwd() / "public" / "tooling_dry_run_isolation_master_audio.wav").exists()


def test_arxiv_read_only_fetch_does_not_write_metadata_cache(monkeypatch, tmp_path: Path) -> None:
    import pipeline.arxiv_fetcher as arxiv_fetcher

    monkeypatch.setattr(arxiv_fetcher, "CACHE_BASE_DIR", tmp_path)
    metadata = {
        "arxiv_id": "2601.12345",
        "title": "Read Only Cache Test",
        "abstract": "A test abstract.",
        "published": "2026-01-01",
    }
    monkeypatch.setattr(arxiv_fetcher, "_fetch_from_local_cache", lambda _paper_id: None)
    monkeypatch.setattr(arxiv_fetcher, "_fetch_from_huggingface", lambda _paper_id: metadata)

    result = arxiv_fetcher.fetch_arxiv_paper(
        "2601.12345",
        extract_figures=False,
        write_cache=False,
    )

    assert result["title"] == "Read Only Cache Test"
    assert not list(tmp_path.rglob("*"))


def test_script_finalization_can_be_read_only(tmp_path: Path) -> None:
    from pipeline.script_generator import _persist_and_finalize_spec

    spec = {
        "id": "read_only_script",
        "category": "mechanism_deepdive",
        "math_formulas": [{"beat_id": 1, "latex": r"$x^2$"}],
    }

    result = _persist_and_finalize_spec(
        spec,
        "Read Only Script",
        "mechanism_deepdive",
        persist=False,
        output_root=tmp_path,
    )

    assert result["math_formulas"][0]["filename"] == "read_only_script_beat1_formula.svg"
    assert not list(tmp_path.rglob("*"))
