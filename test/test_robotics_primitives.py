"""
Test Scene for Robotics & TAMP Primitives.
Fast headless verification via:
manim -ql -s --media_dir test_media test/test_robotics_primitives.py TestRoboticsPrimitivesScene
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.primitives.robotics import (
    CoupledCanvas,
    CoupledNode,
    ConstraintProjectionSheaf,
    ParametricKinematicArm,
    ASTMorphTree,
    SandboxIsolationPod,
)

class TestRoboticsPrimitivesScene(Scene):
    def construct(self):
        # Configure 9:16 vertical view
        self.camera.background_color = "#0A0D14"

        # 1. Dual-Manifold Canvas Coordinator
        canvas = CoupledCanvas()
        self.add(canvas)

        # 2. Discrete Action Node in Top Pane
        node_pick = CoupledNode("ACTION OPERATOR", "pick(target_can, obs_table)", status="active")
        node_pick.move_to(canvas.discrete_to_point(0.0, 0.4))
        self.add(node_pick)

        # 3. Parametric Kinematic Arm in Bottom Pane
        arm_base = canvas.continuous_to_point(-1.2, -1.2)
        arm = ParametricKinematicArm(base_point=arm_base, link_lengths=(1.1, 0.9, 0.6))
        arm.set_angles([0.4, -0.8, 0.3])
        self.add(arm)

        # 4. Obstacle in Continuous Pane
        obstacle = RoundedRectangle(
            width=0.9, height=1.1, corner_radius=0.1,
            color="#EF4444", fill_color="#450A0A", fill_opacity=0.85, stroke_width=1.5
        ).move_to(canvas.continuous_to_point(0.8, -0.4))
        self.add(obstacle)

        # 5. Constraint Projection Sheaf connecting discrete node to obstacle
        sheaf = ConstraintProjectionSheaf(node_pick, obstacle, color="#38BDF8", opacity=0.18)
        self.add(sheaf)


class TestASTAndSandboxScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0D14"

        # 1. AST Tree at the top
        ast_spec = {
            "id": "root_fn",
            "type": "Function",
            "label": "synthesize_plan()",
            "children": [
                {
                    "id": "loop_while",
                    "type": "ControlFlow",
                    "label": "while not goal",
                    "children": [
                        {"id": "cond_ik", "type": "Condition", "label": "is_collision()"},
                        {"id": "hole_traj", "type": "Hole", "label": "??_rrt"}
                    ]
                },
                {
                    "id": "ret_action",
                    "type": "Block",
                    "label": "yield action"
                }
            ]
        }
        ast = ASTMorphTree(ast_spec, root_pos=np.array([0.0, 3.6, 0.0]), h_spacing=2.2, v_spacing=1.1)
        self.add(ast)

        # 2. Execution Sandbox Pod at the bottom
        pod = SandboxIsolationPod(width=6.0, height=3.0, pod_id="sbx_tamp_sim")
        pod.shift(DOWN * 2.2)
        pod.set_test_results([
            {"name": "test_start_pose", "status": "PASS", "latency": "1.2ms"},
            {"name": "test_obstacle_clearance", "status": "FAIL", "latency": "0.8ms"},
            {"name": "test_goal_reachability", "status": "PASS", "latency": "2.4ms"},
        ])
        self.add(pod)
