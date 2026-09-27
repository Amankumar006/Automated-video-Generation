"""
Parametric Kinematic Arm & Link Chain for Robotics Motion Planning.
Computes forward kinematics (FK) analytically and renders capsule hulls
with SE(2) end-effector coordinate frames.
"""

from manim import *
import numpy as np
from typing import Optional, List, Tuple


class ParametricKinematicArm(VGroup):
    """
    Planar multi-link robot manipulator with forward kinematics computation,
    capsule hulls, and SE(2) end-effector orientation frames.
    """
    def __init__(
        self,
        base_point: np.ndarray = np.array([-1.8, -3.2, 0.0]),
        link_lengths: tuple = (1.4, 1.1, 0.7),
        joint_angles: Optional[list] = None,
        link_radius: float = 0.12,
        base_color: str = "#38BDF8",
        **kwargs
    ):
        if "color" in kwargs:
            base_color = kwargs.pop("color")
        super().__init__(**kwargs)
        self.base_point = np.array(base_point, dtype=float)
        self.link_lengths = link_lengths
        self.link_radius = link_radius
        self.base_color = base_color

        # State: current joint angles in radians
        if joint_angles is not None:
            self.angles = list(joint_angles)
        else:
            self.angles = [0.0] * len(link_lengths)

        # Mobjects containers
        self.links_group = VGroup()
        self.joints_group = VGroup()
        self.ee_frame = VGroup()

        self.add(self.links_group, self.joints_group, self.ee_frame)
        self.set_angles(self.angles)

    def compute_fk(self, angles: list) -> tuple[list[np.ndarray], float]:
        """Computes joint positions and final end-effector heading via forward kinematics."""
        points = [self.base_point.copy()]
        curr_p = self.base_point.copy()
        accum_angle = 0.0

        for L, theta in zip(self.link_lengths, angles):
            accum_angle += theta
            dx = L * np.cos(accum_angle)
            dy = L * np.sin(accum_angle)
            curr_p = curr_p + np.array([dx, dy, 0.0])
            points.append(curr_p.copy())

        return points, accum_angle

    def set_angles(self, angles: list):
        """Updates robot arm geometry to the specified joint angles."""
        self.angles = angles
        joint_pts, final_heading = self.compute_fk(angles)

        # Clear previous geometry
        self.links_group.submobjects.clear()
        self.joints_group.submobjects.clear()
        self.ee_frame.submobjects.clear()

        # Build capsule links and joint hubs
        for i in range(len(joint_pts) - 1):
            p1 = joint_pts[i]
            p2 = joint_pts[i + 1]

            # Capsule link: bold rounded stroke
            link_line = Line(
                p1, p2,
                stroke_width=self.link_radius * 75,
                stroke_color=self.base_color,
                stroke_opacity=0.88
            )
            self.links_group.add(link_line)

            # Joint hub
            joint_hub = Circle(
                radius=self.link_radius * 1.15,
                color="#F8FAFC",
                fill_color="#0F172A",
                fill_opacity=1.0,
                stroke_width=2.0
            ).move_to(p1)
            self.joints_group.add(joint_hub)

        # Terminal joint (wrist)
        self.joints_group.add(
            Circle(
                radius=self.link_radius * 1.15,
                color="#F8FAFC",
                fill_color="#0F172A",
                fill_opacity=1.0,
                stroke_width=2.0
            ).move_to(joint_pts[-1])
        )

        # End-Effector Coordinate Frame (SE(2) Triad)
        ee_pos = joint_pts[-1]
        x_dir = np.array([np.cos(final_heading), np.sin(final_heading), 0.0])
        y_dir = np.array([-np.sin(final_heading), np.cos(final_heading), 0.0])

        ee_axis_x = Arrow(
            ee_pos, ee_pos + x_dir * 0.40, buff=0,
            color="#EF4444", stroke_width=2.8, max_tip_length_to_length_ratio=0.35
        )
        ee_axis_y = Arrow(
            ee_pos, ee_pos + y_dir * 0.40, buff=0,
            color="#10B981", stroke_width=2.8, max_tip_length_to_length_ratio=0.35
        )
        self.ee_frame.add(ee_axis_x, ee_axis_y)
        return self

    @property
    def end_effector_point(self) -> np.ndarray:
        """Returns the current 3D position of the robot end-effector tip."""
        pts, _ = self.compute_fk(self.angles)
        return pts[-1]

    def animate_to_angles(self, target_angles: list, run_time: float = 1.0):
        """Returns a Transform animation interpolating to target joint angles."""
        target = ParametricKinematicArm(
            base_point=self.base_point,
            link_lengths=self.link_lengths,
            joint_angles=target_angles,
            link_radius=self.link_radius,
            base_color=self.base_color
        )
        return Transform(self, target, run_time=run_time)
