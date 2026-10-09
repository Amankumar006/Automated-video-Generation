"""
Unit tests for Kinetic Particle Radiance & Luminous Dynamics Engine (Visual Engine 7.5).
Verifies formula sparkle bursts, glowing neon halo pulses, and traveling photon streams.
"""

import sys
import unittest
import numpy as np
from pathlib import Path
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from manim_engine.primitives.particles import (
    create_formula_sparkle_burst,
    create_formula_halo_pulse,
    create_traveling_photon_stream
)


class TestParticleDynamics(unittest.TestCase):

    def test_create_formula_sparkle_burst(self):
        """Formula sparkle burst must generate expected particle count and alpha animation."""
        target = Square().move_to([0, -3.5, 0])
        particles, burst_anim = create_formula_sparkle_burst(
            target_mobject=target,
            color="#38BDF8",
            particle_count=14,
            run_time=0.55
        )
        self.assertIsInstance(particles, VGroup)
        self.assertEqual(len(particles), 14)
        self.assertTrue(isinstance(burst_anim, Animation) or hasattr(burst_anim, "run_time"))
        self.assertAlmostEqual(burst_anim.run_time, 0.55)

    def test_create_formula_halo_pulse(self):
        """Formula halo pulse must generate expanding glowing rectangle and animation."""
        target = RoundedRectangle(width=4.0, height=1.2).move_to([0, -3.5, 0])
        halo, pulse_anim = create_formula_halo_pulse(
            target_mobject=target,
            color="#34D399",
            run_time=0.65
        )
        self.assertIsInstance(halo, RoundedRectangle)
        self.assertTrue(isinstance(pulse_anim, (Animation, AnimationGroup)) or hasattr(pulse_anim, "build"))

    def test_create_traveling_photon_stream(self):
        """Traveling photon stream must generate moving particles along vector trajectory."""
        start = np.array([-2.0, 0.0, 0.0])
        end = np.array([2.0, 0.0, 0.0])
        photons, stream_anim = create_traveling_photon_stream(
            start_point=start,
            end_point=end,
            color="#34D399",
            particle_count=6,
            run_time=1.0
        )
        self.assertIsInstance(photons, VGroup)
        self.assertEqual(len(photons), 6)
        self.assertTrue(isinstance(stream_anim, Animation) or hasattr(stream_anim, "run_time"))


if __name__ == "__main__":
    unittest.main()
