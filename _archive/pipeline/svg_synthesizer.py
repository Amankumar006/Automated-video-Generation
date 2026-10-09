"""
The Model Verse — Dynamic Beat Vector & SVG Synthesizer (Visual Engine 3.5)
Generates bespoke, script-relevant vector diagrams and SVG visual assets for every
individual beat of a short video, eliminating repetitive canned templates.
Combines Gemini generative vector synthesis with deterministic procedural fallbacks.
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BEAT_SVGS_DIR = PROJECT_ROOT / "public" / "beat_svgs"
BEAT_SVGS_DIR.mkdir(parents=True, exist_ok=True)


class SVGSynthesizer:
    """
    Synthesizes custom vector SVG assets tailored to each beat's narrative script,
    everyday physical analogies, and Subject-Verb-Object (SVO) visual actions.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            try:
                from pipeline.config import WORKSPACE_ROOT
                from dotenv import load_dotenv
                load_dotenv(WORKSPACE_ROOT / ".env")
                self.api_key = os.environ.get("GEMINI_API_KEY")
            except Exception:
                pass

        self.candidate_models = [
            "gemini-3.8-flash",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash",
            "gemini-flash-latest"
        ]

    def synthesize_beat_svg(
        self,
        beat: Dict[str, Any],
        topic: str,
        spec_id: str,
        beat_id: int,
        force_regenerate: bool = False
    ) -> Path:
        """
        Synthesizes or retrieves a bespoke vector SVG for a specific beat.
        Guarantees a clean, valid vector SVG file on disk.
        """
        clean_spec = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec_id).lower()
        target_path = BEAT_SVGS_DIR / f"{clean_spec}_beat{beat_id}.svg"

        if target_path.exists() and not force_regenerate and target_path.stat().st_size > 100:
            return target_path

        # 1. Attempt Gemini Generative Vector Synthesis if API is active
        svg_code = None
        if self.api_key:
            try:
                svg_code = self._generate_ai_vector_svg(beat, topic)
            except Exception as e:
                print(f"   ℹ️ AI SVG generator fallback for beat {beat_id}: {e}")

        # 2. Fallback to Deterministic Procedural Vector Generation
        if not svg_code or not self._validate_svg(svg_code):
            svg_code = self._generate_procedural_vector_svg(beat, topic)

        # 3. Clean and save SVG
        cleaned_svg = self._clean_chalkboard_svg(svg_code)
        target_path.write_text(cleaned_svg, encoding="utf-8")
        print(f"   🎨 Generated bespoke vector SVG for Beat {beat_id}: {target_path.name} ({len(cleaned_svg)} bytes)")
        return target_path

    def _generate_ai_vector_svg(self, beat: Dict[str, Any], topic: str) -> Optional[str]:
        """Calls Gemini to generate pure vector SVG XML for the beat analogy."""
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        b_text = beat.get("text", "")
        v_focus = beat.get("visual_focus", "")
        svo = beat.get("svo_action", {})
        analogy = beat.get("everyday_analogy", "")

        prompt = f"""You are the Lead Visual Designer for 'The Model Verse' 3Blue1Brown-style animations.
Create clean, valid, standalone SVG XML code that visually diagrams this SPECIFIC concept and physical analogy.
The diagram MUST be UNIQUE to this exact paper concept — never reuse generic network graphs, generic circles, or abstract arrows.

Topic: {topic}
Voiceover Narration: "{b_text}"
Visual Focus: "{v_focus}"
Physical Analogy: "{analogy}"
SVO Entities: Subject='{svo.get("subject", "")}', Action='{svo.get("action_verb", "")}', Object='{svo.get("direct_object", "")}'

CRITICAL DESIGN & TECHNICAL RULES:
1. Canvas: <svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
2. USE THE FULL 600x600 CANVAS. Fill the entire viewport with the diagram — no tiny centered icons surrounded by empty space!
3. Visual Style: Signature 3Blue1Brown chalkboard vector geometry with bold strokes (stroke-width 3-6px).
4. Elements allowed: ONLY <path>, <rect>, <circle>, <ellipse>, <polygon>, <polyline>, <line>, <g>, <defs>, <linearGradient>.
5. STRICT PROHIBITION: DO NOT USE ANY <text> TAGS! (All text is rendered natively by Manim over the diagram).
6. Colors to use:
   - Neon Cyan: #38BDF8
   - Mint Green: #34D399
   - Amber / Gold: #F59E0B
   - Coral / Crimson: #EF4444
   - Violet: #A855F7
   - Chalk White: #F8FAFC
   - Muted Slate: #475569
7. Depict the ACTUAL physical metaphor from the narration. If it describes spatial memory, draw a 3D grid of memory cells. If it describes camera rays, draw perspective projection lines. If it describes streaming video, draw filmstrip frames flowing into a pipeline. BE LITERAL AND SPECIFIC.
8. Make the diagram LARGE, BOLD, and DETAILED with at least 15-20 distinct SVG elements. No tiny diagrams!
9. Output ONLY the raw <svg>...</svg> XML markup. No explanation, no markdown ticks."""

        for model_name in self.candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt)
                if res and res.text:
                    txt = res.text.strip()
                    if "```xml" in txt:
                        txt = txt.split("```xml")[1].split("```")[0].strip()
                    elif "```svg" in txt:
                        txt = txt.split("```svg")[1].split("```")[0].strip()
                    elif "```" in txt:
                        txt = txt.split("```")[1].split("```")[0].strip()
                    if "<svg" in txt and "</svg>" in txt:
                        return txt
            except Exception:
                continue
        return None

    def _generate_procedural_vector_svg(self, beat: Dict[str, Any], topic: str) -> str:
        """
        Deterministic, procedural vector graphics generator.
        Selects from an extensive suite of bespoke 3Blue1Brown vector blueprints based on keywords.
        """
        text = (beat.get("text", "") + " " + beat.get("visual_focus", "") + " " + str(beat.get("everyday_analogy", ""))).lower()

        if any(k in text for k in ["smoothie", "blend", "fruit", "strawberr", "puree"]):
            return self._build_blender_vs_fruit_svg()
        elif any(k in text for k in ["flicker", "portrait", "sketch", "outline", "contour", "wireframe", "dots"]):
            return self._build_flickering_contour_svg()
        elif any(k in text for k in ["split", "dual", "track", "bifurcat", "two path", "semantic and geometric"]):
            return self._build_bifurcated_dual_track_svg()
        elif any(k in text for k in ["barrier", "penalty", "bleed", "prevent", "isolate", "separate paths", "forcefield"]):
            return self._build_anti_bleed_barrier_svg()
        elif any(k in text for k in ["lego", "voxel", "quantiz", "block", "grid", "pixelat", "chunk"]):
            return self._build_lego_quantization_svg()
        elif any(k in text for k in ["puzzle", "jigsaw", "snap", "broken", "interlock"]):
            return self._build_jigsaw_puzzle_svg()
        elif any(k in text for k in ["bottleneck", "highway", "toll", "choke", "narrow", "express"]):
            return self._build_highway_bottleneck_svg()
        elif any(k in text for k in ["field", "flow", "velocity", "streamline", "trajectory", "vector field"]):
            return self._build_vector_field_streamlines_svg()
        elif any(k in text for k in ["memory", "cache", "kv", "buffer", "rack", "evict"]):
            return self._build_memory_hierarchy_racks_svg()
        elif any(k in text for k in ["pareto", "frontier", "tradeoff", "versus", "comparison", "speedup"]):
            return self._build_pareto_frontier_comparison_svg()
        else:
            return self._build_neural_semantic_network_svg()

    # --- Procedural SVG Blueprints (3Blue1Brown Chalkboard Standard) ---

    def _build_blender_vs_fruit_svg(self) -> str:
        """Blender vessel pureeing mixture on left vs distinct whole preserved fruits on right."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Left Side: Blender Pitcher with swirl fluid -->
  <path d="M 120 120 L 220 120 L 200 300 L 140 300 Z" fill="#1E293B" stroke="#38BDF8" stroke-width="4" stroke-linejoin="round"/>
  <rect x="135" y="300" width="70" height="24" rx="4" fill="#334155" stroke="#38BDF8" stroke-width="3"/>
  <path d="M 140 220 Q 170 190 200 230 Q 180 270 145 250 Z" fill="#F59E0B" fill-opacity="0.8"/>
  <path d="M 155 240 Q 170 210 185 240" fill="none" stroke="#EF4444" stroke-width="3"/>
  <circle cx="170" cy="205" r="4" fill="#38BDF8"/>
  <circle cx="185" cy="225" r="3" fill="#F8FAFC"/>
  <!-- Middle Transition Arrow -->
  <path d="M 250 200 L 330 200" stroke="#94A3B8" stroke-width="4" stroke-dasharray="6,6"/>
  <polygon points="340,200 325,190 325,210" fill="#38BDF8"/>
  <line x1="290" y1="160" x2="290" y2="240" stroke="#EF4444" stroke-width="3" stroke-dasharray="4,4"/>
  <!-- Right Side: Preserved Individual Strawberries / Fruit Shapes -->
  <g transform="translate(380, 130)">
    <path d="M 40 10 C 10 30 10 70 40 90 C 70 70 70 30 40 10 Z" fill="#EF4444" stroke="#F8FAFC" stroke-width="3"/>
    <path d="M 30 10 L 40 0 L 50 10" stroke="#34D399" stroke-width="4" fill="none"/>
    <circle cx="32" cy="40" r="2.5" fill="#F8FAFC"/>
    <circle cx="48" cy="45" r="2.5" fill="#F8FAFC"/>
    <circle cx="40" cy="65" r="2.5" fill="#F8FAFC"/>
  </g>
  <g transform="translate(460, 210)">
    <path d="M 40 10 C 10 30 10 70 40 90 C 70 70 70 30 40 10 Z" fill="#EF4444" stroke="#34D399" stroke-width="3"/>
    <path d="M 30 10 L 40 0 L 50 10" stroke="#34D399" stroke-width="4" fill="none"/>
    <circle cx="32" cy="40" r="2.5" fill="#F8FAFC"/>
    <circle cx="48" cy="45" r="2.5" fill="#F8FAFC"/>
    <circle cx="40" cy="65" r="2.5" fill="#F8FAFC"/>
  </g>
</svg>"""

    def _build_flickering_contour_svg(self) -> str:
        """Flickering noisy wave/point cloud transitioning into a crisp wireframe contour."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Left Side: Noisy Flickering Cloud -->
  <rect x="60" y="80" width="200" height="240" rx="16" fill="#1E293B" stroke="#475569" stroke-width="2.5" stroke-dasharray="6,6"/>
  <circle cx="110" cy="150" r="6" fill="#EF4444" fill-opacity="0.8"/>
  <circle cx="170" cy="130" r="8" fill="#F59E0B" fill-opacity="0.7"/>
  <circle cx="210" cy="190" r="5" fill="#EF4444" fill-opacity="0.9"/>
  <circle cx="130" cy="240" r="7" fill="#F59E0B" fill-opacity="0.8"/>
  <circle cx="180" cy="270" r="6" fill="#EF4444" fill-opacity="0.7"/>
  <path d="M 90 200 Q 150 160 220 230" stroke="#EF4444" stroke-width="3" stroke-dasharray="4,4" fill="none"/>
  <!-- Central Dynamic Transform Conduit -->
  <path d="M 280 200 L 330 200" stroke="#38BDF8" stroke-width="4"/>
  <polygon points="340,200 326,192 326,208" fill="#38BDF8"/>
  <!-- Right Side: Sharp Geometric Connect-the-Dots Wireframe -->
  <rect x="350" y="80" width="200" height="240" rx="16" fill="#0F172A" stroke="#34D399" stroke-width="3"/>
  <polygon points="450,110 510,160 490,260 410,260 390,160" fill="#064E3B" fill-opacity="0.5" stroke="#34D399" stroke-width="4"/>
  <circle cx="450" cy="110" r="6" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="510" cy="160" r="6" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="490" cy="260" r="6" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="410" cy="260" r="6" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="390" cy="160" r="6" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <!-- Center Anchor Crosshair -->
  <line x1="450" y1="180" x2="450" y2="200" stroke="#F59E0B" stroke-width="2"/>
  <line x1="440" y1="190" x2="460" y2="190" stroke="#F59E0B" stroke-width="2"/>
</svg>"""

    def _build_bifurcated_dual_track_svg(self) -> str:
        """Unified input conduit splitting into Upper Semantic Track and Lower Geometric Track."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Input Conduit -->
  <rect x="40" y="165" width="100" height="70" rx="12" fill="#1E293B" stroke="#38BDF8" stroke-width="3.5"/>
  <circle cx="70" cy="200" r="10" fill="#38BDF8"/>
  <circle cx="105" cy="200" r="10" fill="#A855F7"/>
  <!-- Bifurcation Fork -->
  <path d="M 140 180 C 200 180 220 110 280 110 L 320 110" fill="none" stroke="#A855F7" stroke-width="5"/>
  <polygon points="330,110 318,103 318,117" fill="#A855F7"/>
  <path d="M 140 220 C 200 220 220 290 280 290 L 320 290" fill="none" stroke="#34D399" stroke-width="5"/>
  <polygon points="330,290 318,283 318,297" fill="#34D399"/>
  <!-- Track 1 (Top): Semantic Concept Cloud -->
  <rect x="330" y="65" width="220" height="90" rx="14" fill="#1E1B4B" stroke="#A855F7" stroke-width="3"/>
  <circle cx="370" cy="110" r="18" fill="#6B21A8" fill-opacity="0.7"/>
  <circle cx="410" cy="100" r="22" fill="#7C3AED" fill-opacity="0.8"/>
  <circle cx="450" cy="112" r="16" fill="#6B21A8" fill-opacity="0.7"/>
  <circle cx="490" cy="105" r="14" fill="#8B5CF6" fill-opacity="0.9"/>
  <!-- Track 2 (Bottom): Geometric Depth & Contour Grid -->
  <rect x="330" y="245" width="220" height="90" rx="14" fill="#064E3B" stroke="#34D399" stroke-width="3"/>
  <line x1="350" y1="265" x2="530" y2="265" stroke="#34D399" stroke-width="2"/>
  <line x1="350" y1="290" x2="530" y2="290" stroke="#34D399" stroke-width="2"/>
  <line x1="350" y1="315" x2="530" y2="315" stroke="#34D399" stroke-width="2"/>
  <line x1="390" y1="250" x2="370" y2="330" stroke="#38BDF8" stroke-width="2.5"/>
  <line x1="440" y1="250" x2="420" y2="330" stroke="#38BDF8" stroke-width="2.5"/>
  <line x1="490" y1="250" x2="470" y2="330" stroke="#38BDF8" stroke-width="2.5"/>
</svg>"""

    def _build_anti_bleed_barrier_svg(self) -> str:
        """Two parallel running conduits separated by a glowing repulsion energy barrier."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Upper Channel (Semantic) -->
  <rect x="60" y="70" width="480" height="90" rx="12" fill="#1E1B4B" stroke="#818CF8" stroke-width="3"/>
  <path d="M 80 115 L 520 115" stroke="#A855F7" stroke-width="4" stroke-dasharray="10,6"/>
  <circle cx="160" cy="115" r="10" fill="#38BDF8"/>
  <circle cx="300" cy="115" r="10" fill="#A855F7"/>
  <circle cx="440" cy="115" r="10" fill="#38BDF8"/>
  <!-- Central Anti-Bleed Energy Barrier -->
  <line x1="60" y1="200" x2="540" y2="200" stroke="#EF4444" stroke-width="6"/>
  <line x1="60" y1="200" x2="540" y2="200" stroke="#F87171" stroke-width="2" stroke-dasharray="14,8"/>
  <!-- Deflection / Repulsion Field Vectors -->
  <polygon points="180,185 190,175 190,195" fill="#EF4444"/>
  <polygon points="180,215 190,205 190,225" fill="#EF4444"/>
  <polygon points="320,185 330,175 330,195" fill="#EF4444"/>
  <polygon points="320,215 330,205 330,225" fill="#EF4444"/>
  <polygon points="460,185 470,175 470,195" fill="#EF4444"/>
  <polygon points="460,215 470,205 470,225" fill="#EF4444"/>
  <!-- Lower Channel (Geometric) -->
  <rect x="60" y="240" width="480" height="90" rx="12" fill="#064E3B" stroke="#34D399" stroke-width="3"/>
  <path d="M 80 285 L 520 285" stroke="#34D399" stroke-width="4" stroke-dasharray="10,6"/>
  <polygon points="160,275 170,295 150,295" fill="#34D399"/>
  <polygon points="300,275 310,295 290,295" fill="#F59E0B"/>
  <polygon points="440,275 450,295 430,295" fill="#34D399"/>
</svg>"""

    def _build_lego_quantization_svg(self) -> str:
        """Smooth analog curve on left being quantized into rigid Lego / voxel blocks on right."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Left Side: Smooth Continuous Wave -->
  <rect x="50" y="80" width="220" height="240" rx="14" fill="#0F172A" stroke="#38BDF8" stroke-width="2.5"/>
  <path d="M 65 240 Q 110 100 160 200 T 255 160" fill="none" stroke="#38BDF8" stroke-width="5"/>
  <!-- Middle Transition Arrow -->
  <path d="M 285 200 L 320 200" stroke="#F59E0B" stroke-width="4"/>
  <polygon points="330,200 318,193 318,207" fill="#F59E0B"/>
  <!-- Right Side: Discrete Lego Blocks / Voxelized Step -->
  <rect x="340" y="80" width="220" height="240" rx="14" fill="#1E293B" stroke="#F59E0B" stroke-width="3"/>
  <!-- Stepped Rectangles representing Lego quantization -->
  <rect x="360" y="220" width="30" height="60" fill="#EF4444" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="375" cy="216" r="4" fill="#EF4444" stroke="#F8FAFC" stroke-width="1.5"/>
  <rect x="390" y="160" width="30" height="120" fill="#F59E0B" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="405" cy="156" r="4" fill="#F59E0B" stroke="#F8FAFC" stroke-width="1.5"/>
  <rect x="420" y="120" width="30" height="160" fill="#34D399" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="435" cy="116" r="4" fill="#34D399" stroke="#F8FAFC" stroke-width="1.5"/>
  <rect x="450" y="170" width="30" height="110" fill="#38BDF8" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="465" cy="166" r="4" fill="#38BDF8" stroke="#F8FAFC" stroke-width="1.5"/>
  <rect x="480" y="210" width="30" height="70" fill="#A855F7" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="495" cy="206" r="4" fill="#A855F7" stroke="#F8FAFC" stroke-width="1.5"/>
</svg>"""

    def _build_jigsaw_puzzle_svg(self) -> str:
        """Broken puzzle pieces snapping together into a coherent trajectory."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Piece 1 (Cyan) -->
  <path d="M 120 140 L 200 140 C 210 120 230 120 240 140 L 260 140 L 260 220 L 200 220 L 120 220 Z" fill="#1E293B" stroke="#38BDF8" stroke-width="4"/>
  <circle cx="190" cy="180" r="8" fill="#38BDF8"/>
  <!-- Piece 2 (Amber) Interlocking -->
  <path d="M 275 140 L 350 140 L 350 220 C 330 230 330 250 350 260 L 350 280 L 275 280 L 275 220 Z" fill="#1E293B" stroke="#F59E0B" stroke-width="4"/>
  <circle cx="312" cy="210" r="8" fill="#F59E0B"/>
  <!-- Snap Connection Lightning / Pulse -->
  <path d="M 265 170 L 272 180 L 263 190 L 270 200" stroke="#34D399" stroke-width="4" fill="none"/>
  <!-- Coherent Trajectory Arrow piercing through -->
  <path d="M 80 180 L 480 180" stroke="#34D399" stroke-width="5" stroke-dasharray="12,8"/>
  <polygon points="500,180 482,170 482,190" fill="#34D399"/>
</svg>"""

    def _build_highway_bottleneck_svg(self) -> str:
        """Multi-lane throughput bottlenecking into single choke point then express lane."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Multi-Lane Inlet -->
  <path d="M 60 90 L 220 160 L 220 240 L 60 310" fill="#1E293B" stroke="#475569" stroke-width="3"/>
  <line x1="70" y1="140" x2="200" y2="180" stroke="#38BDF8" stroke-width="3" stroke-dasharray="8,6"/>
  <line x1="70" y1="200" x2="200" y2="200" stroke="#38BDF8" stroke-width="3" stroke-dasharray="8,6"/>
  <line x1="70" y1="260" x2="200" y2="220" stroke="#38BDF8" stroke-width="3" stroke-dasharray="8,6"/>
  <!-- Bottleneck Choke Point -->
  <rect x="230" y="170" width="70" height="60" rx="8" fill="#7F1D1D" stroke="#EF4444" stroke-width="3.5"/>
  <line x1="245" y1="185" x2="285" y2="215" stroke="#F8FAFC" stroke-width="3"/>
  <line x1="285" y1="185" x2="245" y2="215" stroke="#F8FAFC" stroke-width="3"/>
  <!-- High-Speed Bypass Conduit (Green) -->
  <path d="M 210 130 C 260 80 340 80 390 140" fill="none" stroke="#34D399" stroke-width="5"/>
  <polygon points="400,150 395,135 382,143" fill="#34D399"/>
  <!-- Express Outlet -->
  <path d="M 310 180 L 520 130 L 520 270 L 310 220" fill="#064E3B" stroke="#34D399" stroke-width="3"/>
  <line x1="330" y1="200" x2="510" y2="200" stroke="#34D399" stroke-width="4"/>
</svg>"""

    def _build_vector_field_streamlines_svg(self) -> str:
        """2D flow field streamlines with velocity direction arrows."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="60" width="500" height="280" rx="16" fill="#0F172A" stroke="#334155" stroke-width="2"/>
  <!-- Curving Streamlines -->
  <path d="M 80 120 C 200 80 380 200 520 140" fill="none" stroke="#38BDF8" stroke-width="3.5"/>
  <polygon points="525,140 510,132 513,148" fill="#38BDF8"/>
  <path d="M 80 200 C 220 180 360 280 520 220" fill="none" stroke="#34D399" stroke-width="4"/>
  <polygon points="525,220 510,212 513,228" fill="#34D399"/>
  <path d="M 80 280 C 180 320 340 120 520 300" fill="none" stroke="#F59E0B" stroke-width="3.5"/>
  <polygon points="525,300 510,292 513,308" fill="#F59E0B"/>
  <!-- Grid Velocity Vectors -->
  <line x1="160" y1="150" x2="190" y2="135" stroke="#A855F7" stroke-width="3"/>
  <circle cx="160" cy="150" r="3" fill="#A855F7"/>
  <line x1="280" y1="220" x2="315" y2="235" stroke="#A855F7" stroke-width="3"/>
  <circle cx="280" cy="220" r="3" fill="#A855F7"/>
  <line x1="400" y1="160" x2="435" y2="180" stroke="#A855F7" stroke-width="3"/>
  <circle cx="400" cy="160" r="3" fill="#A855F7"/>
</svg>"""

    def _build_memory_hierarchy_racks_svg(self) -> str:
        """Hardware cache memory hierarchy racks (SRAM -> HBM -> DRAM)."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- SRAM Cache Rack (Small, Fast, Glowing) -->
  <rect x="70" y="80" width="120" height="240" rx="10" fill="#064E3B" stroke="#34D399" stroke-width="3"/>
  <rect x="85" y="105" width="90" height="25" rx="4" fill="#34D399"/>
  <rect x="85" y="145" width="90" height="25" rx="4" fill="#34D399"/>
  <rect x="85" y="185" width="90" height="25" rx="4" fill="#34D399"/>
  <rect x="85" y="225" width="90" height="25" rx="4" fill="#34D399"/>
  <!-- HBM Memory Rack (Mid) -->
  <rect x="240" y="80" width="130" height="240" rx="10" fill="#1E293B" stroke="#38BDF8" stroke-width="3"/>
  <rect x="255" y="105" width="100" height="30" rx="4" fill="#0284C7"/>
  <rect x="255" y="150" width="100" height="30" rx="4" fill="#0284C7"/>
  <rect x="255" y="195" width="100" height="30" rx="4" fill="#0284C7"/>
  <rect x="255" y="240" width="100" height="30" rx="4" fill="#0284C7"/>
  <!-- Eviction Arrow -->
  <path d="M 200 200 L 230 200" stroke="#F59E0B" stroke-width="4"/>
  <polygon points="235,200 225,193 225,207" fill="#F59E0B"/>
  <!-- Off-Chip Storage (Large, Slow) -->
  <rect x="420" y="80" width="120" height="240" rx="10" fill="#1E1B4B" stroke="#A855F7" stroke-width="3"/>
  <circle cx="480" cy="140" r="30" fill="#312E81" stroke="#A855F7" stroke-width="2"/>
  <circle cx="480" cy="240" r="30" fill="#312E81" stroke="#A855F7" stroke-width="2"/>
</svg>"""

    def _build_pareto_frontier_comparison_svg(self) -> str:
        """Pareto frontier trade-off curve with winning model in top-right quadrant."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <!-- Coordinate Axes -->
  <line x1="80" y1="330" x2="520" y2="330" stroke="#475569" stroke-width="3"/>
  <polygon points="530,330 518,324 518,336" fill="#475569"/>
  <line x1="80" y1="330" x2="80" y2="70" stroke="#475569" stroke-width="3"/>
  <polygon points="80,60 74,72 86,72" fill="#475569"/>
  <!-- Baseline Models in Lower-Left Cluster -->
  <circle cx="160" cy="270" r="8" fill="#EF4444" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="210" cy="240" r="8" fill="#EF4444" stroke="#F8FAFC" stroke-width="2"/>
  <circle cx="280" cy="210" r="9" fill="#F59E0B" stroke="#F8FAFC" stroke-width="2"/>
  <!-- Pareto Optimal Frontier Curve -->
  <path d="M 120 290 Q 280 200 440 90" fill="none" stroke="#38BDF8" stroke-width="4" stroke-dasharray="8,6"/>
  <!-- SOTA Winner in Optimal Frontier -->
  <circle cx="440" cy="90" r="15" fill="#10B981" stroke="#34D399" stroke-width="4"/>
  <circle cx="440" cy="90" r="24" fill="none" stroke="#34D399" stroke-width="2" stroke-dasharray="4,4"/>
  <line x1="440" y1="330" x2="440" y2="114" stroke="#34D399" stroke-width="2" stroke-dasharray="4,4"/>
  <line x1="80" y1="90" x2="416" y2="90" stroke="#34D399" stroke-width="2" stroke-dasharray="4,4"/>
</svg>"""

    def _build_neural_semantic_network_svg(self) -> str:
        """Universal neural network topology with glowing nodes and interconnects."""
        return """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
  <rect x="60" y="60" width="480" height="280" rx="16" fill="#0F172A" stroke="#334155" stroke-width="2"/>
  <!-- Synaptic Interconnects -->
  <line x1="130" y1="120" x2="290" y2="140" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.6"/>
  <line x1="130" y1="200" x2="290" y2="140" stroke="#38BDF8" stroke-width="2.5" stroke-opacity="0.8"/>
  <line x1="130" y1="280" x2="290" y2="260" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.6"/>
  <line x1="290" y1="140" x2="460" y2="200" stroke="#34D399" stroke-width="3.5"/>
  <line x1="290" y1="260" x2="460" y2="200" stroke="#34D399" stroke-width="3.5"/>
  <!-- Input Layer -->
  <circle cx="130" cy="120" r="14" fill="#1E293B" stroke="#38BDF8" stroke-width="3"/>
  <circle cx="130" cy="200" r="16" fill="#0284C7" stroke="#38BDF8" stroke-width="3.5"/>
  <circle cx="130" cy="280" r="14" fill="#1E293B" stroke="#38BDF8" stroke-width="3"/>
  <!-- Hidden Layer -->
  <circle cx="290" cy="140" r="18" fill="#1E1B4B" stroke="#A855F7" stroke-width="3.5"/>
  <circle cx="290" cy="260" r="18" fill="#1E1B4B" stroke="#A855F7" stroke-width="3.5"/>
  <!-- Output Node -->
  <circle cx="460" cy="200" r="22" fill="#064E3B" stroke="#34D399" stroke-width="4.5"/>
  <circle cx="460" cy="200" r="8" fill="#F8FAFC"/>
</svg>"""

    def _clean_chalkboard_svg(self, svg_code: str) -> str:
        """
        Removes any solid dark full-canvas rects that could conflict with Manim's
        transparent or custom chalkboard background, and removes disallowed tags.
        """
        # Remove any <text> tags if LLM accidentally produced them
        cleaned = re.sub(r'<text[\s\S]*?</text>', '', svg_code, flags=re.IGNORECASE)
        # Remove any solid black/dark background rect covering whole canvas
        cleaned = re.sub(
            r'<rect[^>]*(?:width=\"(?:600|100%)\")[^>]*(?:fill=\"(?:#0f172a|#0b0f19|#000|#1e293b|black)\")[^>]*/>',
            '',
            cleaned,
            flags=re.IGNORECASE
        )
        return cleaned.strip()

    def _validate_svg(self, svg_code: str) -> bool:
        """Validates XML syntax and presence of root svg tag."""
        if not svg_code or "<svg" not in svg_code or "</svg>" not in svg_code:
            return False
        try:
            ET.fromstring(svg_code)
            return True
        except Exception:
            return False
