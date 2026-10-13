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
from pipeline.qa.tier2_vlm_council import (
    Tier2VLMCouncil,
    Tier2CouncilReport,
    GatekeeperCriticEvaluation,
    CriticDefect,
    PrescribedPatch,
    vlm_council
)
from pipeline.qa.closed_loop_repair import (
    ClosedLoopRepairEngine,
    VisualRepairDiagnosticLedger,
    RepairPatchLedgerEntry,
    repair_engine
)

__all__ = [
    "GatekeeperVerdict",
    "GatekeeperViolation",
    "Tier1AuditReport",
    "FarnebackMotionAnalyzer",
    "WCAGContrastAnalyzer",
    "AABBCollisionSolver",
    "MobileSafeZoneAuditor",
    "Tier1CVGatekeeper",
    "Tier2VLMCouncil",
    "Tier2CouncilReport",
    "GatekeeperCriticEvaluation",
    "CriticDefect",
    "PrescribedPatch",
    "vlm_council",
    "ClosedLoopRepairEngine",
    "VisualRepairDiagnosticLedger",
    "RepairPatchLedgerEntry",
    "repair_engine"
]
