"""Project Aether World Model (Scene State Graph Engine).

Provides persistent scene state representations, graph delta mutation engines,
multi-shot continuity auditing, and state storage & ledger query facilities.
(Pillar 2 / WBS 1.3).
"""

from __future__ import annotations

from aether.state.continuity import (
    ContinuityAuditor,
    ContinuityAuditResult,
    ContinuitySeverity,
    ContinuityViolation,
    ContinuityViolationType,
)
from aether.state.graph import AetherWorldModel
from aether.state.schemas import (
    ActionType,
    CameraDelta,
    CameraState,
    CharacterDelta,
    CharacterState,
    EnvironmentDelta,
    EnvironmentState,
    HandAttachment,
    PhysicalState,
    PropDelta,
    PropState,
    SceneAction,
    SceneSnapshot,
    SceneState,
    StateDelta,
    WardrobeItemState,
)
from aether.state.store import (
    CharacterMovementPoint,
    InjuryRecord,
    PropPossessionRecord,
    WardrobeRecord,
    WorldStateStore,
)

__all__ = [
    # Schemas
    "ActionType",
    "HandAttachment",
    "PhysicalState",
    "WardrobeItemState",
    "CharacterState",
    "PropState",
    "CameraState",
    "EnvironmentState",
    "SceneState",
    "SceneAction",
    "CharacterDelta",
    "PropDelta",
    "CameraDelta",
    "EnvironmentDelta",
    "StateDelta",
    "SceneSnapshot",
    # World Model
    "AetherWorldModel",
    # Continuity
    "ContinuityAuditor",
    "ContinuityAuditResult",
    "ContinuitySeverity",
    "ContinuityViolation",
    "ContinuityViolationType",
    # Store
    "WorldStateStore",
    "PropPossessionRecord",
    "CharacterMovementPoint",
    "WardrobeRecord",
    "InjuryRecord",
]
