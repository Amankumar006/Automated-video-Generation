import os
from manim import *

# 1080x1920 9:16 Vertical Video Configuration
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.background_color = "#070A10"

class DeepSeekV3Short(Scene):
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

        # -----------------------------------------------------------------
        # BEAT 1: 0.0s to 4.2s — "DeepSeek-V3 has 671 billion parameters."
        # -----------------------------------------------------------------
        brand_tag = Text("THE MODEL VERSE", font_size=24, color="#38BDF8", weight=BOLD).shift(UP * 6.8)
        title = Text("DeepSeek-V3", font_size=64, color=WHITE, weight=BOLD).next_to(brand_tag, DOWN, buff=0.35)
        
        # 671B Big Counter & Glowing Ring
        total_num = Text("671B", font_size=110, color="#38BDF8", weight=HEAVY).shift(UP * 2.2)
        total_label = Text("TOTAL PARAMETERS", font_size=28, color="#94A3B8", weight=BOLD).next_to(total_num, DOWN, buff=0.35)
        total_box = VGroup(total_num, total_label)

        self.play(FadeIn(brand_tag, shift=DOWN), FadeIn(title, shift=DOWN), run_time=0.8)
        self.play(DrawBorderThenFill(total_box), run_time=1.2)
        self.wait(2.5)

        # -----------------------------------------------------------------
        # BEAT 2: 4.2s to 10.5s — "But for each token, its gating network routes to only 8 out of 256 experts."
        # -----------------------------------------------------------------
        # Transition 671B to top HUD
        total_hud = Text("671B Total", font_size=28, color="#64748B", weight=SEMIBOLD).shift(UP * 5.4 + LEFT * 2.2)
        active_hud = Text("37B Active", font_size=28, color="#00F0FF", weight=BOLD).shift(UP * 5.4 + RIGHT * 2.2)
        divider = Text("|", font_size=28, color="#334155").shift(UP * 5.4)
        hud = VGroup(total_hud, divider, active_hud)

        # Gating formula pill (positioned cleanly ABOVE token)
        gate_box = RoundedRectangle(
            corner_radius=0.12,
            width=5.4,
            height=0.6,
            color="#38BDF8",
            fill_color="#0369A1",
            fill_opacity=0.2,
            stroke_width=1.5
        ).shift(UP * 4.3)
        gate_label = Text("TOP-8 SIGMOID AFFINITY GATE", font_size=20, color="#38BDF8", weight=BOLD).move_to(gate_box)
        gate_group = VGroup(gate_box, gate_label)

        # Token Node (below gate, above arrows)
        token_rect = RoundedRectangle(
            corner_radius=0.15,
            width=3.8,
            height=0.85,
            color="#00F0FF",
            fill_color="#0F172A",
            fill_opacity=0.95,
            stroke_width=2.5
        ).shift(UP * 3.1)
        token_label = Text('Token: "intelligence"', font_size=26, color=WHITE, weight=SEMIBOLD).move_to(token_rect)
        token_group = VGroup(token_rect, token_label)

        # 256 Expert Grid (16x16) positioned cleanly below token
        expert_dots = []
        for i in range(256):
            row = i // 16
            col = i % 16
            x = (col - 7.5) * 0.38
            y = 1.3 - (row * 0.26) # Spans Y = 1.3 down to -2.6
            dot = Dot(point=[x, y, 0], radius=0.06, color="#1E293B")
            expert_dots.append(dot)
        experts_grid = VGroup(*expert_dots)

        # 8 Selected experts
        selected_indices = [18, 45, 82, 107, 139, 178, 212, 245]
        active_highlights = []
        arrows = []
        
        for idx in selected_indices:
            pt = expert_dots[idx].get_center()
            # Glowing cyan dot
            active_highlights.append(Dot(point=pt, radius=0.13, color="#00F0FF"))
            # Dynamic arrow fanning from token to expert
            arrows.append(
                Arrow(
                    start=token_rect.get_bottom(),
                    end=pt,
                    buff=0.07,
                    color="#00F0FF",
                    stroke_width=2.5,
                    max_tip_length_to_length_ratio=0.14
                )
            )

        self.play(
            ReplacementTransform(total_box, hud),
            FadeIn(gate_group),
            FadeIn(token_group, shift=DOWN),
            run_time=1.2
        )
        self.play(Create(experts_grid, lag_ratio=0.002), run_time=1.0)

        # Gating dispatch: 8 glowing arrows shoot out and activate nodes
        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.08),
            *[Transform(expert_dots[idx], active_highlights[i]) for i, idx in enumerate(selected_indices)],
            run_time=1.8
        )
        self.wait(1.7)

        # -----------------------------------------------------------------
        # BEAT 3: 10.3s to 14.5s — "That is just 37 billion active parameters!"
        # -----------------------------------------------------------------
        # Dim out non-active experts & arrows
        dim_anims = [a.animate.set_opacity(0.15) for a in arrows] + [
            expert_dots[i].animate.set_opacity(0.06)
            for i in range(256)
            if i not in selected_indices
        ]
        
        # 37B Big Winner Banner in bottom safe zone (y = -3.8 to -5.5)
        active_banner = Text("37B", font_size=112, color="#00F0FF", weight=HEAVY).shift(DOWN * 3.8)
        active_sub = Text("ACTIVE PARAMETERS PER TOKEN", font_size=24, color=WHITE, weight=BOLD).next_to(active_banner, DOWN, buff=0.25)
        savings_pill = Text("⚡ 94% COMPUTE SAVED", font_size=26, color="#4ADE80", weight=BOLD).next_to(active_sub, DOWN, buff=0.3)
        final_group = VGroup(active_banner, active_sub, savings_pill)

        self.play(
            *dim_anims,
            FadeIn(final_group, shift=UP * 0.4),
            run_time=1.4
        )
        self.play(
            Circumscribe(active_banner, color="#38BDF8", stroke_width=3, time_width=0.7),
            run_time=1.0
        )
        self.wait(1.5)
