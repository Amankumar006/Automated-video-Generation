"""
The Model Verse — Tests for Tier 1 Deterministic CV Gatekeeper Engine
"""

import time
import pytest
import numpy as np
import cv2
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.vsg.schema import BoundingBoxPx
from pipeline.qa.tier1_cv_gatekeeper import (
    GatekeeperVerdict,
    FarnebackMotionAnalyzer,
    WCAGContrastAnalyzer,
    AABBCollisionSolver,
    MobileSafeZoneAuditor,
    Tier1CVGatekeeper
)


def create_blank_canvas(color_bgr=(15, 11, 6)) -> np.ndarray:
    """Creates a 1080x1920 canvas filled with dark background color."""
    return np.full((1920, 1080, 3), color_bgr, dtype=np.uint8)


class TestTier1CVGatekeeper:
    def test_optical_flow_jitter_and_strobing(self):
        analyzer = FarnebackMotionAnalyzer()

        # 1. Identical frames: zero motion, SSIM = 1.0, passes
        frame1 = np.full((1920, 1080), 20, dtype=np.uint8)
        frame2 = frame1.copy()
        passed, violations, metrics, flow = analyzer.analyze(frame1, frame2)
        assert passed
        assert len(violations) == 0
        assert metrics["ssim"] > 0.99

        # 2. Severe flashing/strobing: frame drops from bright to pitch black
        frame_bright = np.full((1920, 1080), 200, dtype=np.uint8)
        frame_black = np.zeros((1920, 1080), dtype=np.uint8)
        passed_strobe, strobe_violations, _, _ = analyzer.analyze(frame_bright, frame_black)
        assert not passed_strobe
        assert any(v.rule == "GLOBAL_STROBING_DETECTED" for v in strobe_violations)

    def test_wcag_aaa_contrast_analyzer(self):
        analyzer = WCAGContrastAnalyzer()
        canvas = create_blank_canvas(color_bgr=(20, 16, 11))  # dark navy background

        # Case A: High contrast card (White text on dark canvas)
        box_high = BoundingBoxPx(x_min_px=200, y_min_px=400, width_px=500, height_px=200)
        # Draw white glyphs inside the box
        cv2.putText(canvas, "FRONTIER AI", (240, 520), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)

        passed_high, violation_high, cr_high = analyzer.evaluate_bounding_box(canvas, box_high, "card_high")
        assert passed_high
        assert violation_high is None
        assert cr_high >= 7.0

        # Case B: Low contrast card (Dark muted slate text on dark canvas)
        canvas_low = create_blank_canvas(color_bgr=(20, 16, 11))
        box_low = BoundingBoxPx(x_min_px=200, y_min_px=700, width_px=500, height_px=200)
        # Draw very low contrast text: color (28, 22, 16) vs (20, 16, 11)
        cv2.putText(canvas_low, "UNREADABLE TEXT", (240, 820), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (32, 26, 18), 4)

        passed_low, violation_low, cr_low = analyzer.evaluate_bounding_box(canvas_low, box_low, "card_low")
        assert not passed_low
        assert violation_low is not None
        assert violation_low.rule == "WCAG_CONTRAST_VIOLATION"
        assert cr_low < 7.0

    def test_aabb_collision_solver(self):
        solver = AABBCollisionSolver()

        # Disjoint boxes
        box1 = ("card1", BoundingBoxPx(x_min_px=200, y_min_px=300, width_px=400, height_px=200))
        box2 = ("card2", BoundingBoxPx(x_min_px=200, y_min_px=600, width_px=400, height_px=200))
        passed, violations = solver.audit_collisions([box1, box2])
        assert passed
        assert len(violations) == 0

        # Colliding boxes
        box_overlap = ("card_overlap", BoundingBoxPx(x_min_px=250, y_min_px=400, width_px=400, height_px=200))
        passed_col, col_violations = solver.audit_collisions([box1, box_overlap])
        assert not passed_col
        assert any(v.rule == "AABB_SPATIAL_COLLISION" for v in col_violations)

    def test_mobile_safe_zone_auditor(self):
        auditor = MobileSafeZoneAuditor()

        # 1. Sacred safe zone box -> Passes
        safe_box = BoundingBoxPx(x_min_px=200, y_min_px=300, width_px=600, height_px=800)
        passed, violation, _ = auditor.audit_box(safe_box, "safe_node")
        assert passed
        assert violation is None

        # 2. Top corridor breach (Y < 220) -> Fails
        top_box = BoundingBoxPx(x_min_px=200, y_min_px=100, width_px=600, height_px=200)
        passed_top, violation_top, _ = auditor.audit_box(top_box, "top_node")
        assert not passed_top
        assert violation_top.rule == "SAFE_ZONE_BREACH"

        # 3. Bottom corridor breach (Y > 1420) -> Fails
        bottom_box = BoundingBoxPx(x_min_px=200, y_min_px=1400, width_px=600, height_px=200)
        passed_bottom, violation_bottom, _ = auditor.audit_box(bottom_box, "bottom_node")
        assert not passed_bottom
        assert violation_bottom.rule == "SAFE_ZONE_BREACH"

        # 4. Right engagement rail breach (X > 920) -> Fails
        rail_box = BoundingBoxPx(x_min_px=900, y_min_px=500, width_px=150, height_px=200)
        passed_rail, violation_rail, _ = auditor.audit_box(rail_box, "rail_node")
        assert not passed_rail
        assert violation_rail.rule == "SAFE_ZONE_BREACH"

    def test_master_gatekeeper_latency_benchmark(self):
        gatekeeper = Tier1CVGatekeeper()
        frame1 = create_blank_canvas()
        frame2 = create_blank_canvas()

        # Add sample text to frame2
        cv2.putText(frame2, "PRO BROADCAST", (300, 600), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
        node_box = ("hero_text", BoundingBoxPx(x_min_px=250, y_min_px=500, width_px=600, height_px=200), True)

        # Benchmark 10 consecutive frames
        latencies = []
        for i in range(10):
            report, _ = gatekeeper.evaluate_frame(
                frame2,
                frame_index=i,
                prev_frame_bgr=frame1,
                node_boxes=[node_box]
            )
            latencies.append(report.latency_ms)

        mean_latency = float(np.mean(latencies))
        assert report.passed
        # The spec requires < 50ms per frame
        assert mean_latency < 50.0, f"Mean latency ({mean_latency}ms) exceeded 50ms target"
