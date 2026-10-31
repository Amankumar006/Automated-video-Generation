import time
from pathlib import Path

from PIL import Image

from pipeline.vlm_critic import VLMCritic


def test_vlm_batch_timeout_fails_closed(monkeypatch, tmp_path: Path):
    """A stalled provider must stop the batch and fail the production gate."""
    frames = tmp_path / "frames"
    frames.mkdir()
    for beat_id in range(1, 4):
        Image.new("RGB", (32, 64), color=(10, 13, 20)).save(frames / f"beat_{beat_id:02d}.png")

    monkeypatch.setenv("VLM_CRITIC_BATCH_TIMEOUT_SECONDS", "0.01")
    critic = VLMCritic(api_key=None)

    def slow_audit(*args, **kwargs):
        time.sleep(0.02)
        return {"beat_id": kwargs.get("beat_id", 1), "overall_score": 9.0, "passed": True}

    monkeypatch.setattr(critic, "audit_keyframe", slow_audit)
    spec = {"title": "Timeout test", "beats": [{"beat_id": i} for i in range(1, 4)]}

    report = critic.audit_batch_keyframes(str(frames), spec)

    assert report["audit_timeout"] is True
    assert report["incomplete_audit"] is True
    assert report["passed_quality_gate"] is False


def test_vlm_batch_marks_provider_outage_separately(monkeypatch, tmp_path: Path):
    """A provider outage remains a failed audit but is distinguishable from bad visuals."""
    frames = tmp_path / "frames"
    frames.mkdir()
    for beat_id in range(1, 3):
        Image.new("RGB", (32, 64), color=(10, 13, 20)).save(frames / f"beat_{beat_id:02d}.png")

    critic = VLMCritic(api_key=None)
    monkeypatch.setattr(
        critic,
        "audit_keyframe",
        lambda *args, **kwargs: {
            "beat_id": kwargs.get("beat_id", 1),
            "overall_score": 6.0,
            "passed": False,
            "provider_unavailable": True,
        },
    )
    spec = {"title": "Provider outage test", "beats": [{"beat_id": i} for i in range(1, 3)]}

    report = critic.audit_batch_keyframes(str(frames), spec)

    assert report["provider_unavailable"] is True
    assert report["passed_quality_gate"] is False
