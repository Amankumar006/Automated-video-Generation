"""
The Model Verse — Test Suite for Spotlight Staging & Kinetic Camera Controllers (Visual Engine 7.0)
Validates cognitive visual hierarchy (100% focal / 20% background dimming) and kinetic camera breathing.
"""

import sys
import unittest
from pathlib import Path
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.controllers import SpotlightStagingController, KineticCameraController
from manim_engine.primitives.visual_compositions import (
    BlueprintGridMemory,
    BlueprintSplitFlow,
    BlueprintTreeHierarchy,
    BlueprintPipelineStages
)
from manim_engine.primitives.showdown_engine import BlueprintHorizontalRaceBars
from manim_engine.primitives.code_execution_engine import BlueprintChalkboardCodeBlock


class TestSpotlightAndCameraControllers(unittest.TestCase):

    def setUp(self):
        self.spotlight = SpotlightStagingController(default_dim_opacity=0.20)
        self.camera = KineticCameraController()

    def test_spotlight_grid_memory_partition(self):
        """Grid memory must isolate the active hit cell as focal and dim remaining cells."""
        grid = BlueprintGridMemory(
            title="KV CACHE GRID",
            active_cell_label="HIT: TOKEN",
            efficiency_label="O(1) LATENCY"
        )
        focal, bg = self.spotlight.identify_focal_and_background(grid)
        self.assertGreater(len(focal), 0)
        self.assertGreater(len(bg), 0)
        self.assertIn(grid.active_cell, focal)

    def test_spotlight_split_flow_partition(self):
        """Split flow must spotlight active branch based on SVO direct object."""
        split = BlueprintSplitFlow(
            input_label="UNIFIED STREAM",
            router_label="DISPATCH",
            branch_a_label="SEMANTIC",
            branch_b_label="GEOMETRIC"
        )
        svo_a = {"direct_object": "Semantic Representation"}
        focal_a, bg_a = self.spotlight.identify_focal_and_background(split, svo_action=svo_a)
        self.assertIn(split.branch_a_group, focal_a)
        self.assertIn(split.branch_b_group, bg_a)

        svo_b = {"direct_object": "Geometric Depth Map"}
        focal_b, bg_b = self.spotlight.identify_focal_and_background(split, svo_action=svo_b)
        self.assertIn(split.branch_b_group, focal_b)
        self.assertIn(split.branch_a_group, bg_b)

    def test_spotlight_tree_hierarchy_partition(self):
        """Tree hierarchy must spotlight optimal search branch while dimming pruned branches."""
        tree = BlueprintTreeHierarchy(
            root_label="ROOT QUERY",
            optimal_label="CHOSEN PATH",
            pruned_label="PRUNED"
        )
        focal, bg = self.spotlight.identify_focal_and_background(tree)
        self.assertIn(tree.optimal_group, focal)
        self.assertIn(tree.pruned_group, bg)

    def test_spotlight_race_bars_partition(self):
        """Horizontal drag race bars must spotlight hero bar and dim competitors."""
        race = BlueprintHorizontalRaceBars(
            title="THROUGHPUT SHOWDOWN",
            contestants=[
                {"name": "Ours", "value": 1180.0, "display_val": "1,180", "is_hero": True, "color": "#10B981"},
                {"name": "Prior", "value": 660.0, "display_val": "660", "is_hero": False, "color": "#38BDF8"}
            ]
        )
        focal, bg = self.spotlight.identify_focal_and_background(race)
        self.assertIn(race.hero_bar, focal)
        self.assertGreater(len(bg), 0)

    def test_spotlight_code_block_partition(self):
        """Chalkboard code block must spotlight highlighted kernel lines."""
        code = BlueprintChalkboardCodeBlock(
            filename="kernel.py",
            lines=["line 1", "line 2", "line 3"],
            highlight_lines=[2]
        )
        focal, bg = self.spotlight.identify_focal_and_background(code)
        self.assertGreater(len(focal), 0)
        self.assertGreater(len(bg), 0)

    def test_build_spotlight_animations(self):
        """Spotlight builder must create animations with 20% background dimming."""
        focal_dot = Dot()
        bg_dot = Dot()
        anims = self.spotlight.build_spotlight_animations(
            focal_elements=[focal_dot],
            background_elements=[bg_dot],
            run_time=0.5,
            dim_opacity=0.20
        )
        self.assertEqual(len(anims), 2)

    def test_create_spotlight_halo(self):
        """Spotlight halo must produce a valid SurroundingRectangle."""
        dot = Dot()
        halo = self.spotlight.create_spotlight_halo(dot, color="#34D399")
        self.assertIsInstance(halo, SurroundingRectangle)

    def test_kinetic_camera_ambient_drift(self):
        """Kinetic camera must generate continuous breathing drift animation."""
        mock_frame = Square()
        drift_anim = self.camera.get_ambient_drift_animation(
            camera_frame=mock_frame,
            duration=4.5
        )
        self.assertTrue(hasattr(drift_anim, "build") or isinstance(drift_anim, Animation))

    def test_multi_layer_depth_sandwich(self):
        """Multi-layer depth sandwich must assign correct z-indices across the 3 layers."""
        scene = MovingCameraScene()
        dots = VGroup(Dot())
        header = VGroup(Text("Header"))
        captions = VGroup(Text("Caption"))

        sandwich = self.camera.create_depth_sandwich(
            scene=scene,
            chalkboard_dots=dots,
            header_group=header,
            caption_container=captions
        )

        self.assertEqual(sandwich["backdrop"].z_index, -10)
        self.assertEqual(sandwich["header"].z_index, 50)
        self.assertEqual(sandwich["captions"].z_index, 60)


if __name__ == "__main__":
    unittest.main()
