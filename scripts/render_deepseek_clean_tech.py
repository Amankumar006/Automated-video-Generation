import os
from manim import *

# 1080x1920 9:16 Vertical Video Configuration for Shorts / Reels
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.background_color = "#0A0D14"  # Carbon Obsidian tech background

FONT_HELVETICA = "Helvetica"

class DeepSeekV3CleanTech(MovingCameraScene):
    def construct(self):
        # -----------------------------------------------------------------
        # BACKGROUND: Minimalist Clean Tech Dot Grid
        # -----------------------------------------------------------------
        bg_dots = []
        for x in range(-4, 5):
            for y in range(-7, 8):
                d = Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
                bg_dots.append(d)
        dot_grid = VGroup(*bg_dots)
        self.add(dot_grid)

        # Persistent Top Safe-Zone Brand Watermark
        brand_tag = VGroup(
            Text("THE MODEL VERSE", font=FONT_HELVETICA, font_size=20, color="#10B981", weight=BOLD),
            Text(" // ", font=FONT_HELVETICA, font_size=18, color="#475569"),
            Text("ARCHITECTURE LAB", font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM),
        ).arrange(RIGHT, buff=0.12).shift(UP * 7.1)
        self.add(brand_tag)

        # -----------------------------------------------------------------
        # BEAT 1: 0.0s – 6.0s (The Hard Hook & 671B Dynamic Counter)
        # "DeepSeek-V3 has 671 billion parameters. But running it costs almost nothing. How?"
        # -----------------------------------------------------------------
        b1_tag = RoundedRectangle(
            corner_radius=0.12, width=3.6, height=0.55,
            color="#10B981", fill_color="#064E3B", fill_opacity=0.45, stroke_width=1.5
        ).shift(UP * 5.6)
        b1_tag_txt = Text("FRONTIER AI ARCHITECTURE", font=FONT_HELVETICA, font_size=16, color="#A7F3D0", weight=BOLD).move_to(b1_tag)
        hook_tag_group = VGroup(b1_tag, b1_tag_txt)

        title = Text("DeepSeek-V3", font=FONT_HELVETICA, font_size=64, color=WHITE, weight=HEAVY).shift(UP * 4.6)
        
        # Dynamic Counter 0 -> 671
        counter_tracker = ValueTracker(0)
        total_num = always_redraw(
            lambda: Text(
                f"{int(counter_tracker.get_value())}B",
                font=FONT_HELVETICA,
                font_size=126,
                color="#10B981",
                weight=HEAVY
            ).shift(UP * 2.0)
        )
        total_label = Text("TOTAL PARAMETERS", font=FONT_HELVETICA, font_size=24, color="#94A3B8", weight=BOLD).shift(UP * 0.75)

        hook_card = RoundedRectangle(
            corner_radius=0.18, width=7.4, height=1.1,
            color="#F59E0B", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.0
        ).shift(DOWN * 1.6)
        hook_metric = Text("⚡ FRACTION OF GPT-4 INFERENCE COST", font=FONT_HELVETICA, font_size=20, color="#FDE047", weight=HEAVY).move_to(hook_card)
        hook_card_group = VGroup(hook_card, hook_metric)

        b1_static = VGroup(hook_tag_group, title, total_label, hook_card_group)

        # Active Progression (No Static Pause)
        self.play(FadeIn(hook_tag_group, shift=DOWN * 0.3), FadeIn(title, shift=DOWN * 0.3), run_time=0.8)
        self.add(total_num)
        self.play(
            counter_tracker.animate.set_value(671),
            FadeIn(total_label, shift=UP * 0.2),
            run_time=1.8
        )
        self.play(FadeIn(hook_card_group, shift=UP * 0.3), run_time=0.8)
        # Pulse & Micro-Camera Push instead of static wait
        self.play(
            Circumscribe(hook_card, color="#FBBF24", stroke_width=3.5, time_width=0.7),
            self.camera.frame.animate.scale(0.96).shift(UP * 0.15),
            run_time=1.4
        )
        self.play(
            Flash(total_num, color="#10B981", line_length=0.3, num_lines=8, time_width=0.5),
            run_time=0.7
        )
        self.play(
            FadeOut(b1_static), FadeOut(total_num),
            self.camera.frame.animate.scale(1 / 0.96).shift(DOWN * 0.15),
            run_time=0.5
        )

        # -----------------------------------------------------------------
        # BEAT 2: 6.0s – 15.0s (Dense Brute-Force Crisis: 64-Tile Overload & Heat Shockwaves)
        # "In a standard dense model, every single word forces all 671 billion weights to calculate at once. A massive brute-force bottleneck."
        # -----------------------------------------------------------------
        dense_header_box = RoundedRectangle(
            corner_radius=0.12, width=6.8, height=0.65,
            color="#FF3366", fill_color="#4C0519", fill_opacity=0.45, stroke_width=1.5
        ).shift(UP * 5.2)
        dense_header_txt = Text("TRADITIONAL DENSE MODEL", font=FONT_HELVETICA, font_size=20, color="#FECDD3", weight=BOLD).move_to(dense_header_box)
        dense_header = VGroup(dense_header_box, dense_header_txt)

        # 8x8 Grid of clean rounded tiles representing monolithic weights
        tiles = []
        for i in range(64):
            r = i // 8
            c = i % 8
            x = (c - 3.5) * 0.72
            y = 3.2 - (r * 0.72)
            tile = RoundedRectangle(
                corner_radius=0.08, width=0.58, height=0.58,
                color="#334155", fill_color="#1E293B", fill_opacity=0.7, stroke_width=1.2
            ).move_to([x, y, 0])
            tiles.append(tile)
        dense_box_grid = VGroup(*tiles)

        token_enter = RoundedRectangle(
            corner_radius=0.12, width=4.0, height=0.65,
            color="#38BDF8", fill_color="#0F172A", fill_opacity=0.95, stroke_width=1.8
        ).shift(UP * 4.2)
        token_enter_txt = Text('Input Word: "Intelligence"', font=FONT_HELVETICA, font_size=18, color=WHITE, weight=BOLD).move_to(token_enter)
        token_enter_grp = VGroup(token_enter, token_enter_txt)

        dense_warning_card = RoundedRectangle(
            corner_radius=0.16, width=7.4, height=1.25,
            color="#FF3366", fill_color="#111827", fill_opacity=0.95, stroke_width=2.0
        ).shift(DOWN * 3.8)
        dense_warn_title = Text("⚠️ 100% OF WEIGHTS FIRE PER WORD", font=FONT_HELVETICA, font_size=20, color="#FF3366", weight=HEAVY).shift(DOWN * 3.55)
        dense_warn_sub = Text("Monolithic Brute-Force Compute Bottleneck", font=FONT_HELVETICA, font_size=18, color="#CBD5E1").shift(DOWN * 4.05)
        dense_warn_group = VGroup(dense_warning_card, dense_warn_title, dense_warn_sub)

        # Real-time Compute Load Counter for continuous motion
        flop_tracker = ValueTracker(0)
        flop_readout = always_redraw(
            lambda: Text(
                f"COMPUTE LOAD: {int(flop_tracker.get_value())}%",
                font=FONT_HELVETICA,
                font_size=17,
                color="#FF6B6B",
                weight=BOLD
            ).shift(DOWN * 4.75)
        )

        b2_group = VGroup(dense_header, dense_box_grid, token_enter_grp, dense_warn_group, flop_readout)

        self.play(FadeIn(dense_header, shift=DOWN * 0.3), Create(dense_box_grid, lag_ratio=0.01), run_time=1.3)
        self.play(
            dense_box_grid.animate.set_color("#FF3366").set_fill("#881337", opacity=0.85),
            FadeIn(token_enter_grp, shift=DOWN * 0.3),
            run_time=1.1
        )
        self.add(flop_readout)
        self.play(
            FadeIn(dense_warn_group, shift=UP * 0.3),
            flop_tracker.animate.set_value(100),
            Circumscribe(dense_box_grid, color="#FF3366", stroke_width=3.5, time_width=0.7),
            run_time=1.4
        )
        # Sequential heat stress waves across tiles (Zero static downtime)
        self.play(
            LaggedStart(
                *[t.animate.set_fill("#EF4444", opacity=0.95).set_stroke(color=WHITE, width=2.0) for t in tiles],
                lag_ratio=0.015
            ),
            run_time=1.6
        )
        self.play(
            Circumscribe(dense_warning_card, color="#FF3366", stroke_width=3.5, time_width=0.6),
            dense_box_grid.animate.set_fill("#881337", opacity=0.7).set_stroke(color="#FF3366", width=1.2),
            run_time=1.6
        )
        # Camera micro shake / zoom out
        self.play(
            self.camera.frame.animate.scale(1.04),
            Flash(dense_warning_card, color="#FF3366", line_length=0.25, num_lines=8),
            run_time=1.5
        )
        self.play(
            FadeOut(b2_group),
            self.camera.frame.animate.scale(1 / 1.04),
            run_time=0.5
        )

        # -----------------------------------------------------------------
        # BEAT 3: 15.0s – 22.5s (Sparse MoE: 256 Modular Experts & Scanner Sweep)
        # "DeepSeek flips this with Sparse Mixture of Experts, dividing the entire model into 256 specialized sub-networks."
        # -----------------------------------------------------------------
        moe_header_box = RoundedRectangle(
            corner_radius=0.12, width=6.8, height=0.65,
            color="#10B981", fill_color="#064E3B", fill_opacity=0.45, stroke_width=1.5
        ).shift(UP * 5.7)
        moe_header_txt = Text("SPARSE MIXTURE OF EXPERTS", font=FONT_HELVETICA, font_size=20, color="#A7F3D0", weight=BOLD).move_to(moe_header_box)
        moe_header = VGroup(moe_header_box, moe_header_txt)

        hud_capsule = RoundedRectangle(
            corner_radius=0.12, width=6.8, height=0.55,
            color="#1F2937", fill_color="#111827", fill_opacity=0.9, stroke_width=1.5
        ).shift(UP * 4.95)
        hud_left = Text("Total: 671B", font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=BOLD).shift(UP * 4.95 + LEFT * 2.0)
        hud_mid = Text("•", font=FONT_HELVETICA, font_size=18, color="#475569").shift(UP * 4.95)
        hud_right = Text("Pool: 256 Experts", font=FONT_HELVETICA, font_size=18, color="#10B981", weight=BOLD).shift(UP * 4.95 + RIGHT * 1.8)
        hud_group = VGroup(hud_capsule, hud_left, hud_mid, hud_right)

        # 256 Expert Grid (16x16)
        expert_dots = []
        for i in range(256):
            row = i // 16
            col = i % 16
            x = (col - 7.5) * 0.36
            y = 1.8 - (row * 0.25)  # Spans 1.8 down to -1.95
            dot = Dot(point=[x, y, 0], radius=0.065, color="#1E293B", fill_opacity=0.85)
            expert_dots.append(dot)
        experts_grid = VGroup(*expert_dots)

        moe_label_pill = Text("256 SPECIALIZED EXPERT POOLS", font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=BOLD).shift(DOWN * 2.5)

        self.play(FadeIn(moe_header, shift=DOWN * 0.3), FadeIn(hud_group, shift=DOWN * 0.3), run_time=0.8)
        self.play(Create(experts_grid, lag_ratio=0.003), run_time=1.5)
        self.play(FadeIn(moe_label_pill, shift=UP * 0.3), run_time=0.7)

        # Scanner Line Sweep across the 256 experts (Eliminates static pause)
        scanner_line = Line(LEFT * 3.2, RIGHT * 3.2, stroke_color="#10B981", stroke_width=2.5, stroke_opacity=0.8).shift(UP * 1.9)
        self.play(
            scanner_line.animate.shift(DOWN * 3.8),
            LaggedStart(
                *[expert_dots[i].animate.set_color("#34D399").set_opacity(0.9) for i in range(0, 256, 4)],
                lag_ratio=0.01
            ),
            run_time=2.2
        )
        self.play(
            FadeOut(scanner_line),
            *[expert_dots[i].animate.set_color("#1E293B").set_opacity(0.85) for i in range(0, 256, 4)],
            self.camera.frame.animate.scale(0.95).shift(UP * 0.1),
            run_time=1.8
        )
        self.play(self.camera.frame.animate.scale(1 / 0.95).shift(DOWN * 0.1), run_time=0.5)

        # -----------------------------------------------------------------
        # BEAT 4: 22.5s – 27.8s (The Shared Expert Secret with Continuous Golden Pulses)
        # "Plus one permanently active shared expert that never sleeps, capturing universal knowledge."
        # -----------------------------------------------------------------
        shared_card = RoundedRectangle(
            corner_radius=0.14, width=7.2, height=0.75,
            color="#F59E0B", fill_color="#78350F", fill_opacity=0.35, stroke_width=2.0
        ).shift(DOWN * 3.3)
        shared_icon = Text("★", font=FONT_HELVETICA, font_size=20, color="#FBBF24")
        shared_txt = Text("SHARED EXPERT #0 [ ALWAYS ACTIVE ]", font=FONT_HELVETICA, font_size=18, color="#FDE68A", weight=BOLD)
        shared_content = VGroup(shared_icon, shared_txt).arrange(RIGHT, buff=0.18).move_to(shared_card)
        shared_group = VGroup(shared_card, shared_content)

        self.play(FadeIn(shared_group, shift=UP * 0.4), run_time=0.8)
        self.play(
            Circumscribe(shared_card, color="#F59E0B", stroke_width=3.2, time_width=0.6),
            shared_card.animate.set_stroke(color="#FBBF24", width=2.8),
            run_time=1.2
        )
        # Continuous Golden Wave Emission (Eliminates static wait)
        pulse_ring1 = Circle(radius=0.8, color="#F59E0B", stroke_width=2.5, stroke_opacity=0.8).move_to(shared_card.get_center())
        pulse_ring2 = Circle(radius=1.2, color="#FBBF24", stroke_width=1.5, stroke_opacity=0.5).move_to(shared_card.get_center())
        self.play(
            pulse_ring1.animate.scale(3.2).set_stroke(opacity=0.0),
            pulse_ring2.animate.scale(2.8).set_stroke(opacity=0.0),
            shared_icon.animate.rotate(PI),
            run_time=1.8
        )
        self.play(
            Circumscribe(shared_card, color="#FBBF24", stroke_width=2.0),
            run_time=1.5
        )

        # -----------------------------------------------------------------
        # BEAT 5: 27.8s – 33.8s (Top-8 Sigmoid Router + Dynamic Laser Beams)
        # "When a token enters, a high-speed router scores affinity, dispatching to only the top 8 experts."
        # -----------------------------------------------------------------
        router_card = RoundedRectangle(
            corner_radius=0.14, width=7.0, height=0.70,
            color="#10B981", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.0
        ).shift(UP * 4.2)
        router_formula = VGroup(
            Text("Gate", font=FONT_HELVETICA, font_size=20, color="#10B981", weight=BOLD),
            Text("(x) = ", font=FONT_HELVETICA, font_size=20, color=WHITE),
            Text("Top-8", font=FONT_HELVETICA, font_size=20, color="#FACC15", weight=HEAVY),
            Text(" [ ", font=FONT_HELVETICA, font_size=22, color="#94A3B8"),
            Text("σ", font=FONT_HELVETICA, font_size=22, color="#38BDF8", slant=ITALIC, weight=BOLD),
            Text("( W·x + Bias ) ]", font=FONT_HELVETICA, font_size=20, color=WHITE),
        ).arrange(RIGHT, buff=0.06).move_to(router_card)
        router_group = VGroup(router_card, router_formula)

        token_capsule = RoundedRectangle(
            corner_radius=0.14, width=3.6, height=0.64,
            color="#00F0FF", fill_color="#0284C7", fill_opacity=0.35, stroke_width=2.0
        ).shift(UP * 3.1)
        token_txt = Text('Token: "intelligence"', font=FONT_HELVETICA, font_size=20, color=WHITE, weight=BOLD).move_to(token_capsule)
        token_group = VGroup(token_capsule, token_txt)

        # 8 Selected Expert indices across the 16x16 grid
        selected_indices = [22, 54, 87, 115, 142, 179, 215, 248]
        active_dots = []
        curved_lasers = []
        flash_anims = []

        for idx in selected_indices:
            pt = expert_dots[idx].get_center()
            active_dots.append(Dot(point=pt, radius=0.13, color="#10B981"))
            # Glowing curved laser beam
            laser = CurvedArrow(
                start_point=token_capsule.get_bottom(),
                end_point=pt,
                angle=0.18 if pt[0] > 0 else -0.18,
                color="#10B981",
                stroke_width=2.4,
                tip_length=0.16
            )
            curved_lasers.append(laser)
            flash_anims.append(Flash(pt, color="#10B981", line_length=0.22, num_lines=6, time_width=0.4))

        # Golden laser beam to shared expert
        shared_laser = CurvedArrow(
            start_point=token_capsule.get_bottom(),
            end_point=shared_card.get_top(),
            angle=-0.08,
            color="#F59E0B",
            stroke_width=2.4,
            tip_length=0.16
        )

        self.play(
            FadeIn(router_group, shift=DOWN * 0.3),
            FadeIn(token_group, shift=DOWN * 0.3),
            self.camera.frame.animate.scale(0.88).move_to(UP * 2.4),
            run_time=0.9
        )
        self.play(
            self.camera.frame.animate.scale(1 / 0.88).move_to(ORIGIN),
            LaggedStart(*[Create(a) for a in curved_lasers], lag_ratio=0.06),
            Create(shared_laser),
            *[Transform(expert_dots[idx], active_dots[i]) for i, idx in enumerate(selected_indices)],
            run_time=2.1
        )
        self.play(*flash_anims, run_time=0.8)
        # Dynamic Token Particle Flowing into Lasers (No static pause)
        token_particles = [
            Dot(point=token_capsule.get_bottom(), radius=0.07, color="#00F0FF")
            for _ in range(8)
        ]
        self.play(
            LaggedStart(
                *[MoveAlongPath(token_particles[i], curved_lasers[i]) for i in range(8)],
                lag_ratio=0.08
            ),
            Circumscribe(router_card, color="#FACC15", stroke_width=2.0),
            run_time=2.2
        )

        # -----------------------------------------------------------------
        # BEAT 6: 33.8s – 42.8s (The 37B Payoff & ZERO OVERLAP Clean Stage)
        # "The result? 671 billion parameters of intelligence, but only 37 billion active per token. 94 percent of compute, saved."
        # -----------------------------------------------------------------
        # CRITICAL FIX: Completely fade out all 256 expert dots, active dots, lasers, router, and shared box
        # so NOTHING overlaps with 37B or the typography!
        b5_fadeouts = [
            FadeOut(router_group), FadeOut(token_group), FadeOut(shared_group),
            FadeOut(shared_laser), FadeOut(moe_label_pill),
            FadeOut(experts_grid),  # Removes ALL 256 dots cleanly!
            *[FadeOut(a) for a in curved_lasers],
            *[FadeOut(p) for p in token_particles],
            *[FadeOut(expert_dots[idx]) for idx in selected_indices],
        ]

        active_hero_num = Text("37B", font=FONT_HELVETICA, font_size=130, color="#10B981", weight=HEAVY).shift(UP * 0.6)
        active_hero_label = Text("ACTIVE PARAMETERS PER TOKEN", font=FONT_HELVETICA, font_size=24, color=WHITE, weight=HEAVY).next_to(active_hero_num, DOWN, buff=0.3)
        active_hero_group = VGroup(active_hero_num, active_hero_label)

        # Animated Efficiency Gauge Progress Bar
        gauge_bg = RoundedRectangle(
            corner_radius=0.12, width=7.4, height=0.45,
            color="#1F2937", fill_color="#111827", fill_opacity=0.9, stroke_width=1.5
        ).shift(DOWN * 1.5)
        gauge_fill_tracker = ValueTracker(7.4)
        gauge_fill = always_redraw(
            lambda: RoundedRectangle(
                corner_radius=0.12, width=max(0.4, gauge_fill_tracker.get_value()), height=0.41,
                color="#10B981", fill_color="#059669", fill_opacity=0.85, stroke_width=0
            ).align_to(gauge_bg, LEFT)
        )
        gauge_label = Text("COMPUTE RETENTION: 5.5%", font=FONT_HELVETICA, font_size=15, color="#A7F3D0", weight=BOLD).move_to(gauge_bg)
        gauge_group = VGroup(gauge_bg, gauge_fill, gauge_label)

        # High-contrast efficiency equation badge
        efficiency_card = RoundedRectangle(
            corner_radius=0.16, width=7.6, height=1.0,
            color="#10B981", fill_color="#064E3B", fill_opacity=0.4, stroke_width=2.0
        ).shift(DOWN * 2.6)
        eff_left = Text("37B / 671B", font=FONT_HELVETICA, font_size=22, color="#A7F3D0", weight=BOLD)
        eff_arrow = Text("  ➔  ", font=FONT_HELVETICA, font_size=22, color=WHITE)
        eff_right = Text("⚡ 94.5% COMPUTE SAVED", font=FONT_HELVETICA, font_size=22, color="#FDE047", weight=HEAVY)
        eff_content = VGroup(eff_left, eff_arrow, eff_right).arrange(RIGHT, buff=0.08).move_to(efficiency_card)
        efficiency_group = VGroup(efficiency_card, eff_content)

        proof_pill = Text("✓ MATCHES MONOLITHIC FRONTIER ACCURACY", font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=BOLD).next_to(efficiency_card, DOWN, buff=0.25)

        # Clean Stage Entry: FadeOut previous elements, reveal 37B with shockwave
        self.play(*b5_fadeouts, run_time=0.8)
        self.play(
            FadeIn(active_hero_group, shift=UP * 0.3),
            Flash(active_hero_num, color="#10B981", line_length=0.4, num_lines=10, time_width=0.6),
            run_time=1.1
        )
        self.play(
            Circumscribe(active_hero_num, color="#10B981", stroke_width=3.5, time_width=0.7),
            FadeIn(gauge_bg), FadeIn(gauge_fill), FadeIn(gauge_label),
            run_time=1.1
        )
        # Gauge shrinks from 100% load to 5.5% load in real time!
        self.play(
            gauge_fill_tracker.animate.set_value(0.42),
            FadeIn(efficiency_group, shift=UP * 0.3),
            FadeIn(proof_pill, shift=UP * 0.3),
            run_time=1.8
        )
        # Continuous pulsing attention on the 94.5% savings
        self.play(
            Circumscribe(efficiency_card, color="#FDE047", stroke_width=3.5, time_width=0.6),
            self.camera.frame.animate.scale(0.97),
            run_time=1.8
        )
        self.play(
            Flash(efficiency_card, color="#FDE047", line_length=0.25, num_lines=8),
            run_time=1.9
        )
        self.play(self.camera.frame.animate.scale(1 / 0.97), run_time=0.5)

        # Transition out of Beats 3-6
        b6_all = VGroup(
            moe_header, hud_group,
            active_hero_group, gauge_group, efficiency_group, proof_pill
        )
        self.play(FadeOut(b6_all), run_time=0.5)

        # -----------------------------------------------------------------
        # BEAT 7: 42.8s – 46.89s (Minimalist Clean Tech Outro & Follow CTA)
        # "Follow The Model Verse for more deep architecture breakdowns like this."
        # -----------------------------------------------------------------
        outro_card = RoundedRectangle(
            corner_radius=0.22, width=7.6, height=7.4,
            color="#1F2937", fill_color="#0F172A", fill_opacity=0.92, stroke_width=2.0
        ).shift(UP * 0.2)

        outro_logo = Text("THE MODEL VERSE", font=FONT_HELVETICA, font_size=46, color="#10B981", weight=HEAVY).shift(UP * 2.2)
        outro_sub = Text("Deep AI Architecture Breakdowns", font=FONT_HELVETICA, font_size=20, color="#CBD5E1", weight=MEDIUM).next_to(outro_logo, DOWN, buff=0.25)

        # Interactive-Style Follow Button
        follow_btn_box = RoundedRectangle(
            corner_radius=0.18, width=6.4, height=1.1,
            color="#10B981", fill_color="#10B981", fill_opacity=0.25, stroke_width=2.5
        ).shift(DOWN * 0.15)
        follow_star = Text("✦", font=FONT_HELVETICA, font_size=26, color="#10B981")
        follow_label = Text("FOLLOW FOR MORE", font=FONT_HELVETICA, font_size=26, color=WHITE, weight=HEAVY)
        follow_content = VGroup(follow_star, follow_label).arrange(RIGHT, buff=0.2).move_to(follow_btn_box)
        follow_btn = VGroup(follow_btn_box, follow_content)

        url_card = VGroup(
            Text("themodelverse.in", font=FONT_HELVETICA, font_size=32, color="#34D399", weight=BOLD),
            Text("New Breakdown Videos Every Week", font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM)
        ).arrange(DOWN, buff=0.16).shift(DOWN * 2.0)

        outro_group = VGroup(outro_card, outro_logo, outro_sub, follow_btn, url_card)

        self.play(FadeIn(outro_card), FadeIn(outro_logo, shift=DOWN * 0.3), FadeIn(outro_sub), run_time=0.8)
        self.play(DrawBorderThenFill(follow_btn), FadeIn(url_card, shift=UP * 0.2), run_time=0.9)
        self.play(
            Circumscribe(follow_btn_box, color="#10B981", stroke_width=3.5, time_width=0.6),
            follow_star.animate.rotate(PI),
            run_time=1.2
        )
        self.play(
            Flash(follow_btn_box, color="#10B981", line_length=0.25, num_lines=8),
            run_time=1.19
        )
