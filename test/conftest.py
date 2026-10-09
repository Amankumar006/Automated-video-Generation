"""Global test configuration and fixtures for The Model Verse pipeline tests."""

import pytest
from pipeline.quota_tracker import quota_tracker


@pytest.fixture(autouse=True)
def reset_global_quota_tracker():
    """Guarantees pristine QuotaHealthTracker state across all tests in the session."""
    quota_tracker.reset()
    yield
    quota_tracker.reset()
