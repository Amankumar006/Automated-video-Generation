import os
from manim import *

# 1080x1920 9:16 Vertical Video Configuration for Shorts / Reels
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.background_color = "#070A10"

class DeepSeekV3ProShort(Scene):
    def construct(self):
        # -----------------------------------------------------------------
        # BACKGROUND: Subtle 3B1B Mathematical Coordinate Grid
        # -----------------------------------------------------------------
        grid = NumberPlane(
            x_range=[-4.5, 4.5, 1],
            y_range=[-8, 8, 1],
            background_line_style={
                "stroke_color": "#1E293B",
                "stroke_width": 1,
                "stroke_opacity": 0.35,
            },
            axis_config={"stroke_opacity": 0},
        )
        self.add(grid)

        # Persistent Brand Watermark at top safe zone (y = 7.0)
        brand_tag = Text("THE MODEL VERSE", font_size=24, color="#38BDF8", weight=BOLD).shift(UP * 7.0)
        self.add(brand_tag)

        # -----------------------------------------------------------------
        # BEAT 1: 0.0s – 6.8s (Hook)
        # "How does DeepSeek-V3 deliver 671 billion parameters at a fraction of the cost of GPT-4?"
        # -----------------------------------------------------------------
        title = Text("DeepSeek-V3", font_size=68, color=WHITE, weight=BOLD).shift(UP * 5.5)
        
        # 671B Big Counter
        total_num = Text("671B", font_size=116, color="#38BDF8", weight=HEAVY).shift(UP * 2.2)
        total_label = Text("TOTAL PARAMETERS", font_size=28, color="#94A3B8", weight=BOLD).next_to(total_num, DOWN, buff=0.35)
        total_group = VGroup(total_num, total_label)

        hook_pill = RoundedRectangle(
            corner_radius=0.15,
            width=7.2,
            height=0.9,
            color="#0284C7",
            fill_color="#0369A1",
            fill_opacity=0.2,
            stroke_width=1.5
        ).shift(DOWN * 2.0)
        hook_pill_text = Text("FRONTIER INTELLIGENCE • FRACTION OF COST", font_size=21, color="#7DD3FC", weight=SEMIBOLD).move_to(hook_pill)
        hook_pill_group = VGroup(hook_pill, hook_pill_text)

        b1_group = VGroup(title, total_group, hook_pill_group)

        self.play(FadeIn(title, shift=DOWN * 0.4), run_time=0.8)
        self.play(DrawBorderThenFill(total_group), run_time=1.2)
        self.play(FadeIn(hook_pill_group, shift=UP * 0.4), run_time=0.8)
        self.wait(3.6)
        self.play(FadeOut(b1_group), run_time=0.4)

        # -----------------------------------------------------------------
        # BEAT 2: 6.8s – 13.5s (Dense Model Flaw)
        # "In a standard dense model, every single word forces all 671 billion parameters to calculate at once."
        # -----------------------------------------------------------------
        dense_label = Text("TRADITIONAL DENSE ARCHITECTURE", font_size=26, color="#F87171", weight=BOLD).shift(UP * 4.3)
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
        self.wait(3.1)
        self.play(FadeOut(VGroup(dense_label, dense_grid, b2_sub)), run_time=0.4)

        # -----------------------------------------------------------------
        # BEAT 3: 13.5s – 23.7s (Sparse MoE: 256 Experts + 1 Shared Expert)
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
        self.wait(6.1)

        # -----------------------------------------------------------------
        # BEAT 4: 23.7s – 29.8s (Top-8 Sigmoid Routing)
        # "When a token enters, an ultra-fast gating router scores affinity, dispatching to only the top 8 experts."
        # -----------------------------------------------------------------
        gate_box = RoundedRectangle(
            corner_radius=0.12,
            width=5.8,
            height=0.6,
            color="#38BDF8",
            fill_color="#0369A1",
            fill_opacity=0.25,
            stroke_width=1.5
        ).shift(UP * 4.2)
        gate_label = Text("TOP-8 SIGMOID AFFINITY GATE", font_size=20, color="#38BDF8", weight=BOLD).move_to(gate_box)
        gate_group = VGroup(gate_box, gate_label)

        token_rect = RoundedRectangle(
            corner_radius=0.14,
            width=3.8,
            height=0.75,
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
        cyan_arrows = []
        
        for idx in selected_indices:
            pt = expert_dots[idx].get_center()
            active_highlights.append(Dot(point=pt, radius=0.13, color="#00F0FF"))
            cyan_arrows.append(
                Arrow(
                    start=token_rect.get_bottom(),
                    end=pt,
                    buff=0.07,
                    color="#00F0FF",
                    stroke_width=2.4,
                    max_tip_length_to_length_ratio=0.14
                )
            )

        self.play(
            FadeIn(gate_group, shift=DOWN * 0.3),
            FadeIn(token_group, shift=DOWN * 0.3),
            run_time=0.8
        )
        self.play(
            LaggedStart(*[GrowArrow(a) for a in cyan_arrows], lag_ratio=0.08),
            *[Transform(expert_dots[idx], active_highlights[i]) for i, idx in enumerate(selected_indices)],
            run_time=1.6
        )
        self.wait(3.7)

        # -----------------------------------------------------------------
        # BEAT 5: 29.8s – 41.9s (The Result: 37B Active & 94% Compute Saved)
        # "The result? 671 billion parameters of total intelligence, but only 37 billion active per token.
        #  That slashes compute by 94 percent without losing reasoning power."
        # -----------------------------------------------------------------
        dim_anims = [a.animate.set_opacity(0.15) for a in cyan_arrows] + [
            expert_dots[i].animate.set_opacity(0.05)
            for i in range(256)
            if i not in selected_indices
        ]

        active_banner = Text("37B", font_size=116, color="#00F0FF", weight=HEAVY).shift(DOWN * 4.2)
        active_sub = Text("ACTIVE PARAMETERS PER TOKEN", font_size=24, color=WHITE, weight=BOLD).next_to(active_banner, DOWN, buff=0.25)
        savings_pill = Text("⚡ 94% COMPUTE SAVED", font_size=28, color="#4ADE80", weight=BOLD).next_to(active_sub, DOWN, buff=0.3)
        frontier_pill = Text("✓ MATCHES FRONTIER ACCURACY", font_size=20, color="#94A3B8", weight=SEMIBOLD).next_to(savings_pill, DOWN, buff=0.25)

        self.play(*dim_anims, run_time=0.8)
        self.play(FadeIn(VGroup(active_banner, active_sub), shift=UP * 0.4), run_time=1.2)
        self.play(Circumscribe(active_banner, color="#38BDF8", stroke_width=3, time_width=0.7), run_time=1.2)
        self.play(FadeIn(savings_pill, shift=UP * 0.3), FadeIn(frontier_pill, shift=UP * 0.3), run_time=1.0)
        self.wait(7.5)

        # Fade out Beat 3-5 elements cleanly
        self.play(
            FadeOut(experts_grid),
            FadeOut(shared_group),
            FadeOut(gate_group),
            FadeOut(token_group),
            FadeOut(active_banner),
            FadeOut(active_sub),
            FadeOut(savings_pill),
            FadeOut(frontier_pill),
            FadeOut(moe_title),
            FadeOut(hud),
            *[FadeOut(a) for a in cyan_arrows],
            run_time=0.4
        )

        # -----------------------------------------------------------------
        # BEAT 6: 41.9s – 46.0s (Outro & Call To Action)
        # "Follow The Model Verse for the architecture behind modern AI."
        # -----------------------------------------------------------------
        outro_title = Text("THE MODEL VERSE", font_size=52, color="#38BDF8", weight=HEAVY).shift(UP * 1.0)
        outro_tagline = Text("Deep AI Architecture Breakdowns", font_size=28, color=WHITE, weight=SEMIBOLD).next_to(outro_title, DOWN, buff=0.4)
        outro_url = Text("themodelverse.in", font_size=32, color="#00F0FF", weight=BOLD).next_to(outro_tagline, DOWN, buff=0.6)
        outro_group = VGroup(outro_title, outro_tagline, outro_url)

        self.play(FadeIn(outro_group, shift=UP * 0.5), run_time=0.8)
        self.play(Circumscribe(outro_url, color="#00F0FF", stroke_width=2.5, time_width=0.6), run_time=1.0)
        self.wait(2.3)
