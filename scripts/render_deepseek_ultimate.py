import os
from manim import *

# 1080x1920 9:16 Vertical Video Configuration for Shorts / Reels
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.background_color = "#05070D"

class DeepSeekV3Ultimate(MovingCameraScene):
    def construct(self):
        # -----------------------------------------------------------------
        # BACKGROUND: Mathematical Cartesian Coordinate Plane
        # -----------------------------------------------------------------
        grid = NumberPlane(
            x_range=[-4.5, 4.5, 1],
            y_range=[-8, 8, 1],
            background_line_style={
                "stroke_color": "#1E293B",
                "stroke_width": 1,
                "stroke_opacity": 0.4,
            },
            axis_config={"stroke_opacity": 0},
        )
        self.add(grid)

        # Persistent Brand Watermark at top safe zone
        brand_tag = Text("THE MODEL VERSE", font_size=24, color="#38BDF8", weight=BOLD).shift(UP * 7.0)
        self.add(brand_tag)

        # -----------------------------------------------------------------
        # BEAT 1: 0.0s – 7.2s (Hook + Dynamic Number Count-up)
        # "How does DeepSeek-V3 deliver 671 billion parameters at a fraction of the cost of GPT-4?"
        # -----------------------------------------------------------------
        title = Text("DeepSeek-V3", font_size=68, color=WHITE, weight=BOLD).shift(UP * 5.4)
        
        # Live dynamic counter ticking up from 0 to 671
        counter_tracker = ValueTracker(0)
        total_num = always_redraw(
            lambda: Text(
                f"{int(counter_tracker.get_value())}B",
                font_size=116,
                color="#38BDF8",
                weight=HEAVY
            ).shift(UP * 2.2)
        )
        total_label = Text("TOTAL PARAMETERS", font_size=28, color="#94A3B8", weight=BOLD).shift(UP * 1.0)

        hook_pill = RoundedRectangle(
            corner_radius=0.15,
            width=7.4,
            height=0.85,
            color="#0284C7",
            fill_color="#0369A1",
            fill_opacity=0.25,
            stroke_width=1.5
        ).shift(DOWN * 1.8)
        hook_pill_text = Text("FRONTIER INTELLIGENCE • FRACTION OF COST", font_size=20, color="#7DD3FC", weight=SEMIBOLD).move_to(hook_pill)
        hook_pill_group = VGroup(hook_pill, hook_pill_text)

        b1_static = VGroup(title, total_label, hook_pill_group)

        self.play(FadeIn(title, shift=DOWN * 0.4), run_time=0.8)
        self.add(total_num)
        self.play(
            counter_tracker.animate.set_value(671),
            FadeIn(total_label, shift=UP * 0.2),
            run_time=2.0
        )
        self.play(FadeIn(hook_pill_group, shift=UP * 0.4), run_time=0.8)
        self.wait(2.8)
        self.play(FadeOut(b1_static), FadeOut(total_num), run_time=0.5)

        # -----------------------------------------------------------------
        # BEAT 2: 7.2s – 14.2s (Dense Inefficiency & Warning Pulse)
        # "In a standard dense model, every single word forces all 671 billion parameters to calculate at once."
        # -----------------------------------------------------------------
        dense_label = Text("TRADITIONAL DENSE ARCHITECTURE", font_size=26, color="#F87171", weight=BOLD).shift(UP * 4.3)
        
        # 8x8 dense neural array
        dense_dots = []
        for i in range(64):
            r = i // 8
            c = i % 8
            x = (c - 3.5) * 0.65
            y = 2.4 - (r * 0.65)
            dot = Dot(point=[x, y, 0], radius=0.12, color="#EF4444")
            dense_dots.append(dot)
        dense_grid = VGroup(*dense_dots)

        overhead_pill = Text("⚠️ 100% OF NEURONS FIRE PER TOKEN", font_size=24, color="#EF4444", weight=BOLD).shift(DOWN * 3.8)
        overhead_sub = Text("Massive VRAM & Compute Inefficiency", font_size=22, color="#94A3B8").next_to(overhead_pill, DOWN, buff=0.25)
        b2_sub = VGroup(overhead_pill, overhead_sub)

        self.play(FadeIn(dense_label), FadeIn(dense_grid), run_time=0.8)
        self.play(
            dense_grid.animate.set_color("#FF6B6B"),
            FadeIn(b2_sub, shift=UP * 0.3),
            run_time=1.2
        )
        self.play(
            Circumscribe(dense_grid, color="#EF4444", stroke_width=3, time_width=0.8),
            run_time=1.2
        )
        self.wait(3.3)
        self.play(FadeOut(VGroup(dense_label, dense_grid, b2_sub)), run_time=0.4)

        # -----------------------------------------------------------------
        # BEAT 3: 14.2s – 24.5s (Sparse MoE: 256 Experts + 1 Shared Expert)
        # "DeepSeek flips this on its head with a Sparse Mixture of Experts.
        #  It breaks the model into 256 specialized sub-networks, plus one permanently active shared expert."
        # -----------------------------------------------------------------
        moe_title = Text("DeepSeek Sparse MoE", font_size=42, color=WHITE, weight=BOLD).shift(UP * 5.7)
        hud_total = Text("671B Capacity", font_size=24, color="#64748B", weight=SEMIBOLD).shift(UP * 5.0 + LEFT * 2.2)
        hud_divider = Text("|", font_size=24, color="#334155").shift(UP * 5.0)
        hud_active = Text("37B Active", font_size=24, color="#00F0FF", weight=BOLD).shift(UP * 5.0 + RIGHT * 2.2)
        hud = VGroup(hud_total, hud_divider, hud_active)

        # 256 Expert Grid (16x16)
        expert_dots = []
        for i in range(256):
            row = i // 16
            col = i % 16
            x = (col - 7.5) * 0.36
            y = 1.6 - (row * 0.25) # Y spans 1.6 down to -2.15
            dot = Dot(point=[x, y, 0], radius=0.055, color="#1E293B")
            expert_dots.append(dot)
        experts_grid = VGroup(*expert_dots)

        # 1 Shared Expert placed with distinct golden highlight
        shared_box = RoundedRectangle(
            corner_radius=0.12,
            width=6.8,
            height=0.65,
            color="#F59E0B",
            fill_color="#78350F",
            fill_opacity=0.3,
            stroke_width=1.5
        ).shift(DOWN * 2.8)
        shared_label = Text("★ 1 SHARED EXPERT (ALWAYS ACTIVE)", font_size=20, color="#FBBF24", weight=BOLD).move_to(shared_box)
        shared_group = VGroup(shared_box, shared_label)

        self.play(FadeIn(moe_title), FadeIn(hud), run_time=0.8)
        self.play(Create(experts_grid, lag_ratio=0.002), run_time=1.5)
        self.play(FadeIn(shared_group, shift=UP * 0.3), run_time=0.8)
        self.play(Circumscribe(shared_box, color="#F59E0B", stroke_width=2.5, time_width=0.6), run_time=1.0)
        self.wait(5.8)

        # -----------------------------------------------------------------
        # BEAT 4: 24.5s – 31.0s (Top-8 Sigmoid Router + Camera Zoom + Curved Beziers)
        # "When a token enters, an ultra-fast gating router scores affinity, dispatching to only the top 8 experts."
        # -----------------------------------------------------------------
        # Mathematical Gating Formula (Color-coded typographically)
        gate_text = VGroup(
            Text("Gate", font_size=22, color="#00F0FF", weight=BOLD),
            Text("(x) = ", font_size=22, color=WHITE),
            Text("Top-8", font_size=22, color="#FACC15", weight=BOLD),
            Text(" [ ", font_size=26, color="#94A3B8"),
            Text("σ", font_size=24, color="#38BDF8", slant=ITALIC, weight=BOLD),
            Text("( W", font_size=22, color=WHITE),
            Text("g", font_size=16, color=WHITE).shift(DOWN * 0.08),
            Text("·x + b", font_size=22, color=WHITE),
            Text("i", font_size=16, color=WHITE).shift(DOWN * 0.08),
            Text(" ) ]", font_size=26, color="#94A3B8"),
        ).arrange(RIGHT, buff=0.06).shift(UP * 4.2)

        gate_bg = RoundedRectangle(
            corner_radius=0.12,
            width=6.6,
            height=0.65,
            color="#38BDF8",
            fill_color="#0369A1",
            fill_opacity=0.25,
            stroke_width=1.5
        ).move_to(gate_text)
        gate_group = VGroup(gate_bg, gate_text)

        token_rect = RoundedRectangle(
            corner_radius=0.14,
            width=3.8,
            height=0.72,
            color="#00F0FF",
            fill_color="#0F172A",
            fill_opacity=0.95,
            stroke_width=2.5
        ).shift(UP * 3.1)
        token_label = Text('Token: "intelligence"', font_size=24, color=WHITE, weight=SEMIBOLD).move_to(token_rect)
        token_group = VGroup(token_rect, token_label)

        # 8 Selected experts across the 16x16 grid
        selected_indices = [18, 45, 82, 107, 139, 178, 212, 245]
        active_highlights = []
        curved_arrows = []
        flash_anims = []
        
        for idx in selected_indices:
            pt = expert_dots[idx].get_center()
            active_highlights.append(Dot(point=pt, radius=0.13, color="#00F0FF"))
            # Curved Bezier spline routing into expert
            arrow = CurvedArrow(
                start_point=token_rect.get_bottom(),
                end_point=pt,
                angle=0.15 if pt[0] > 0 else -0.15,
                color="#00F0FF",
                stroke_width=2.2,
                tip_length=0.18
            )
            curved_arrows.append(arrow)
            flash_anims.append(Flash(pt, color="#00F0FF", line_length=0.2, num_lines=6, time_width=0.4))

        # Golden arrow to shared expert
        shared_arrow = CurvedArrow(
            start_point=token_rect.get_bottom(),
            end_point=shared_box.get_top(),
            angle=-0.1,
            color="#F59E0B",
            stroke_width=2.2,
            tip_length=0.18
        )

        self.play(
            FadeIn(gate_group, shift=DOWN * 0.3),
            FadeIn(token_group, shift=DOWN * 0.3),
            run_time=0.8
        )
        # Dynamic Camera Zoom into Token & Gating Router
        self.play(
            self.camera.frame.animate.scale(0.85).move_to(UP * 2.8),
            run_time=0.8
        )
        # Pull camera back out as curved arrows fan across the pool
        self.play(
            self.camera.frame.animate.scale(1 / 0.85).move_to(ORIGIN),
            LaggedStart(*[Create(a) for a in curved_arrows], lag_ratio=0.08),
            Create(shared_arrow),
            *[Transform(expert_dots[idx], active_highlights[i]) for i, idx in enumerate(selected_indices)],
            run_time=2.0
        )
        self.play(*flash_anims, run_time=0.8)
        self.wait(1.5)

        # -----------------------------------------------------------------
        # BEAT 5: 31.0s – 42.5s (The 37B Payoff & Efficiency Equation)
        # "The result? 671 billion parameters of total intelligence, but only 37 billion active per token.
        #  That slashes compute by 94 percent without losing reasoning power."
        # -----------------------------------------------------------------
        dim_anims = [a.animate.set_opacity(0.12) for a in curved_arrows] + [
            shared_arrow.animate.set_opacity(0.2)
        ] + [
            expert_dots[i].animate.set_opacity(0.04)
            for i in range(256)
            if i not in selected_indices
        ]

        active_banner = Text("37B", font_size=116, color="#00F0FF", weight=HEAVY).shift(DOWN * 4.2)
        active_sub = Text("ACTIVE PARAMETERS PER TOKEN", font_size=24, color=WHITE, weight=BOLD).next_to(active_banner, DOWN, buff=0.25)
        
        # Mathematical efficiency equation
        math_equation = VGroup(
            Text("37B", font_size=26, color="#00F0FF", weight=BOLD),
            Text(" / ", font_size=26, color="#64748B"),
            Text("671B", font_size=26, color="#38BDF8", weight=BOLD),
            Text(" ≈ ", font_size=26, color=WHITE),
            Text("5.5% Load", font_size=26, color="#F59E0B", weight=BOLD),
            Text("  ➔  ", font_size=26, color=WHITE),
            Text("⚡ 94.5% SAVED", font_size=28, color="#4ADE80", weight=HEAVY),
        ).arrange(RIGHT, buff=0.08).next_to(active_sub, DOWN, buff=0.3)

        frontier_pill = Text("✓ MATCHES FRONTIER ACCURACY", font_size=20, color="#94A3B8", weight=SEMIBOLD).next_to(math_equation, DOWN, buff=0.25)

        self.play(*dim_anims, run_time=0.8)
        self.play(FadeIn(VGroup(active_banner, active_sub), shift=UP * 0.4), run_time=1.2)
        self.play(Circumscribe(active_banner, color="#38BDF8", stroke_width=3, time_width=0.7), run_time=1.2)
        self.play(FadeIn(math_equation, shift=UP * 0.3), FadeIn(frontier_pill, shift=UP * 0.3), run_time=1.0)
        self.wait(7.0)

        # Clean Transition Out of Beat 3-5
        self.play(
            FadeOut(experts_grid),
            FadeOut(shared_group),
            FadeOut(gate_group),
            FadeOut(token_group),
            FadeOut(active_banner),
            FadeOut(active_sub),
            FadeOut(math_equation),
            FadeOut(frontier_pill),
            FadeOut(moe_title),
            FadeOut(hud),
            FadeOut(shared_arrow),
            *[FadeOut(a) for a in curved_arrows],
            run_time=0.4
        )

        # -----------------------------------------------------------------
        # BEAT 6: 42.5s – 46.5s (Outro & High-Converting Call To Action)
        # "Follow The Model Verse for more videos like this."
        # -----------------------------------------------------------------
        outro_title = Text("THE MODEL VERSE", font_size=56, color="#38BDF8", weight=HEAVY).shift(UP * 2.2)
        outro_tagline = Text("Deep AI Architecture Breakdowns", font_size=24, color="#94A3B8", weight=SEMIBOLD).next_to(outro_title, DOWN, buff=0.3)

        # High-visibility Follow button
        follow_box = RoundedRectangle(
            corner_radius=0.18,
            width=6.4,
            height=1.05,
            color="#00F0FF",
            fill_color="#0891B2",
            fill_opacity=0.3,
            stroke_width=2.5
        ).shift(DOWN * 0.1)
        follow_icon = Text("✦", font_size=28, color="#00F0FF")
        follow_text = Text("FOLLOW FOR MORE", font_size=28, color=WHITE, weight=HEAVY)
        follow_btn_content = VGroup(follow_icon, follow_text).arrange(RIGHT, buff=0.22).move_to(follow_box)
        follow_button = VGroup(follow_box, follow_btn_content)

        outro_url = Text("themodelverse.in", font_size=32, color="#00F0FF", weight=BOLD).shift(DOWN * 1.8)
        outro_sub = Text("More Breakdowns Like This Every Week", font_size=20, color="#64748B", weight=SEMIBOLD).next_to(outro_url, DOWN, buff=0.25)

        self.play(FadeIn(outro_title, shift=DOWN * 0.3), FadeIn(outro_tagline), run_time=0.8)
        self.play(DrawBorderThenFill(follow_button), run_time=1.0)
        self.play(
            Circumscribe(follow_box, color="#00F0FF", stroke_width=3.5, time_width=0.6),
            FadeIn(outro_url, shift=UP * 0.2),
            FadeIn(outro_sub, shift=UP * 0.2),
            run_time=1.0
        )
        self.wait(1.8)
