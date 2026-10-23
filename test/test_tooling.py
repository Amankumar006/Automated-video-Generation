from __future__ import annotations

from pathlib import Path

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
