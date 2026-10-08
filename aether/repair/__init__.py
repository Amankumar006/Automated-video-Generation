"""Project Aether Surgical Repair Engine (Pillar 6 / WBS 1.7).

Provides localized spatio-temporal inpainting masks, minimum necessary intervention
planning, audio remastering, and execution pipelines to address RSK-004.
"""

from __future__ import annotations

from aether.repair.executor import SurgicalRepairExecutor
from aether.repair.masking import TemporalMaskEngine
from aether.repair.planner import RepairPlanner
from aether.repair.schemas import (
    ComputeTier,
    ProtectedRegion,
    ProtectedRegionType,
    RepairActionType,
    RepairBoundaryMask,
    RepairExecutionResult,
    RepairPlan,
    SurgicalRepairTask,
)

__all__ = [
    "ComputeTier",
    "ProtectedRegion",
    "ProtectedRegionType",
    "RepairActionType",
    "RepairBoundaryMask",
    "RepairExecutionResult",
    "RepairPlan",
    "RepairPlanner",
    "SurgicalRepairExecutor",
    "SurgicalRepairTask",
    "TemporalMaskEngine",
]
