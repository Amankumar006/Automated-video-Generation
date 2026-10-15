"""
The Model Verse — Pre-Render Static AST Linter & PBD Layout Collision Solver
Validates VSG-IR ASTs prior to rendering:
1. Word density caps (<=14 words/card, <=24 words/frame)
2. Rule of One focal validation
3. AABB pairwise collision detection (zero-tolerance IoU = 0.0)
4. Mobile 9:16 safe-zone boundary compliance
5. Position-Based Dynamics (PBD) Minimum Translation Vector (MTV) auto-relaxation
"""

import copy
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from pipeline.vsg.schema import (
    VideoSceneGraphIR,
    BeatAST,
    LayoutContainer,
    VisualNode,
    BoundingBoxPx,
    BandType,
    NodeType
)


# Mobile 9:16 Safe Zone Coordinates on 1080x1920 canvas
SAFE_ZONE_X_MIN = 120.0
SAFE_ZONE_X_MAX = 920.0
SAFE_ZONE_Y_MIN = 220.0
SAFE_ZONE_Y_MAX = 1420.0

# Density Limits
MAX_WORDS_PER_CARD = 14
MAX_WORDS_PER_FRAME = 24


class LintViolationSeverity(str):
    ERROR = "ERROR"
    WARNING = "WARNING"


class LintViolation(BaseModel):
    severity: str = LintViolationSeverity.ERROR
    rule: str
    message: str
    beat_id: int
    node_id: Optional[str] = None
    container_id: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class LintReport(BaseModel):
    is_valid: bool
    violations: List[LintViolation] = Field(default_factory=list)
    auto_relaxed: bool = False
    relaxed_ast: Optional[VideoSceneGraphIR] = None

    @property
    def passed(self) -> bool:
        return self.is_valid

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == LintViolationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == LintViolationSeverity.WARNING)


def count_words(text: str) -> int:
    """Helper to count alphanumeric words in a text block."""
    if not text:
        return 0
    return len([w for w in text.strip().split() if w])


def extract_node_text(node: VisualNode) -> str:
    """Extracts user-facing text from props based on node type."""
    props = node.props
    collected = []
    for key in ("title", "headline", "label", "text", "description", "value", "caption", "metric"):
        val = props.get(key)
        if isinstance(val, str):
            collected.append(val)
        elif isinstance(val, (int, float)):
            collected.append(str(val))
    return " ".join(collected)


class VSGASTLinter:
    """Static pre-render validator and layout collision solver for VSG-IR."""

    def __init__(
        self,
        safe_x_min: float = SAFE_ZONE_X_MIN,
        safe_x_max: float = SAFE_ZONE_X_MAX,
        safe_y_min: float = SAFE_ZONE_Y_MIN,
        safe_y_max: float = SAFE_ZONE_Y_MAX,
        max_words_card: int = MAX_WORDS_PER_CARD,
        max_words_frame: int = MAX_WORDS_PER_FRAME
    ):
        self.safe_x_min = safe_x_min
        self.safe_x_max = safe_x_max
        self.safe_y_min = safe_y_min
        self.safe_y_max = safe_y_max
        self.max_words_card = max_words_card
        self.max_words_frame = max_words_frame

    def lint_and_solve(self, ast: VideoSceneGraphIR) -> Tuple[LintReport, VideoSceneGraphIR]:
        """Convenience method returning both LintReport and the relaxed/solved VideoSceneGraphIR."""
        report = self.lint(ast, auto_relax_pbd=True)
        solved_ast = report.relaxed_ast if report.relaxed_ast is not None else ast
        return report, solved_ast

    def lint(self, ast: VideoSceneGraphIR, auto_relax_pbd: bool = True) -> LintReport:
        """Audits the full VSG-IR AST and optionally applies PBD collision relaxation."""
        violations: List[LintViolation] = []

        # 1. Audit Project Metadata
        if ast.metadata.canvas.width_px != 1080 or ast.metadata.canvas.height_px != 1920:
            violations.append(LintViolation(
                severity=LintViolationSeverity.ERROR,
                rule="CANVAS_DIMENSIONS",
                message=f"Canvas must be 1080x1920 9:16 vertical video. Found {ast.metadata.canvas.width_px}x{ast.metadata.canvas.height_px}",
                beat_id=0
            ))

        # 2. Audit Beats
        for beat in ast.beats:
            self._lint_beat(beat, violations)

        # 3. Collision Audit & Relaxation
        collision_violations = [v for v in violations if v.rule == "AABB_COLLISION"]
        relaxed_ast: Optional[VideoSceneGraphIR] = None
        auto_relaxed = False

        if collision_violations and auto_relax_pbd:
            relaxed_ast, resolved = self.relax_collisions(ast)
            if resolved:
                # Re-audit relaxed AST
                re_violations: List[LintViolation] = []
                for b in relaxed_ast.beats:
                    self._lint_beat(b, re_violations)
                # If collisions resolved, update report
                violations = re_violations
                auto_relaxed = True

        has_errors = any(v.severity == LintViolationSeverity.ERROR for v in violations)

        return LintReport(
            is_valid=(not has_errors),
            violations=violations,
            auto_relaxed=auto_relaxed,
            relaxed_ast=relaxed_ast
        )

    def _lint_beat(self, beat: BeatAST, violations: List[LintViolation]):
        # Rule of One Focus Node Check
        focus_id = beat.narrative.primary_focus_node_id
        all_nodes = beat.all_nodes()
        node_ids = {n.id for n in all_nodes}

        if focus_id and focus_id not in node_ids:
            violations.append(LintViolation(
                severity=LintViolationSeverity.ERROR,
                rule="RULE_OF_ONE_FOCUS",
                message=f"Beat {beat.beat_id} primary_focus_node_id '{focus_id}' does not exist in any container",
                beat_id=beat.beat_id,
                node_id=focus_id
            ))

        # Word Density per Frame Check
        total_frame_words = sum(count_words(extract_node_text(n)) for n in all_nodes)
        if total_frame_words > self.max_words_frame:
            violations.append(LintViolation(
                severity=LintViolationSeverity.WARNING,
                rule="FRAME_WORD_DENSITY",
                message=f"Beat {beat.beat_id} total static text has {total_frame_words} words (exceeds recommendation of {self.max_words_frame})",
                beat_id=beat.beat_id,
                metrics={"total_words": total_frame_words, "limit": self.max_words_frame}
            ))

        # Node-by-node audits
        for container in beat.layout_containers:
            # Container Safe Zone Check
            cb = container.bounds
            if cb.x_min_px < self.safe_x_min or cb.x_max_px > self.safe_x_max or \
               cb.y_min_px < self.safe_y_min or cb.y_max_px > self.safe_y_max:
                violations.append(LintViolation(
                    severity=LintViolationSeverity.ERROR,
                    rule="CONTAINER_SAFE_ZONE",
                    message=f"Container '{container.container_id}' bounds [{cb.x_min_px}, {cb.y_min_px}, {cb.x_max_px}, {cb.y_max_px}] breach safe zone [{self.safe_x_min}, {self.safe_y_min}, {self.safe_x_max}, {self.safe_y_max}]",
                    beat_id=beat.beat_id,
                    container_id=container.container_id
                ))

            for node in container.nodes:
                # Node Word Density
                text = extract_node_text(node)
                w_count = count_words(text)
                if w_count > self.max_words_card:
                    violations.append(LintViolation(
                        severity=LintViolationSeverity.ERROR,
                        rule="CARD_WORD_DENSITY",
                        message=f"Node '{node.id}' contains {w_count} words (max allowed: {self.max_words_card})",
                        beat_id=beat.beat_id,
                        node_id=node.id,
                        metrics={"word_count": w_count, "limit": self.max_words_card}
                    ))

                # Node Safe Zone Check (if explicit bounds set)
                nb = node.bounds
                if nb:
                    if nb.x_min_px < self.safe_x_min or nb.x_max_px > self.safe_x_max or \
                       nb.y_min_px < self.safe_y_min or nb.y_max_px > self.safe_y_max:
                        violations.append(LintViolation(
                            severity=LintViolationSeverity.ERROR,
                            rule="NODE_SAFE_ZONE",
                            message=f"Node '{node.id}' bounds [{nb.x_min_px}, {nb.y_min_px}, {nb.x_max_px}, {nb.y_max_px}] breach mobile safe zone",
                            beat_id=beat.beat_id,
                            node_id=node.id
                        ))

        # Pairwise Node Collision Audit (within beat)
        bounded_nodes = [(n.id, n.bounds) for n in all_nodes if n.bounds]
        for i in range(len(bounded_nodes)):
            for j in range(i + 1, len(bounded_nodes)):
                id_a, bounds_a = bounded_nodes[i]
                id_b, bounds_b = bounded_nodes[j]
                if bounds_a.intersects(bounds_b):
                    iou = bounds_a.intersection_iou(bounds_b)
                    violations.append(LintViolation(
                        severity=LintViolationSeverity.ERROR,
                        rule="AABB_COLLISION",
                        message=f"Spatial collision between nodes '{id_a}' and '{id_b}' (IoU: {iou:.3f})",
                        beat_id=beat.beat_id,
                        node_id=f"{id_a} vs {id_b}",
                        metrics={"node_a": id_a, "node_b": id_b, "iou": iou}
                    ))

    def relax_collisions(self, ast: VideoSceneGraphIR, max_iterations: int = 8) -> Tuple[VideoSceneGraphIR, bool]:
        """
        Applies Position-Based Dynamics (PBD) Minimum Translation Vectors (MTV)
        to resolve pairwise collisions and clamps nodes to safe zones.
        """
        cloned = copy.deepcopy(ast)
        all_resolved = True

        # Node weights: fixed/stage nodes are heavier (w=0.2), text cards/pills lighter (w=1.0)
        def get_inv_mass(node: VisualNode) -> float:
            if node.node_type in (NodeType.METRIC_PILL, NodeType.KINETIC_CAPTION_STREAM):
                return 1.2
            if node.node_type in (NodeType.GLASS_HUD_CARD, NodeType.EQUATION_CHASSIS):
                return 0.8
            return 0.3  # heavy central stage visual

        for beat in cloned.beats:
            # 1. Clamp container bounds to safe zone
            for container in beat.layout_containers:
                cb = container.bounds
                max_w = self.safe_x_max - self.safe_x_min
                max_h = self.safe_y_max - self.safe_y_min
                if cb.width_px > max_w:
                    cb.width_px = max_w
                if cb.height_px > max_h:
                    cb.height_px = max_h
                cb.x_min_px = max(self.safe_x_min, min(self.safe_x_max - cb.width_px, cb.x_min_px))
                cb.y_min_px = max(self.safe_y_min, min(self.safe_y_max - cb.height_px, cb.y_min_px))

            all_nodes = beat.all_nodes()
            bounded = [n for n in all_nodes if n.bounds]

            # 2. Pre-clamp all bounded nodes to safe zone
            for n in bounded:
                b = n.bounds
                max_w = self.safe_x_max - self.safe_x_min
                max_h = self.safe_y_max - self.safe_y_min
                if b.width_px > max_w:
                    b.width_px = max_w
                if b.height_px > max_h:
                    b.height_px = max_h
                b.x_min_px = max(self.safe_x_min, min(self.safe_x_max - b.width_px, b.x_min_px))
                b.y_min_px = max(self.safe_y_min, min(self.safe_y_max - b.height_px, b.y_min_px))

            # 3. PBD collision relaxation loop
            for _ in range(max_iterations):
                had_collision = False
                for i in range(len(bounded)):
                    for j in range(i + 1, len(bounded)):
                        node_a = bounded[i]
                        node_b = bounded[j]
                        b_a = node_a.bounds
                        b_b = node_b.bounds

                        if b_a.intersects(b_b):
                            had_collision = True
                            w_a = get_inv_mass(node_a)
                            w_b = get_inv_mass(node_b)
                            w_sum = w_a + w_b

                            # Overlap deltas
                            dx1 = b_a.x_max_px - b_b.x_min_px
                            dx2 = b_b.x_max_px - b_a.x_min_px
                            dy1 = b_a.y_max_px - b_b.y_min_px
                            dy2 = b_b.y_max_px - b_a.y_min_px

                            dx = dx1 if dx1 < dx2 else -dx2
                            dy = dy1 if dy1 < dy2 else -dy2

                            # Minimum Translation Vector along smallest penetration axis
                            if abs(dx) < abs(dy):
                                shift_x_a = -(w_a / w_sum) * dx
                                shift_x_b = +(w_b / w_sum) * dx
                                shift_y_a = 0.0
                                shift_y_b = 0.0
                            else:
                                shift_x_a = 0.0
                                shift_x_b = 0.0
                                shift_y_a = -(w_a / w_sum) * dy
                                shift_y_b = +(w_b / w_sum) * dy

                            # Apply translation
                            b_a.x_min_px += shift_x_a
                            b_b.x_min_px += shift_x_b
                            b_a.y_min_px += shift_y_a
                            b_b.y_min_px += shift_y_b

                            # Clamp to Safe Zone
                            b_a.x_min_px = max(self.safe_x_min, min(self.safe_x_max - b_a.width_px, b_a.x_min_px))
                            b_a.y_min_px = max(self.safe_y_min, min(self.safe_y_max - b_a.height_px, b_a.y_min_px))
                            b_b.x_min_px = max(self.safe_x_min, min(self.safe_x_max - b_b.width_px, b_b.x_min_px))
                            b_b.y_min_px = max(self.safe_y_min, min(self.safe_y_max - b_b.height_px, b_b.y_min_px))

                if not had_collision:
                    break
            else:
                all_resolved = False

        return cloned, all_resolved
