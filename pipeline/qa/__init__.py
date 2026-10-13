"""
The Model Verse — QA Package Init
Exports Tier 1 Deterministic CV Gatekeeper and diagnostic metrics.
"""

from pipeline.qa.tier1_cv_gatekeeper import (
    GatekeeperVerdict,
    GatekeeperViolation,
    Tier1AuditReport,
    FarnebackMotionAnalyzer,
    WCAGContrastAnalyzer,
    AABBCollisionSolver,
    MobileSafeZoneAuditor,
    Tier1CVGatekeeper
)

__all__ = [
    "GatekeeperVerdict",
    "GatekeeperViolation",
    "Tier1AuditReport",
    "FarnebackMotionAnalyzer",
    "WCAGContrastAnalyzer",
    "AABBCollisionSolver",
    "MobileSafeZoneAuditor",
    "Tier1CVGatekeeper"
]
