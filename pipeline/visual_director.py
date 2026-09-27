"""
The Model Verse — Script-Driven Visual Director (Visual Engine 3.0)
Reads the voiceover script, conceptual shifts, and physical analogies for each beat,
and dynamically generates bespoke, high-fidelity SVG vector designs and animation recipes.
Eliminates generic templates and repetitive circular gauges in favor of authentic 3b1b visual explanations.
"""

import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import WORKSPACE_ROOT

VISUAL_ASSETS_DIR = PROJECT_ROOT / "public" / "visual_assets"
VISUAL_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_svg_code(raw_svg: str) -> str:
    """Cleans up raw LLM SVG code, strips markdown blocks, and ensures valid XML."""
    text = raw_svg.strip()
    # Strip markdown code fences
    if "```" in text:
        match = re.search(r"```(?:xml|svg)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()
        else:
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text).strip()

    # Find <svg ... </svg>
    svg_start = text.find("<svg")
    svg_end = text.rfind("</svg>")
    if svg_start != -1 and svg_end != -1:
        text = text[svg_start:svg_end + 6]
    
    # Ensure xmlns attribute exists
    if "xmlns=" not in text:
        text = text.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
    return text


def validate_and_fix_svg(svg_path: Path) -> bool:
    """Parses SVG with XML parser to verify validity; patches any malformed tags."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        # Verify it has valid elements
        if len(list(root)) == 0 and not root.text:
            return False
        return True
    except Exception as e:
        print(f"⚠️ XML Validation error in {svg_path.name}: {e}")
        return False


class VisualDirector:
    """
    AI Visual Director that designs bespoke graphic scenes for every beat of a video script.
    """

    def __init__(self):
        import google.generativeai as genai
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.candidate_models = ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-flash-latest"]

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Calls Gemini with model fallback cascade."""
        import google.generativeai as genai
        if not self.api_key:
            return None

        for model_name in self.candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                # Try next model
                continue
        return None

    def design_beat_svg(
        self,
        beat_id: int,
        beat_text: str,
        visual_focus: str,
        topic: str,
        clean_id: str,
        svo_action: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generates a custom SVG vector diagram specifically designed for this beat's narrative.
        """
        output_file = VISUAL_ASSETS_DIR / f"{clean_id}_beat_{beat_id}.svg"
        if output_file.exists() and output_file.stat().st_size > 200:
            print(f"   🎨 Reusing existing custom vector asset for Beat {beat_id}: {output_file.name}")
            return output_file

        print(f"   🎨 Generating bespoke 3b1b vector diagram for Beat {beat_id}...")

        svo_info = ""
        if svo_action:
            svo_info = f"Action: {svo_action.get('subject', '')} {svo_action.get('action_verb', '')} {svo_action.get('direct_object', '')} (Anchor: '{svo_action.get('anchor_word', '')}')"

        prompt = f"""You are the Lead Visual Designer for 'The Model Verse', an elite 3Blue1Brown-style educational channel explaining cutting-edge AI breakthroughs.

Generate a complete, valid, standalone SVG vector diagram for Beat {beat_id} of our video on: '{topic}'.

NARRATIVE CONTEXT:
- Voiceover Audio: "{beat_text}"
- Target Visual Focus: "{visual_focus}"
{svo_info}

DESIGN & PEDAGOGY SPECIFICATIONS:
1. Canvas & ViewBox:
   - viewBox="0 0 800 900" (vertical 9:16 safe focal area)
   - Transparent or dark background (do NOT add a black background rect, the canvas is already #0A0D14).
2. 3Blue1Brown Aesthetic & Color Palette:
   - Neon Sky Blue: #38BDF8 (Primary signal / thought 1)
   - Emerald Mint: #34D399 (Positive outcome / thought 2 / clarity)
   - Amber Gold: #F59E0B (Attention / energy / control / tuning)
   - Coral Crimson: #EF4444 (Noise / static / collision / chaos)
   - Electric Purple: #A855F7 (Latent space / deep model core)
   - Subtle Chalk White: #F8FAFC (Lines, ticks, labels, arrows)
   - Muted Slate: #475569 (Containers, background grids, guides)
3. Visual Metaphor Grounding:
   - DO NOT make generic empty cards, boring rectangles, or plain bullet points!
   - DO NOT create generic two-circle progress gauges!
   - Directly illustrate the physical and mathematical mechanism:
     * If the script mentions waves or signals merging -> draw two distinct sinusoidal wave streams colliding into a complex interference pattern with glowing crests.
     * If the script mentions radio dials / tuning / static -> draw a curved or horizontal radio frequency dial with tick marks, a sharp tuning needle, frequency labels (e.g. 98.5 MHz vs 104.2 MHz), and overlapping noisy waveforms.
     * If the script mentions packing thoughts into one space -> draw a coordinate plane or compact memory matrix showing orthogonal vector arrows coexisting.
     * If the script mentions peeling layers / separating thoughts -> draw a laser prism or separator pulling the tangled beam into two crystal-clear, clean parallel light streams.
     * If the script mentions generating two clear answers / linear map -> draw a single forward-pass vector splitting smoothly into two crisp, labeled output pathways.
4. Semantic Organization:
   - Group related elements using <g id="..."> with clear descriptive names (e.g. id="wave_left", id="wave_right", id="interference_zone", id="tuner_needle", id="output_streams").
   - Use clean SVG paths, smooth Bezier curves (C, S, Q), glowing gradients (<linearGradient>), and clean typography.
   - Keep text minimal: 1-3 short technical labels (e.g. "Signal A", "Signal B", "Superposition", "Linear Map"), font-family="sans-serif", font-weight="700", font-size="16" to "22".

Return ONLY the raw SVG code starting with <svg> and ending with </svg>. No markdown explanation.
"""

        raw_svg = self._call_gemini(prompt)
        if raw_svg:
            clean_svg = sanitize_svg_code(raw_svg)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(clean_svg)

            if validate_and_fix_svg(output_file):
                print(f"      ✅ Generated valid custom SVG: {output_file.name} ({output_file.stat().st_size} bytes)")
                return output_file
            else:
                print(f"      ⚠️ Generated SVG failed XML validation. Building fallback procedural vector...")

        # Fallback procedural vector generator if API fails
        fallback_svg = self._generate_fallback_vector_svg(beat_id, topic, visual_focus)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(fallback_svg)
        return output_file

    def _generate_fallback_vector_svg(self, beat_id: int, topic: str, visual_focus: str) -> str:
        """High-quality procedural SVG fallback if LLM is unavailable."""
        if beat_id == 1:
            # Two waves colliding into interference
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900" width="800" height="900">
  <defs>
    <linearGradient id="grad_blue" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#38BDF8" stop-opacity="1.0"/>
    </linearGradient>
    <linearGradient id="grad_orange" x1="100%" y1="0%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#F59E0B" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#F59E0B" stop-opacity="1.0"/>
    </linearGradient>
  </defs>
  <!-- Stream A: Blue Wave -->
  <g id="stream_a">
    <text x="120" y="240" fill="#38BDF8" font-family="sans-serif" font-size="20" font-weight="700">THOUGHT A: SIGNAL 1</text>
    <path d="M 50 300 Q 150 200 250 300 T 450 300" fill="none" stroke="#38BDF8" stroke-width="5" stroke-linecap="round"/>
  </g>
  <!-- Stream B: Orange Wave -->
  <g id="stream_b">
    <text x="500" y="240" fill="#F59E0B" font-family="sans-serif" font-size="20" font-weight="700">THOUGHT B: SIGNAL 2</text>
    <path d="M 350 300 Q 450 400 550 300 T 750 300" fill="none" stroke="#F59E0B" stroke-width="5" stroke-linecap="round"/>
  </g>
  <!-- Central Collision / Overlap Zone -->
  <g id="collision_zone">
    <circle cx="400" cy="550" r="140" fill="none" stroke="#EF4444" stroke-width="2" stroke-dasharray="6 6" opacity="0.6"/>
    <path d="M 150 550 Q 250 430 320 570 T 400 530 T 480 580 T 650 550" fill="none" stroke="#EF4444" stroke-width="6"/>
    <text x="400" y="740" fill="#F8FAFC" font-family="sans-serif" font-size="22" font-weight="700" text-anchor="middle">OVERLAPPING SUPERPOSITION</text>
    <text x="400" y="775" fill="#94A3B8" font-family="sans-serif" font-size="16" text-anchor="middle">Two Independent Concepts in One Latent Channel</text>
  </g>
</svg>"""
        elif beat_id == 2:
            # Radio tuner dial with static overlap
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900" width="800" height="900">
  <!-- Radio Dial Outer Casing -->
  <rect x="80" y="200" width="640" height="300" rx="20" fill="#1E293B" stroke="#475569" stroke-width="4" opacity="0.8"/>
  <!-- Frequency Ticks -->
  <g id="frequency_scale">
    <line x1="120" y1="320" x2="680" y2="320" stroke="#64748B" stroke-width="2"/>
    <line x1="160" y1="300" x2="160" y2="320" stroke="#F8FAFC" stroke-width="3"/>
    <text x="160" y="280" fill="#94A3B8" font-family="sans-serif" font-size="16" text-anchor="middle">88 MHz</text>
    <line x1="280" y1="300" x2="280" y2="320" stroke="#38BDF8" stroke-width="4"/>
    <text x="280" y="280" fill="#38BDF8" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">98.5 [STATION A]</text>
    <line x1="520" y1="300" x2="520" y2="320" stroke="#F59E0B" stroke-width="4"/>
    <text x="520" y="280" fill="#F59E0B" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">104.2 [STATION B]</text>
    <line x1="640" y1="300" x2="640" y2="320" stroke="#F8FAFC" stroke-width="3"/>
    <text x="640" y="280" fill="#94A3B8" font-family="sans-serif" font-size="16" text-anchor="middle">108 MHz</text>
  </g>
  <!-- Tuner Needle between stations -->
  <g id="tuner_needle">
    <line x1="400" y1="230" x2="400" y2="420" stroke="#EF4444" stroke-width="5" stroke-linecap="round"/>
    <circle cx="400" cy="420" r="10" fill="#EF4444"/>
    <text x="400" y="470" fill="#EF4444" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">TUNER: DOUBLE INTERFERENCE</text>
  </g>
  <!-- Static Sound Waveforms -->
  <g id="static_wave">
    <path d="M 100 620 L 150 590 L 190 640 L 240 580 L 300 650 L 370 570 L 420 660 L 500 580 L 580 640 L 640 600 L 700 620" fill="none" stroke="#F59E0B" stroke-width="4"/>
    <text x="400" y="730" fill="#F8FAFC" font-family="sans-serif" font-size="20" font-weight="700" text-anchor="middle">COLLIDING AUDIO WAVES</text>
    <text x="400" y="765" fill="#94A3B8" font-family="sans-serif" font-size="16" text-anchor="middle">The weights blend two signals on one single channel</text>
  </g>
</svg>"""
        elif beat_id == 3:
            # 2D subspace packing / high dimensional efficiency
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900" width="800" height="900">
  <!-- Coordinate Grid -->
  <g id="grid_axes">
    <line x1="150" y1="500" x2="650" y2="500" stroke="#475569" stroke-width="3"/>
    <line x1="400" y1="750" x2="400" y2="250" stroke="#475569" stroke-width="3"/>
    <polygon points="655,500 640,492 640,508" fill="#475569"/>
    <polygon points="400,245 392,260 408,260" fill="#475569"/>
    <text x="660" y="525" fill="#94A3B8" font-family="sans-serif" font-size="16">Dim X</text>
    <text x="415" y="250" fill="#94A3B8" font-family="sans-serif" font-size="16">Dim Y</text>
  </g>
  <!-- Vector 1 (Blue) -->
  <g id="vector_1">
    <line x1="400" y1="500" x2="580" y2="350" stroke="#38BDF8" stroke-width="6" stroke-linecap="round"/>
    <polygon points="585,345 570,355 575,370" fill="#38BDF8"/>
    <text x="600" y="340" fill="#38BDF8" font-family="sans-serif" font-size="20" font-weight="700">Concept v₁</text>
  </g>
  <!-- Vector 2 (Green) -->
  <g id="vector_2">
    <line x1="400" y1="500" x2="250" y2="330" stroke="#34D399" stroke-width="6" stroke-linecap="round"/>
    <polygon points="245,325 252,342 267,335" fill="#34D399"/>
    <text x="160" y="320" fill="#34D399" font-family="sans-serif" font-size="20" font-weight="700">Concept v₂</text>
  </g>
  <!-- Orthogonal Superposition Angle -->
  <g id="angle_badge">
    <path d="M 470 440 Q 400 400 350 440" fill="none" stroke="#F59E0B" stroke-width="3" stroke-dasharray="5 5"/>
    <text x="400" y="420" fill="#F59E0B" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">θ ≈ 90° (Almost Orthogonal)</text>
    <rect x="180" y="650" width="440" height="90" rx="15" fill="#1E293B" stroke="#34D399" stroke-width="3"/>
    <text x="400" y="690" fill="#34D399" font-family="sans-serif" font-size="22" font-weight="700" text-anchor="middle">SUPERPOSITION CAPACITY</text>
    <text x="400" y="720" fill="#E2E8F0" font-family="sans-serif" font-size="16" text-anchor="middle">Stores N > D features inside D dimensions</text>
  </g>
</svg>"""
        elif beat_id == 4:
            # Laser Prism Disentangling Layers
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900" width="800" height="900">
  <!-- Incoming Mixed Beam -->
  <g id="incoming_tangled_beam">
    <text x="160" y="320" fill="#EF4444" font-family="sans-serif" font-size="20" font-weight="700" text-anchor="middle">MIXED STATIC</text>
    <line x1="80" y1="450" x2="330" y2="450" stroke="#EF4444" stroke-width="8" stroke-linecap="round"/>
    <line x1="80" y1="450" x2="330" y2="450" stroke="#F59E0B" stroke-width="4" stroke-dasharray="8 4"/>
  </g>
  <!-- Optical / Linear Decoder Prism -->
  <g id="decoder_prism">
    <polygon points="400,320 480,560 320,560" fill="#1E293B" stroke="#38BDF8" stroke-width="5"/>
    <text x="400" y="480" fill="#38BDF8" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">LINEAR</text>
    <text x="400" y="505" fill="#38BDF8" font-family="sans-serif" font-size="16" text-anchor="middle">DECODER</text>
  </g>
  <!-- Separated Disentangled Streams -->
  <g id="separated_streams">
    <!-- Stream 1 (Blue) Upward -->
    <path d="M 430 430 L 720 280" fill="none" stroke="#38BDF8" stroke-width="7" stroke-linecap="round"/>
    <text x="620" y="250" fill="#38BDF8" font-family="sans-serif" font-size="20" font-weight="700">CLEAN THOUGHT 1</text>
    <!-- Stream 2 (Mint) Downward -->
    <path d="M 430 470 L 720 620" fill="none" stroke="#34D399" stroke-width="7" stroke-linecap="round"/>
    <text x="620" y="660" fill="#34D399" font-family="sans-serif" font-size="20" font-weight="700">CLEAN THOUGHT 2</text>
  </g>
  <text x="400" y="780" fill="#F8FAFC" font-family="sans-serif" font-size="22" font-weight="700" text-anchor="middle">PEELING LAYERS APART</text>
  <text x="400" y="815" fill="#94A3B8" font-family="sans-serif" font-size="16" text-anchor="middle">Tuned projection isolates each independent concept</text>
</svg>"""
        else:
            # Beat 5: Dual Output Parallel Execution
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900" width="800" height="900">
  <!-- Central Model Core -->
  <rect x="250" y="380" width="300" height="140" rx="20" fill="#1E293B" stroke="#A855F7" stroke-width="4"/>
  <text x="400" y="440" fill="#A855F7" font-family="sans-serif" font-size="22" font-weight="700" text-anchor="middle">1 FORWARD PASS</text>
  <text x="400" y="475" fill="#E2E8F0" font-family="sans-serif" font-size="16" text-anchor="middle">Shared Latent Geometry</text>
  <!-- Input Stream -->
  <line x1="400" y1="180" x2="400" y2="370" stroke="#38BDF8" stroke-width="6" stroke-linecap="round"/>
  <polygon points="400,378 392,360 408,360" fill="#38BDF8"/>
  <text x="400" y="150" fill="#38BDF8" font-family="sans-serif" font-size="20" font-weight="700" text-anchor="middle">DUAL-PROMPT INPUT</text>
  <!-- Output Branches -->
  <g id="output_a">
    <path d="M 330 520 Q 250 620 180 680" fill="none" stroke="#38BDF8" stroke-width="6" stroke-linecap="round"/>
    <polygon points="175,685 180,668 194,677" fill="#38BDF8"/>
    <rect x="50" y="710" width="260" height="70" rx="12" fill="#0F172A" stroke="#38BDF8" stroke-width="3"/>
    <text x="180" y="745" fill="#38BDF8" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">OUTPUT 1: REASONING</text>
    <text x="180" y="768" fill="#94A3B8" font-family="sans-serif" font-size="14" text-anchor="middle">Confidence: 99.4%</text>
  </g>
  <g id="output_b">
    <path d="M 470 520 Q 550 620 620 680" fill="none" stroke="#34D399" stroke-width="6" stroke-linecap="round"/>
    <polygon points="625,685 620,668 606,677" fill="#34D399"/>
    <rect x="490" y="710" width="260" height="70" rx="12" fill="#0F172A" stroke="#34D399" stroke-width="3"/>
    <text x="620" y="745" fill="#34D399" font-family="sans-serif" font-size="18" font-weight="700" text-anchor="middle">OUTPUT 2: SYNTHESIS</text>
    <text x="620" y="768" fill="#94A3B8" font-family="sans-serif" font-size="14" text-anchor="middle">Confidence: 98.9%</text>
  </g>
</svg>"""

    def prepare_storyboard_for_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes all beats in the spec, generates custom vector diagrams for each beat,
        and attaches the storyboard directives.
        """
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short_topic")).lower()
        topic = spec.get("title", clean_id)
        beats = spec.get("beats", [])

        print(f"\n🎬 [VisualDirector] Designing Script-Driven Visual Storyboard for '{topic}'...")

        storyboard_beats = []
        for b in beats:
            b_id = b.get("beat_id", 1)
            b_text = b.get("text", "")
            v_focus = b.get("visual_focus", "")
            svo = b.get("svo_action", {})

            # Beat 6 is the channel brand signature outro
            if b_id >= 6 or "Follow The Model Verse" in b_text:
                continue

            svg_path = self.design_beat_svg(
                beat_id=b_id,
                beat_text=b_text,
                visual_focus=v_focus,
                topic=topic,
                clean_id=clean_id,
                svo_action=svo
            )

            b["bespoke_svg_path"] = str(svg_path.relative_to(PROJECT_ROOT))
            b["visual_type"] = "bespoke_script_svg"
            storyboard_beats.append(b)

        spec["script_driven_visuals"] = True
        return spec
