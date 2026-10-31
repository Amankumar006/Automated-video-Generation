import json

from pipeline.analytics_feedback import qualified_growth_score, smoothed_relative_weight
from pipeline.experiment_ledger import (
    budget_remaining,
    can_schedule,
    completed_count,
    load_ledger,
    record_video,
    eligible_winners,
    update_metrics,
)


def test_experiment_ledger_counts_only_public_slots(tmp_path):
    path = tmp_path / "experiment.json"
    record_video({"candidate_id": "a", "status": "produced_unpublished"}, path=path)
    record_video({"candidate_id": "b", "status": "published"}, path=path)
    ledger = load_ledger(path)
    assert completed_count(ledger) == 1
    assert budget_remaining(ledger) == 19
    assert can_schedule(ledger, requested=5)


def test_experiment_metrics_are_written_to_24h_and_72h_buckets(tmp_path):
    path = tmp_path / "experiment.json"
    record_video({"candidate_id": "a", "video_id": "yt-a", "status": "published"}, path=path)
    assert update_metrics("yt-a", {"views": 100, "hours_live": 24}, path=path)
    assert update_metrics("yt-a", {"views": 250, "hours_live": 72}, path=path)
    data = json.loads(path.read_text())
    record = data["videos"][0]
    assert record["metrics_24h"]["views"] == 100
    assert record["metrics_72h"]["views"] == 250


def test_72h_winner_gate_marks_only_public_high_quality_records(tmp_path):
    path = tmp_path / "experiment.json"
    record_video({"candidate_id": "winner", "video_id": "yt-w", "status": "published"}, path=path)
    record_video({"candidate_id": "loser", "video_id": "yt-l", "status": "published"}, path=path)
    update_metrics("yt-w", {"hours_live": 72, "qualified_growth_score": 0.8}, path=path)
    update_metrics("yt-l", {"hours_live": 72, "qualified_growth_score": 0.2}, path=path)
    winners = eligible_winners(load_ledger(path))
    assert [record["candidate_id"] for record in winners] == ["winner"]


def test_low_sample_weights_are_shrunk_and_growth_score_is_bounded():
    assert smoothed_relative_weight(200, 100, sample_count=1) == 1.33
    assert smoothed_relative_weight(200, 100, sample_count=3) == 2.0
    score = qualified_growth_score({
        "views": 1000,
        "views_per_hour": 100,
        "average_percentage_watched": 85,
        "like_ratio_pct": 8,
        "comments": 30,
        "subscribers_gained": 15,
    }, {"views_per_hour": 50})
    assert 0.0 <= score <= 1.0
