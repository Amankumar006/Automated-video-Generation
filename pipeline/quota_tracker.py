"""
The Model Verse — Autonomous Quota Health Tracker
Tracks provider health state in-memory during execution runs.
Once a provider fails with quota exhaustion (429, ResourceExhausted, quota_exceeded, 402, 401),
subsequent calls in the same run immediately skip the exhausted provider and use the active fallback
without repetitive timeouts.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Any, Dict, Optional, Union

logger = logging.getLogger("quota_tracker")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [QuotaTracker] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


QUOTA_ERROR_PATTERNS = [
    r"resource.*exhausted",
    r"quota.*exceed",
    r"exceed.*quota",
    r"over.*quota",
    r"out.*of.*quota",
    r"quota.*(limit|reached|ceiling)",
    r"too.*many.*requests",
    r"toomanyrequests",
    r"\b429\b",
    r"\b402\b",
    r"\b401\b",
    r"rate.*limit",
    r"credit.*limit",
    r"insufficient.*quota",
    r"insufficient.*credit",
    r"insufficient.*fund",
    r"billing.*not.*active",
    r"billing.*disabled",
    r"billing.*limit",
    r"out.*of.*credit",
    r"credit.*exhausted",
    r"payment.*required",
    r"usage.*limit",
    r"daily.*limit",
    r"monthly.*limit",
    r"limit.*reached",
    r"limit.*exceeded",
    r"capacity.*exceeded",
    r"model.*overloaded",
    r"tokens.*per.*minute",
    r"requests.*per.*minute",
    r"unauthorized",
]


def is_quota_error(exc_or_msg: Union[Exception, str, int, None]) -> bool:
    """
    Determines if an exception, HTTP status code, or error string indicates quota or rate limit exhaustion.
    """
    if exc_or_msg is None:
        return False

    if isinstance(exc_or_msg, int):
        return exc_or_msg in (429, 402, 401)

    # Check exception class name and status attributes
    if isinstance(exc_or_msg, BaseException):
        cls_name = type(exc_or_msg).__name__.lower()
        if any(term in cls_name for term in (
            "resourceexhausted",
            "ratelimit",
            "quotaexceeded",
            "toomanyrequests",
            "overquota",
            "insufficientquota",
            "quotaerror",
            "paymentrequired",
            "budgetexceeded",
            "creditsexhausted",
            "insufficientcredits",
        )):
            return True
        code = getattr(exc_or_msg, "status_code", getattr(exc_or_msg, "code", None))
        if callable(code):
            try:
                code = code()
            except Exception:
                code = None
        if isinstance(code, int) and code in (429, 402, 401):
            return True
        if hasattr(code, "value") and isinstance(code.value, int) and code.value in (429, 402, 401):
            return True
        if hasattr(code, "name") and ("RESOURCE_EXHAUSTED" in str(code.name) or "UNAUTHENTICATED" in str(code.name)):
            return True

        # Check requests.exceptions.HTTPError (response.status_code)
        resp_obj = getattr(exc_or_msg, "response", None)
        if resp_obj is not None:
            resp_status = getattr(resp_obj, "status_code", None)
            if isinstance(resp_status, int) and resp_status in (429, 402, 401):
                return True
            resp_text = getattr(resp_obj, "text", "")
            if resp_text and is_quota_error(resp_text):
                return True

    msg = str(exc_or_msg).lower()

    # Check status code patterns in string representations
    for status_str in ("429", "402", "401"):
        if (
            f"status {status_str}" in msg
            or f"status: {status_str}" in msg
            or f"code {status_str}" in msg
            or f"({status_str})" in msg
            or f"http {status_str}" in msg
            or f"error {status_str}" in msg
            or re.search(rf"\b{status_str}\b", msg)
        ):
            return True

    for pattern in QUOTA_ERROR_PATTERNS:
        if re.search(pattern, msg):
            return True

    return False


class QuotaHealthTracker:
    """
    In-memory registry tracking the health and quota exhaustion state of external API providers.
    Prevents repeated network calls to services that have already failed with quota exhaustion.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._providers: Dict[str, Dict[str, Any]] = {}

    def _normalize_name(self, provider: str) -> str:
        return provider.strip().lower()

    def is_healthy(self, provider: str) -> bool:
        """
        Returns True if the provider is currently considered healthy and not exhausted.
        """
        norm = self._normalize_name(provider)
        with self._lock:
            state = self._providers.get(norm)
            if not state:
                return True
            return not state.get("exhausted", False)

    def is_exhausted(self, provider: str) -> bool:
        """
        Returns True if the provider is currently marked as exhausted.
        """
        return not self.is_healthy(provider)

    def record_exhausted(self, provider: str, reason: str = "") -> None:
        """
        Marks a provider as exhausted in-memory for the remainder of the run.
        Subsequent calls will immediately skip this provider.
        """
        norm = self._normalize_name(provider)
        with self._lock:
            now = time.time()
            current = self._providers.get(norm, {"failure_count": 0})
            current["exhausted"] = True
            current["exhausted_at"] = now
            current["reason"] = str(reason)
            current["failure_count"] = current.get("failure_count", 0) + 1
            self._providers[norm] = current

        logger.warning(
            f"🚫 [QuotaTracker] Provider '{norm}' marked EXHAUSTED (Reason: {reason}). "
            f"Subsequent calls in this run will immediately skip without timeout."
        )

    def record_success(self, provider: str) -> None:
        """
        Marks a provider as successfully operational.
        """
        norm = self._normalize_name(provider)
        with self._lock:
            self._providers[norm] = {
                "exhausted": False,
                "exhausted_at": None,
                "reason": None,
                "failure_count": 0,
                "last_success_at": time.time(),
            }

    def mark_healthy(self, provider: str) -> None:
        """
        Manually marks a provider as healthy.
        """
        self.record_success(provider)

    def get_status(self, provider: str) -> Dict[str, Any]:
        """
        Returns the current state dictionary of the specified provider.
        """
        norm = self._normalize_name(provider)
        with self._lock:
            state = self._providers.get(norm)
            if not state:
                return {"provider": norm, "exhausted": False, "failure_count": 0}
            res = dict(state)
            res["provider"] = norm
            return res

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns current health states for all registered providers.
        """
        with self._lock:
            return {k: dict(v) for k, v in self._providers.items()}

    def reset(self) -> None:
        """
        Resets all provider states to initial healthy state (useful for test fixtures).
        """
        with self._lock:
            self._providers.clear()
        logger.info("🔄 [QuotaTracker] All provider quota health states have been reset.")


# Global singleton instance
quota_tracker = QuotaHealthTracker()
