"""Persistent state for the audience-led 20-video YouTube experiment.

The ledger is deliberately small and JSON-based so the scheduled workflow can
carry it between runs as a normal repository artifact.  It stores editorial
evidence separately from platform metrics and never treats a failed render or
upload as a completed public experiment slot.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER_PATH = PROJECT_ROOT / "public" / "audience_experiment_ledger.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "public" / "audience_experiment_report.json"
EXPERIMENT_VERSION = "audience-led-experiment-v1"
INITIAL_FORMAT_TARGETS = {
    "practical_demo": 8,
    "comparison": 5,
    "current_release": 4,
    "mechanism": 3,
}


def experiment_config() -> Dict[str, Any]:
    """Read experiment configuration with safe, deterministic defaults."""
    return {
        "experiment_id": os.getenv("EXPERIMENT_ID", "global_builder_20_video"),
        "target_videos": int(os.getenv("EXPERIMENT_TARGET_VIDEOS", "20")),
        "videos_per_week": int(os.getenv("EXPERIMENT_VIDEOS_PER_WEEK", "5")),
        "primary_platform": os.getenv("EXPERIMENT_PRIMARY_PLATFORM", "youtube"),
        "audience_profile": os.getenv("AUDIENCE_PROFILE", "global_ai_builder"),
        "success_metric": os.getenv("EXPERIMENT_SUCCESS_METRIC", "qualified_growth"),
        "crosspost_policy": os.getenv("EXPERIMENT_CROSSPOST_POLICY", "winners_only"),
    }


def _empty_ledger() -> Dict[str, Any]:
    return {
        "version": EXPERIMENT_VERSION,
        "config": experiment_config(),
        "videos": [],
        "updated_at": None,
    }


def load_ledger(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the ledger, tolerating a missing or partially written file."""
    ledger_path = Path(path or DEFAULT_LEDGER_PATH)
    if not ledger_path.exists():
        return _empty_ledger()
    try:
        with ledger_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return _empty_ledger()
    except (OSError, ValueError, TypeError):
        return _empty_ledger()

    defaults = _empty_ledger()
    defaults.update(data)
    defaults["config"] = {**experiment_config(), **(data.get("config") or {})}
    defaults["videos"] = data.get("videos") if isinstance(data.get("videos"), list) else []
    return defaults


def save_ledger(ledger: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """Atomically persist a ledger and return its path."""
    ledger_path = Path(path or DEFAULT_LEDGER_PATH)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(ledger)
    payload["version"] = EXPERIMENT_VERSION
    payload["config"] = {**experiment_config(), **(payload.get("config") or {})}
    payload["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    temporary_path = ledger_path.with_suffix(ledger_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary_path.replace(ledger_path)
    return ledger_path


def completed_count(ledger: Dict[str, Any]) -> int:
    """Count only records that represent a successful public experiment slot."""
    return sum(
        1 for record in ledger.get("videos", [])
        if record.get("status") == "published"
    )


def budget_remaining(ledger: Dict[str, Any]) -> int:
    target = int((ledger.get("config") or {}).get("target_videos", 20))
    return max(0, target - completed_count(ledger))


def can_schedule(ledger: Dict[str, Any], requested: int = 1) -> bool:
    """Return whether a run can reserve the requested number of experiment slots."""
    return requested > 0 and budget_remaining(ledger) >= requested


def _record_key(record: Dict[str, Any]) -> str:
    return str(record.get("candidate_id") or record.get("video_id") or record.get("title") or "")


def record_video(
    record: Dict[str, Any],
    *,
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Insert or update one experiment record without double-counting retries."""
    ledger = load_ledger(path)
    incoming = dict(record)
    incoming.setdefault("status", "selected")
    incoming.setdefault("created_at", dt.datetime.now(dt.timezone.utc).isoformat())
    key = _record_key(incoming)
    records: List[Dict[str, Any]] = ledger.setdefault("videos", [])
    for index, existing in enumerate(records):
        if key and _record_key(existing) == key:
            merged = {**existing, **incoming}
            records[index] = merged
            break
    else:
        records.append(incoming)
    save_ledger(ledger, path)
    save_report(ledger, path=Path(path) if path else None)
    return incoming


def update_metrics(
    video_id: str,
    metrics: Dict[str, Any],
    *,
    observed_at: Optional[str] = None,
    path: Optional[Path] = None,
) -> bool:
    """Attach 24-hour/72-hour metrics to a known video record."""
    ledger = load_ledger(path)
    for record in ledger.get("videos", []):
        if str(record.get("video_id")) != str(video_id):
            continue
        timestamp = observed_at or dt.datetime.now(dt.timezone.utc).isoformat()
        age_hours = metrics.get("hours_live")
        bucket = "metrics_24h" if age_hours is not None and float(age_hours) <= 48 else "metrics_72h"
        record[bucket] = {**(record.get(bucket) or {}), **metrics, "observed_at": timestamp}
        if metrics.get("qualified_growth_score") is not None:
            record["qualified_growth_score"] = metrics["qualified_growth_score"]
        if bucket == "metrics_72h":
            record["crosspost_eligible"] = (
                record.get("status") == "published"
                and float(metrics.get("qualified_growth_score") or record.get("qualified_growth_score") or 0) >= 0.65
            )
        save_ledger(ledger, path)
        save_report(ledger, path=Path(path) if path else None)
        return True
    return False


def eligible_winners(ledger: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Return public videos that passed the 72-hour winner gate."""
    current = ledger or load_ledger()
    return [
        record for record in current.get("videos", [])
        if record.get("status") == "published"
        and record.get("metrics_72h")
        and record.get("crosspost_eligible") is True
    ]


def report(ledger: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a compact experiment status report for dry-runs and CI logs."""
    current = ledger or load_ledger()
    records = current.get("videos", [])
    winners = [r for r in records if float(r.get("qualified_growth_score") or 0) >= 0.65]
    failures = [r for r in records if r.get("status") in {"failed", "rejected"}]
    losers = [r for r in records if r in failures or (r.get("qualified_growth_score") is not None and float(r.get("qualified_growth_score") or 0) < 0.35)]
    format_mix = {name: 0 for name in INITIAL_FORMAT_TARGETS}
    for record in records:
        selected_format = record.get("selected_format")
        if selected_format in format_mix:
            format_mix[selected_format] += 1
    return {
        "experiment_id": (current.get("config") or {}).get("experiment_id"),
        "target_videos": (current.get("config") or {}).get("target_videos", 20),
        "completed_videos": completed_count(current),
        "budget_remaining": budget_remaining(current),
        "selected_records": len(records),
        "winner_count": len(winners),
        "crosspost_ready_count": len(eligible_winners(current)),
        "failure_count": len(failures),
        "winners": [r.get("title") for r in winners[-5:]],
        "losers": [r.get("title") for r in losers[-5:]],
        "format_mix": format_mix,
        "format_targets": INITIAL_FORMAT_TARGETS,
        "recommended_next_formats": [
            name for name, target in sorted(INITIAL_FORMAT_TARGETS.items(), key=lambda item: format_mix[item[0]] / max(item[1], 1))
            if format_mix[name] < target
        ],
    }


def save_report(ledger: Optional[Dict[str, Any]] = None, *, path: Optional[Path] = None) -> Path:
    """Persist the compact experiment dashboard beside the detailed ledger."""
    current = ledger or load_ledger()
    report_path = Path(path).with_name("audience_experiment_report.json") if path else DEFAULT_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report(current), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report_path
