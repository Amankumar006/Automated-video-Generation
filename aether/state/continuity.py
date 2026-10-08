"""Aether World Model Continuity Auditor.

Multi-shot continuity verification engine that audits transitions between consecutive
cinematic shots, catching physical anomalies, unphysical velocities, prop conservation
violations, wardrobe regressions, and broken reciprocal eyeline relationships.
(Project Aether v2 - Pillar 5 / Pillar 2 / WBS 1.3).
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from aether.state.schemas import (
    ActionType,
    CharacterState,
    HandAttachment,
    PropState,
    SceneAction,
    SceneState,
)


def _get_action_type(action: SceneAction) -> str:
    """Extract normalized uppercase string from ActionType enum or string."""
    at = action.action_type
    if isinstance(at, ActionType):
        return at.value.upper()
    s = str(at)
    if "." in s:
        s = s.split(".")[-1]
    return s.upper()


class ContinuityViolationType(str, Enum):
    """Categorical classification of cinematic continuity violations."""
    TELEPORTATION = "TELEPORTATION"
    UNPHYSICAL_VELOCITY = "UNPHYSICAL_VELOCITY"
    PROP_CONSERVATION = "PROP_CONSERVATION"
    WARDROBE_REGRESSION = "WARDROBE_REGRESSION"
    INJURY_REGRESSION = "INJURY_REGRESSION"
    RECIPROCAL_EYELINE = "RECIPROCAL_EYELINE"
    LIGHTING_DISCONTINUITY = "LIGHTING_DISCONTINUITY"
    CUSTOM = "CUSTOM"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Union[str, ContinuityViolationType]) -> ContinuityViolationType:
        if isinstance(val, cls):
            return val
        s = str(val).upper().strip()
        for member in cls:
            if member.value == s or member.name == s:
                return member
        return cls.CUSTOM


class ContinuitySeverity(str, Enum):
    """Severity tier for a continuity violation."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Union[str, ContinuitySeverity]) -> ContinuitySeverity:
        if isinstance(val, cls):
            return val
        s = str(val).upper().strip()
        for member in cls:
            if member.value == s or member.name == s:
                return member
        return cls.ERROR


class ContinuityViolation(BaseModel):
    """Specific continuity violation defect identified across shots."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    violation_type: ContinuityViolationType = Field(..., description="Classification category")
    severity: ContinuitySeverity = Field(ContinuitySeverity.ERROR, description="Defect severity tier")
    entity_id: str = Field(..., description="Affected character ID, prop ID, or pair identifier")
    message: str = Field(..., description="Human-readable diagnosis of the continuity breach")
    details: Dict[str, Any] = Field(default_factory=dict, description="Quantitative diagnostics and metrics")
    shot_a_id: Optional[str] = Field(None, description="Originating shot identifier")
    shot_b_id: Optional[str] = Field(None, description="Destination shot identifier")


class ContinuityAuditResult(BaseModel):
    """Comprehensive audit report for a shot-to-shot cinematic transition."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_a_id: str = Field(..., description="Identifier of origin Shot A")
    shot_b_id: str = Field(..., description="Identifier of target Shot B")
    is_valid: bool = Field(True, description="True if no CRITICAL or ERROR violations are present")
    violations: List[ContinuityViolation] = Field(default_factory=list, description="List of identified violations")
    checked_characters: List[str] = Field(default_factory=list, description="Character IDs verified")
    checked_props: List[str] = Field(default_factory=list, description="Prop IDs verified")
    elapsed_seconds: float = Field(0.0, description="Elapsed time between shots")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual audit metadata")

    @property
    def passed(self) -> bool:
        """Alias for is_valid."""
        return self.is_valid

    @property
    def errors(self) -> List[ContinuityViolation]:
        """Returns only blocking violations (CRITICAL or ERROR)."""
        return [
            v for v in self.violations
            if v.severity in (ContinuitySeverity.CRITICAL, ContinuitySeverity.ERROR)
        ]

    @property
    def warnings(self) -> List[ContinuityViolation]:
        """Returns non-blocking warning violations."""
        return [v for v in self.violations if v.severity == ContinuitySeverity.WARNING]

    def has_violation_of_type(self, violation_type: Union[ContinuityViolationType, str]) -> bool:
        """Checks if a specific type of violation was caught."""
        target_val = violation_type.value if isinstance(violation_type, ContinuityViolationType) else str(violation_type)
        return any(v.violation_type.value == target_val for v in self.violations)

    def summary(self) -> str:
        """Human-readable summary string."""
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Audit [{self.shot_a_id} -> {self.shot_b_id}]: {status} with "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings."
        )


class ContinuityAuditor:
    """Multi-shot cinematic continuity verification engine."""

    def __init__(
        self,
        max_character_speed_mps: float = 10.0,
        instant_move_tolerance_m: float = 0.05,
        reciprocal_eyeline_tolerance_deg: float = 35.0,
        strict_mode: bool = False,
    ) -> None:
        self.max_character_speed_mps = max_character_speed_mps
        self.instant_move_tolerance_m = instant_move_tolerance_m
        self.reciprocal_eyeline_tolerance_deg = reciprocal_eyeline_tolerance_deg
        self.strict_mode = strict_mode

    def audit_transition(
        self,
        shot_a: SceneState,
        shot_b: SceneState,
        actions: Optional[List[SceneAction]] = None,
        elapsed_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContinuityAuditResult:
        """Audits cinematic continuity across the transition from Shot A to Shot B."""
        act_list = actions or []
        meta = metadata or {}

        # Determine elapsed time
        if elapsed_seconds is not None:
            dt = float(elapsed_seconds)
        else:
            # Sum from actions if available
            dt = sum(a.elapsed_seconds for a in act_list)

        violations: List[ContinuityViolation] = []
        shot_a_id = meta.get("shot_a_id") or shot_a.scene_id
        shot_b_id = meta.get("shot_b_id") or shot_b.scene_id

        # 1. Audit character kinematics (teleportation & unphysical velocity)
        checked_chars: List[str] = []
        for cid, ca in shot_a.character_roster.items():
            if cid in shot_b.character_roster:
                cb = shot_b.character_roster[cid]
                checked_chars.append(cid)
                v = self.check_teleportation(ca, cb, elapsed_seconds=dt)
                if v:
                    v.shot_a_id = shot_a_id
                    v.shot_b_id = shot_b_id
                    violations.append(v)

                # Wardrobe and injury regression checks
                w_violations = self.check_wardrobe_regression(ca, cb, actions=act_list)
                for wv in w_violations:
                    wv.shot_a_id = shot_a_id
                    wv.shot_b_id = shot_b_id
                    violations.append(wv)

        # 2. Audit prop conservation (vanishing, appearing, hand swap without transfer, unheld displacement)
        p_violations = self.check_prop_conservation(
            props_a=shot_a.prop_roster,
            props_b=shot_b.prop_roster,
            actions=act_list,
            elapsed_seconds=dt,
        )
        for pv in p_violations:
            pv.shot_a_id = shot_a_id
            pv.shot_b_id = shot_b_id
            violations.append(pv)
        checked_props = list(set(shot_a.prop_roster.keys()) | set(shot_b.prop_roster.keys()))

        # 3. Reciprocal eyeline checks
        checked_pairs: Set[Tuple[str, str]] = set()

        # A. Pairs explicitly requested in metadata
        eyeline_pairs = (
            meta.get("reciprocal_eyeline_pairs")
            or meta.get("conversing_pairs")
            or meta.get("dialogue_pairs")
            or meta.get("dialogue")
            or []
        )
        for pair in eyeline_pairs:
            if len(pair) == 2:
                cid1, cid2 = pair[0], pair[1]
                pair_key = (min(cid1, cid2), max(cid1, cid2))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                char1 = shot_b.character_roster.get(cid1)
                char2 = shot_b.character_roster.get(cid2)
                if char1 and char2:
                    ev = self.check_reciprocal_eyeline(char1, char2)
                    if ev:
                        ev.shot_a_id = shot_a_id
                        ev.shot_b_id = shot_b_id
                        violations.append(ev)

        # B. Pairs indicated via character metadata
        char_items = list(shot_b.character_roster.values())
        for c1 in char_items:
            partner_id = (
                c1.metadata.get("conversing_with")
                or c1.metadata.get("looking_at")
                or c1.metadata.get("dialogue_with")
            )
            if partner_id and partner_id in shot_b.character_roster:
                pair_key = (min(c1.id, partner_id), max(c1.id, partner_id))
                if pair_key not in checked_pairs:
                    checked_pairs.add(pair_key)
                    c2 = shot_b.character_roster[partner_id]
                    ev = self.check_reciprocal_eyeline(c1, c2)
                    if ev:
                        ev.shot_a_id = shot_a_id
                        ev.shot_b_id = shot_b_id
                        violations.append(ev)

        # C. Auto-detect conversational pairs in Shot B
        for i in range(len(char_items)):
            for j in range(i + 1, len(char_items)):
                c1, c2 = char_items[i], char_items[j]
                pair_key = (min(c1.id, c2.id), max(c1.id, c2.id))
                if pair_key in checked_pairs:
                    continue

                dist = c1.distance_to(c2)
                if dist <= 0.1 or dist > 15.0:
                    continue

                is_c1_looking, dev_1 = self._is_looking_at(c1, c2.position, self.reciprocal_eyeline_tolerance_deg)
                is_c2_looking, dev_2 = self._is_looking_at(c2, c1.position, self.reciprocal_eyeline_tolerance_deg)

                should_check = (is_c1_looking or is_c2_looking)
                if not should_check and len(char_items) == 2 and dist <= 8.0:
                    if dev_1 <= 90.0 and dev_2 <= 90.0:
                        should_check = True

                if should_check:
                    checked_pairs.add(pair_key)
                    ev = self.check_reciprocal_eyeline(c1, c2)
                    if ev:
                        ev.shot_a_id = shot_a_id
                        ev.shot_b_id = shot_b_id
                        violations.append(ev)

        has_blocking = any(
            v.severity in (ContinuitySeverity.CRITICAL, ContinuitySeverity.ERROR)
            for v in violations
        )

        return ContinuityAuditResult(
            shot_a_id=shot_a_id,
            shot_b_id=shot_b_id,
            is_valid=(not has_blocking),
            violations=violations,
            checked_characters=checked_chars,
            checked_props=checked_props,
            elapsed_seconds=dt,
            metadata=meta,
        )

    def audit_shots(
        self,
        world_model: Any,
        branch_name: Optional[str] = None,
    ) -> List[ContinuityAuditResult]:
        """Audits all consecutive shot transitions across a timeline branch."""
        timeline = world_model.get_timeline(branch_name)
        results: List[ContinuityAuditResult] = []
        for i in range(len(timeline) - 1):
            snap_a = timeline[i]
            snap_b = timeline[i + 1]
            dt = max(0.0, snap_b.timestamp - snap_a.timestamp)
            res = self.audit_transition(
                shot_a=snap_a.state,
                shot_b=snap_b.state,
                actions=snap_b.actions_applied,
                elapsed_seconds=dt,
                metadata={
                    "shot_a_id": snap_a.shot_id,
                    "shot_b_id": snap_b.shot_id,
                    **(snap_b.metadata or {}),
                },
            )
            res.shot_a_id = snap_a.shot_id
            res.shot_b_id = snap_b.shot_id
            for v in res.violations:
                v.shot_a_id = snap_a.shot_id
                v.shot_b_id = snap_b.shot_id
            results.append(res)
        return results

    def check_teleportation(
        self,
        char_a: CharacterState,
        char_b: CharacterState,
        elapsed_seconds: float,
    ) -> Optional[ContinuityViolation]:
        """Validates character movement distance against elapsed time."""
        pa = char_a.position
        pb = char_b.position
        dist = math.sqrt(
            (pb[0] - pa[0]) ** 2
            + (pb[1] - pa[1]) ** 2
            + (pb[2] - pa[2]) ** 2
        )

        if elapsed_seconds <= 0.0:
            if dist > self.instant_move_tolerance_m:
                return ContinuityViolation(
                    violation_type=ContinuityViolationType.TELEPORTATION,
                    severity=ContinuitySeverity.CRITICAL,
                    entity_id=char_a.id,
                    message=(
                        f"Instantaneous teleportation: Character '{char_a.id}' displaced by "
                        f"{dist:.2f}m with 0.0s elapsed time."
                    ),
                    details={
                        "character_id": char_a.id,
                        "distance_m": dist,
                        "elapsed_seconds": elapsed_seconds,
                        "tolerance_m": self.instant_move_tolerance_m,
                    },
                )
            return None

        speed = dist / elapsed_seconds
        if speed > self.max_character_speed_mps:
            return ContinuityViolation(
                violation_type=ContinuityViolationType.UNPHYSICAL_VELOCITY,
                severity=ContinuitySeverity.ERROR,
                entity_id=char_a.id,
                message=(
                    f"Unphysical velocity: Character '{char_a.id}' moved {dist:.2f}m in "
                    f"{elapsed_seconds:.2f}s ({speed:.2f} m/s exceeds max threshold {self.max_character_speed_mps} m/s)."
                ),
                details={
                    "character_id": char_a.id,
                    "distance_m": dist,
                    "elapsed_seconds": elapsed_seconds,
                    "velocity_mps": speed,
                    "threshold_mps": self.max_character_speed_mps,
                },
            )

        return None

    def check_prop_conservation(
        self,
        props_a: Dict[str, PropState],
        props_b: Dict[str, PropState],
        actions: List[SceneAction],
        elapsed_seconds: float = 0.0,
    ) -> List[ContinuityViolation]:
        """Detects vanishing props, spontaneous creation, possession breaches, or unphysical movements."""
        violations: List[ContinuityViolation] = []

        # Map actions involving props
        prop_actions: Dict[str, List[SceneAction]] = {}
        for action in actions:
            pid = (
                action.metadata.get("prop_id")
                or action.metadata.get("prop")
                or action.metadata.get("item")
            )
            if not pid:
                if action.target_id and (action.target_id in props_a or action.target_id in props_b):
                    pid = action.target_id
                elif action.actor_id and (action.actor_id in props_a or action.actor_id in props_b):
                    pid = action.actor_id
            if pid:
                prop_actions.setdefault(pid, []).append(action)

        # Check 1: Vanishing props
        for pid, pa in props_a.items():
            if pid not in props_b:
                acts = prop_actions.get(pid, [])
                is_consumed = any(
                    _get_action_type(a) in ("PROP_CONSUMED", "PROP_DESTROYED", "PROP_REMOVED", "PROP_DESPAWN")
                    or a.metadata.get("removed", False)
                    or a.metadata.get("consumed", False)
                    or a.metadata.get("destroyed", False)
                    for a in acts
                )
                if not is_consumed:
                    violations.append(ContinuityViolation(
                        violation_type=ContinuityViolationType.PROP_CONSERVATION,
                        severity=ContinuitySeverity.CRITICAL,
                        entity_id=pid,
                        message=(
                            f"Prop conservation violation: Prop '{pid}' ('{pa.name}') present in "
                            f"Shot A vanished in Shot B without an explanatory action."
                        ),
                        details={"prop_id": pid, "name": pa.name, "origin_owner": pa.owner_id},
                    ))

        # Check 2: Spontaneously appearing props
        for pid, pb in props_b.items():
            if pid not in props_a:
                acts = prop_actions.get(pid, [])
                is_introduced = any(
                    _get_action_type(a) in ("PROP_SPAWNED", "PROP_INTRODUCED", "PROP_CREATED", "PROP_PICKUP")
                    or a.metadata.get("spawned", False)
                    or a.metadata.get("introduced", False)
                    or a.metadata.get("created", False)
                    for a in acts
                )
                if not is_introduced:
                    violations.append(ContinuityViolation(
                        violation_type=ContinuityViolationType.PROP_CONSERVATION,
                        severity=ContinuitySeverity.CRITICAL,
                        entity_id=pid,
                        message=(
                            f"Prop conservation violation: Prop '{pid}' ('{pb.name}') appeared in "
                            f"Shot B without an introductory action."
                        ),
                        details={"prop_id": pid, "name": pb.name, "destination_owner": pb.owner_id},
                    ))

        # Check 3: Hand swap, holder change, or unheld prop movement
        for pid in set(props_a.keys()) & set(props_b.keys()):
            pa = props_a[pid]
            pb = props_b[pid]

            owner_changed = (pa.owner_id != pb.owner_id)
            hand_changed = (str(pa.hand_attachment).lower() != str(pb.hand_attachment).lower())

            acts = prop_actions.get(pid, [])

            if owner_changed or hand_changed:
                if not acts:
                    violations.append(ContinuityViolation(
                        violation_type=ContinuityViolationType.PROP_CONSERVATION,
                        severity=ContinuitySeverity.ERROR,
                        entity_id=pid,
                        message=(
                            f"Prop conservation violation: Prop '{pid}' possession changed from "
                            f"'{pa.owner_id}:{pa.hand_attachment}' to '{pb.owner_id}:{pb.hand_attachment}' "
                            f"without an explicit PROP_TRANSFER action."
                        ),
                        details={
                            "prop_id": pid,
                            "from_owner": pa.owner_id,
                            "to_owner": pb.owner_id,
                            "from_hand": str(pa.hand_attachment),
                            "to_hand": str(pb.hand_attachment),
                        },
                    ))
                else:
                    # Trace expected owner and hand across actions
                    cur_owner = pa.owner_id
                    cur_hand = str(pa.hand_attachment).lower()
                    explicit_hand_specified = False
                    has_transfer_action = False

                    for a in acts:
                        act_type = _get_action_type(a)
                        is_transfer_type = (
                            act_type in (
                                ActionType.PROP_TRANSFER.value,
                                "PROP_TRANSFER",
                                "PROP_HANDOFF",
                                "PROP_PICKUP",
                                "PROP_DROP",
                                "PICKUP",
                                "DROP",
                                "HANDOFF",
                                ActionType.PROP_MUTATION.value,
                                "PROP_MUTATION",
                            )
                            or a.metadata.get("is_transfer", False)
                            or a.metadata.get("drop", False)
                            or ("new_owner" in a.metadata)
                            or ("recipient" in a.metadata)
                            or ("to" in a.metadata)
                        )
                        if not is_transfer_type:
                            continue

                        has_transfer_action = True

                        is_drop = (
                            act_type in ("PROP_DROP", "DROP")
                            or a.metadata.get("drop", False)
                            or a.metadata.get("new_owner") in ("none", "world", "floor")
                            or a.metadata.get("recipient") in ("none", "world", "floor")
                            or a.metadata.get("to") in ("none", "world", "floor")
                        )

                        if is_drop:
                            cur_owner = None
                            cur_hand = "none"
                        else:
                            recipient = (
                                a.metadata.get("new_owner")
                                or a.metadata.get("recipient")
                                or a.metadata.get("to")
                            )
                            if not recipient and act_type in ("PROP_PICKUP", "PICKUP"):
                                recipient = a.actor_id
                            if not recipient and a.target_id and a.target_id != pid:
                                recipient = a.target_id

                            if recipient and str(recipient).lower() not in ("none", "world", "floor"):
                                cur_owner = str(recipient)

                            hand_spec = (
                                a.metadata.get("hand")
                                or a.metadata.get("to_hand")
                                or a.metadata.get("hand_attachment")
                            )
                            if hand_spec:
                                cur_hand = str(hand_spec).lower()
                                explicit_hand_specified = True
                            elif cur_owner is not None and cur_hand == "none":
                                cur_hand = str(pb.hand_attachment).lower()

                    if not has_transfer_action:
                        violations.append(ContinuityViolation(
                            violation_type=ContinuityViolationType.PROP_CONSERVATION,
                            severity=ContinuitySeverity.ERROR,
                            entity_id=pid,
                            message=(
                                f"Prop conservation violation: Prop '{pid}' possession changed from "
                                f"'{pa.owner_id}:{pa.hand_attachment}' to '{pb.owner_id}:{pb.hand_attachment}' "
                                f"without an explicit PROP_TRANSFER action."
                            ),
                            details={
                                "prop_id": pid,
                                "from_owner": pa.owner_id,
                                "to_owner": pb.owner_id,
                                "from_hand": str(pa.hand_attachment),
                                "to_hand": str(pb.hand_attachment),
                            },
                        ))
                    elif cur_owner != pb.owner_id:
                        violations.append(ContinuityViolation(
                            violation_type=ContinuityViolationType.PROP_CONSERVATION,
                            severity=ContinuitySeverity.ERROR,
                            entity_id=pid,
                            message=(
                                f"Prop conservation violation: Prop '{pid}' ended up in possession of "
                                f"'{pb.owner_id}', but actions transferred it to '{cur_owner}'."
                            ),
                            details={
                                "prop_id": pid,
                                "expected_owner": cur_owner,
                                "actual_owner": pb.owner_id,
                                "expected_hand": cur_hand,
                                "actual_hand": str(pb.hand_attachment),
                            },
                        ))
                    elif explicit_hand_specified and cur_hand != str(pb.hand_attachment).lower():
                        violations.append(ContinuityViolation(
                            violation_type=ContinuityViolationType.PROP_CONSERVATION,
                            severity=ContinuitySeverity.ERROR,
                            entity_id=pid,
                            message=(
                                f"Prop conservation violation: Prop '{pid}' held in '{pb.hand_attachment}' "
                                f"hand on '{pb.owner_id}', but transfer action specified '{cur_hand}' hand."
                            ),
                            details={
                                "prop_id": pid,
                                "owner_id": pb.owner_id,
                                "expected_hand": cur_hand,
                                "actual_hand": str(pb.hand_attachment),
                            },
                        ))

            # Check unheld prop displacement without movement action
            if pa.owner_id is None and pb.owner_id is None:
                if pa.world_coordinates is not None and pb.world_coordinates is not None:
                    dx = pb.world_coordinates[0] - pa.world_coordinates[0]
                    dy = pb.world_coordinates[1] - pa.world_coordinates[1]
                    dz = pb.world_coordinates[2] - pa.world_coordinates[2]
                    disp = math.sqrt(dx * dx + dy * dy + dz * dz)

                    if disp > self.instant_move_tolerance_m:
                        has_prop_move = any(
                            _get_action_type(a) in (
                                "PROP_MOVE",
                                "PROP_MUTATION",
                                "PHYSICS",
                                "ENVIRONMENT_CHANGE",
                                ActionType.PROP_MUTATION.value,
                            )
                            or a.metadata.get("moved", False)
                            or ("world_coordinates" in a.metadata)
                            or ("position" in a.metadata)
                            for a in acts
                        )
                        if not has_prop_move:
                            if elapsed_seconds <= 0.0:
                                violations.append(ContinuityViolation(
                                    violation_type=ContinuityViolationType.PROP_CONSERVATION,
                                    severity=ContinuitySeverity.CRITICAL,
                                    entity_id=pid,
                                    message=(
                                        f"Prop conservation violation: Unheld prop '{pid}' ('{pa.name}') displaced by "
                                        f"{disp:.2f}m with 0.0s elapsed time without a movement action."
                                    ),
                                    details={
                                        "prop_id": pid,
                                        "displacement_m": disp,
                                        "tolerance_m": self.instant_move_tolerance_m,
                                    },
                                ))
                            else:
                                prop_speed = disp / elapsed_seconds
                                if prop_speed > self.max_character_speed_mps:
                                    violations.append(ContinuityViolation(
                                        violation_type=ContinuityViolationType.PROP_CONSERVATION,
                                        severity=ContinuitySeverity.ERROR,
                                        entity_id=pid,
                                        message=(
                                            f"Prop conservation violation: Unheld prop '{pid}' ('{pa.name}') displaced by "
                                            f"{disp:.2f}m in {elapsed_seconds:.2f}s ({prop_speed:.2f} m/s) without a movement action."
                                        ),
                                        details={
                                            "prop_id": pid,
                                            "displacement_m": disp,
                                            "elapsed_seconds": elapsed_seconds,
                                            "velocity_mps": prop_speed,
                                        },
                                    ))

        return violations

    def check_wardrobe_regression(
        self,
        char_a: CharacterState,
        char_b: CharacterState,
        actions: List[SceneAction],
    ) -> List[ContinuityViolation]:
        """Detects irreversible wardrobe damage reverting to pristine without repair actions."""
        violations: List[ContinuityViolation] = []
        pristine_tokens = {"pristine", "clean", "intact", "new", "fresh", "unblemished", "normal", "none"}

        # Check wardrobe garments
        for slot, ga in char_a.wardrobe.items():
            gb = char_b.wardrobe.get(slot)
            if not gb:
                continue

            state_a = ga.state.lower().strip()
            state_b = gb.state.lower().strip()

            is_a_damaged = (state_a not in pristine_tokens) or (ga.damage_level > 0.1)
            is_b_pristine = (state_b in pristine_tokens) and (gb.damage_level <= 0.1)

            if is_a_damaged and (is_b_pristine or (gb.damage_level < ga.damage_level - 0.2 and state_b != state_a)):
                # Verify if repair action exists specifically for this garment slot
                char_acts = [
                    a for a in actions
                    if (a.actor_id == char_a.id or a.target_id == char_a.id)
                    and _get_action_type(a) in (
                        ActionType.WARDROBE_MUTATION.value,
                        "WARDROBE_MUTATION",
                        "WARDROBE_REPAIR",
                        "WARDROBE_CHANGE",
                        ActionType.WARDROBE_CHANGE.value,
                    )
                ]
                has_repair = False
                for a in char_acts:
                    is_repair_type = (
                        a.metadata.get("is_repair", False)
                        or a.metadata.get("allow_regression", False)
                        or a.metadata.get("action") in ("repair", "clean", "change", "replace")
                        or _get_action_type(a) in ("WARDROBE_REPAIR", "WARDROBE_CHANGE")
                    )
                    if not is_repair_type:
                        continue
                    act_slot = (
                        a.metadata.get("slot")
                        or a.metadata.get("garment")
                        or a.metadata.get("garment_slot")
                        or a.metadata.get("garment_id")
                    )
                    if act_slot:
                        act_slot_str = str(act_slot).lower().strip()
                        if act_slot_str in (slot.lower().strip(), ga.id.lower().strip(), "all", "outfit", "wardrobe"):
                            has_repair = True
                            break
                    else:
                        has_repair = True
                        break

                if not has_repair:
                    violations.append(ContinuityViolation(
                        violation_type=ContinuityViolationType.WARDROBE_REGRESSION,
                        severity=ContinuitySeverity.ERROR,
                        entity_id=f"{char_a.id}:{slot}",
                        message=(
                            f"Wardrobe state regression: Garment '{slot}' on character '{char_a.id}' "
                            f"regressed from damaged state '{ga.state}' to pristine state '{gb.state}' "
                            f"without an explicit repair or wardrobe change action."
                        ),
                        details={
                            "character_id": char_a.id,
                            "garment_slot": slot,
                            "state_before": ga.state,
                            "state_after": gb.state,
                            "damage_level_before": ga.damage_level,
                            "damage_level_after": gb.damage_level,
                        },
                    ))

        # Check physical injuries
        injury_violations = self.check_injuries_regression(char_a, char_b, actions)
        violations.extend(injury_violations)

        return violations

    def check_injuries_regression(
        self,
        char_a: CharacterState,
        char_b: CharacterState,
        actions: List[SceneAction],
    ) -> List[ContinuityViolation]:
        """Detects physical injuries disappearing without medical or healing actions."""
        violations: List[ContinuityViolation] = []
        for inj in char_a.injuries:
            if inj not in char_b.injuries:
                char_acts = [
                    a for a in actions
                    if (a.actor_id == char_a.id or a.target_id == char_a.id)
                    and (
                        a.metadata.get("healed", False)
                        or a.metadata.get("medical", False)
                        or _get_action_type(a) in (
                            "MEDICAL_TREATMENT",
                            "HEALING",
                            ActionType.HEALING.value,
                            ActionType.MEDICAL_TREATMENT.value,
                        )
                    )
                ]
                has_healing = False
                for a in char_acts:
                    act_inj = (
                        a.metadata.get("injury")
                        or a.metadata.get("target_injury")
                        or a.metadata.get("name")
                    )
                    if act_inj:
                        if str(act_inj).lower().strip() in (inj.lower().strip(), "all", "injuries"):
                            has_healing = True
                            break
                    else:
                        has_healing = True
                        break

                if not has_healing:
                    violations.append(ContinuityViolation(
                        violation_type=ContinuityViolationType.INJURY_REGRESSION,
                        severity=ContinuitySeverity.WARNING,
                        entity_id=char_a.id,
                        message=(
                            f"Physical injury '{inj}' on character '{char_a.id}' vanished without "
                            f"a medical or healing action."
                        ),
                        details={"character_id": char_a.id, "injury": inj},
                    ))

        return violations

    def check_reciprocal_eyeline(
        self,
        char_a: CharacterState,
        char_b: CharacterState,
        max_angle_deviation_deg: Optional[float] = None,
    ) -> Optional[ContinuityViolation]:
        """Validates that two conversing characters have approximately inverse eyeline vectors."""
        tolerance = max_angle_deviation_deg or self.reciprocal_eyeline_tolerance_deg

        ea = char_a.normalized_eyeline()
        eb = char_b.normalized_eyeline()

        # Direct eyeline dot product
        dot_product = sum(ea[i] * eb[i] for i in range(3))
        cos_clamped = max(-1.0, min(1.0, dot_product))
        angle_between_deg = math.degrees(math.acos(cos_clamped))

        # Inverse vectors must form 180 degrees. Deviation = |180 - angle|
        inverse_deviation_deg = abs(180.0 - angle_between_deg)

        # Spatial line-of-sight checks: are they pointing toward each other's 3D coordinates?
        pa = char_a.position
        pb = char_b.position
        dist = math.sqrt(sum((pb[i] - pa[i]) ** 2 for i in range(3)))
        if dist > 0.001:
            is_a_looking, dev_a = self._is_looking_at(char_a, char_b.position, tolerance)
            is_b_looking, dev_b = self._is_looking_at(char_b, char_a.position, tolerance)
        else:
            is_a_looking, dev_a = True, 0.0
            is_b_looking, dev_b = True, 0.0

        # If direct inverse angle is violated OR spatial target ray is misaligned:
        if inverse_deviation_deg > tolerance or not (is_a_looking and is_b_looking):
            return ContinuityViolation(
                violation_type=ContinuityViolationType.RECIPROCAL_EYELINE,
                severity=ContinuitySeverity.ERROR,
                entity_id=f"{char_a.id}:{char_b.id}",
                message=(
                    f"Reciprocal eyeline violation between '{char_a.id}' and '{char_b.id}': "
                    f"eyeline vectors have {inverse_deviation_deg:.1f}° deviation from inverse "
                    f"(eyeline angle is {angle_between_deg:.1f}°, expected ~180° within {tolerance}°). "
                    f"Spatial gaze deviations: {char_a.id}={dev_a:.1f}°, {char_b.id}={dev_b:.1f}°."
                ),
                details={
                    "character_a": char_a.id,
                    "character_b": char_b.id,
                    "eyeline_angle_deg": angle_between_deg,
                    "inverse_deviation_deg": inverse_deviation_deg,
                    "target_deviation_a_deg": dev_a,
                    "target_deviation_b_deg": dev_b,
                    "tolerance_deg": tolerance,
                },
            )

        return None

    def _is_looking_at(
        self,
        character: CharacterState,
        target_position: List[float],
        tolerance_deg: float,
    ) -> Tuple[bool, float]:
        """Calculates whether a character's eyeline is directed towards target position."""
        dx = target_position[0] - character.position[0]
        dy = target_position[1] - character.position[1]
        dz = target_position[2] - character.position[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)

        if dist < 0.001:
            return False, 180.0

        target_dir = [dx / dist, dy / dist, dz / dist]
        eyeline = character.normalized_eyeline()

        dot = sum(eyeline[i] * target_dir[i] for i in range(3))
        cos_clamped = max(-1.0, min(1.0, dot))
        deviation_deg = math.degrees(math.acos(cos_clamped))

        return (deviation_deg <= tolerance_deg), deviation_deg
