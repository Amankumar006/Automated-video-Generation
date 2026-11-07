"""
The Model Verse — AST Security Sandbox & Headless Manim Validator
Validates LLM-synthesized Manim visual code before execution:
1. AST Whitelist & LaTeX Ban: Rejects unsafe imports (os, sys, subprocess, open, eval)
   and explicitly forbids MathTex / Tex (which crash on hosts without LaTeX).
2. Structural Contract: Asserts class BespokeBeatVisual(VGroup) exists with
   required animation methods.
3. Headless Dry-Run: Executes a 1-second headless scene.play() in an isolated
   subprocess to guarantee zero animation exceptions and 9:16 safe-zone bounds.
"""

import ast
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Safe-Zone Geometric Constraints for 9:16 vertical video
MAX_VISUAL_WIDTH = 6.8
MAX_VISUAL_HEIGHT = 7.2
SAFE_CENTER_Y_MIN = -2.5
SAFE_CENTER_Y_MAX = 4.5

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "requests", "urllib", "shutil",
    "pathlib", "importlib", "pickle", "eval", "exec", "open"
}

FORBIDDEN_CALLS = {
    "eval", "exec", "compile", "__import__", "open", "getattr", "setattr"
}

FORBIDDEN_MANIM_CLASSES = {
    "MathTex", "Tex"  # Host lacks pdflatex; CleanText with UTF-8 math is required
}


class ASTSecurityValidator(ast.NodeVisitor):
    """Inspects the Python AST to ensure code is safe and adheres to Manim constraints."""

    def __init__(self):
        self.errors = []
        self.has_bespoke_class = False
        self.methods_found = set()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in FORBIDDEN_MODULES:
                self.errors.append(f"Forbidden module imported: '{base_mod}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in FORBIDDEN_MODULES:
                self.errors.append(f"Forbidden module import: 'from {base_mod} import ...'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check direct function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_CALLS:
                self.errors.append(f"Forbidden function call: '{func_name}()'")
            if func_name in FORBIDDEN_MANIM_CLASSES:
                self.errors.append(
                    f"Forbidden LaTeX class: '{func_name}()'. Host lacks pdflatex. "
                    f"Use CleanText with Unicode math symbols (e.g. 'O(N^2)', 'α, β, ∑, →') instead."
                )
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in FORBIDDEN_CALLS:
                self.errors.append(f"Forbidden attribute call: '.{attr_name}()'")
            if attr_name in FORBIDDEN_MANIM_CLASSES:
                self.errors.append(
                    f"Forbidden LaTeX class: '.{attr_name}()'. "
                    f"Use CleanText with Unicode math symbols instead."
                )

        # Catch graph-dot misalignment patterns
        if isinstance(node.func, ast.Attribute) and node.func.attr == "scale":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "animate":
                target = node.func.value.value
                target_name = target.attr if isinstance(target, ast.Attribute) else (target.id if isinstance(target, ast.Name) else "")
                if target_name in ("nodes", "loop_nodes", "expert_nodes", "tree_nodes", "dots", "tokens", "markers", "points", "vertices"):
                    has_about = any(kw.arg in ("about_point", "about_edge") for kw in node.keywords)
                    if not has_about:
                        self.errors.append(
                            f"Graph misalignment risk: Calling '{target_name}.animate.scale()' on a group of nodes/dots/tokens shifts their positions and detaches them from branch lines or curves. Pulse individual dots via list comprehension '*[d.animate.scale(...) for d in self.{target_name}]' or scale the connected tree/graph group together."
                        )

        if isinstance(node.func, ast.Attribute) and node.func.attr == "shift":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "animate":
                target = node.func.value.value
                target_name = target.attr if isinstance(target, ast.Attribute) else (target.id if isinstance(target, ast.Name) else "")
                if target_name in ("path", "curve", "manifold", "loop_path", "branch_line"):
                    self.errors.append(
                        f"Graph misalignment risk: Calling '{target_name}.animate.shift()' without moving attached dots/tokens detaches the curve from its points. Shift both together via 'VGroup(self.{target_name}, self.tokens).animate.shift(...)/'."
                    )

        if isinstance(node.func, ast.Name) and node.func.id == "Rotate":
            if node.args:
                first_arg = node.args[0]
                first_name = first_arg.attr if isinstance(first_arg, ast.Attribute) else (first_arg.id if isinstance(first_arg, ast.Name) else "")
                if first_name in ("loop_nodes", "nodes", "dots", "tokens"):
                    self.errors.append(
                        f"Graph misalignment risk: Calling 'Rotate({first_name})' rotates dots independently of their connecting path line. Rotate both together via 'Rotate(VGroup(self.loop_path, self.{first_name}))'."
                    )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == "BespokeBeatVisual":
            self.has_bespoke_class = True
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.methods_found.add(item.name)
        self.generic_visit(node)


def validate_code_ast(code_str: str) -> Tuple[bool, Optional[str]]:
    """Performs static AST validation on the synthesized Python code."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Python SyntaxError: {e.msg} at line {e.lineno}"

    validator = ASTSecurityValidator()
    validator.visit(tree)

    if validator.errors:
        return False, "AST Security Violations:\n- " + "\n- ".join(validator.errors)

    if not validator.has_bespoke_class:
        return False, "Missing mandatory class 'class BespokeBeatVisual(VGroup):'"

    required_methods = {"__init__", "get_entrance_animation", "get_kinetic_animation"}
    missing = required_methods - validator.methods_found
    if missing:
        return False, f"BespokeBeatVisual is missing required method(s): {', '.join(missing)}"

    return True, None


def validate_visual_quality_contract(code_str: str) -> Tuple[bool, Optional[str]]:
    """Reject visually lazy or non-deterministic generated modules before render."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as exc:
        return False, f"Visual quality lint could not parse code: {exc.msg}"

    source = code_str.lower()
    if "np.random" in source or "random." in source or "import random" in source:
        return False, "Visual quality contract: generated coordinates must be deterministic; do not use random sampling."

    call_names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            call_names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            call_names.append(node.func.attr)

    text_calls = sum(name in {"CleanText", "Text", "MarkupText"} for name in call_names)
    if text_calls > 3:
        return False, f"Visual quality contract: use at most three explanatory text objects, found {text_calls}. Let the geometry carry the story."

    primitive_names = {
        "Arrow", "Arc", "Circle", "Dot", "Line", "Polygon", "VMobject",
        "StreamLines", "ParametricFunction", "NumberPlane", "DashedLine",
    }
    primitive_count = sum(name in primitive_names for name in call_names)
    if primitive_count < 2:
        return False, "Visual quality contract: the beat needs at least two connected geometric primitives, not a lone object or text treatment."

    motion_names = {
        "Create", "Write", "Transform", "ReplacementTransform", "MoveAlongPath",
        "GrowArrow", "ShowPassingFlash", "FadeTransform", "UpdateFromAlphaFunc",
    }
    has_motion = any(name in motion_names for name in call_names) or ".animate" in source
    if not has_motion:
        return False, "Visual quality contract: the mechanism must have an intentional transformation or path motion."

    if "arrange_in_grid" in source and "roundedrectangle" in source:
        return False, "Visual quality contract: repeated rounded UI tiles are not a mechanism visual."

    return True, None


def check_mobject_collisions_and_bounds(visual: Any) -> Tuple[bool, Optional[str]]:
    """
    Programmatic geometric gate enforcing zero collisions and safe-zone adherence.
    Checks:
    1. Safe-zone vertical/horizontal boundaries (Subtitles: y >= -2.45, Header: y <= 6.0, Sides: |x| <= 3.8).
    2. Text-Text collisions: No two labels may overlap.
    3. Text-Shape collisions: Labels may not collide with shapes unless the shape is a properly-sized background container.
    4. Container overflow: Text must fit inside its enclosing container with margin.
    5. Solid Shape-Shape collisions: Non-concentric filled shapes may not heavily overlap (IoU > 0.35).
    """
    import numpy as np

    # 1. Bounds checks
    bottom = visual.get_bottom()[1]
    top = visual.get_top()[1]
    left = visual.get_left()[0]
    right = visual.get_right()[0]

    if bottom < -2.45:
        return False, f"Safe-Zone Breach: Visual bottom edge ({bottom:.2f}) is below -2.45, colliding with 9:16 vertical kinetic subtitles (y = -3.45). Shift visual UP."
    if top > 6.00:
        return False, f"Safe-Zone Breach: Visual top edge ({top:.2f}) is above 6.00, colliding with top header watermark. Shift visual DOWN."
    if left < -3.80 or right > 3.80:
        return False, f"Safe-Zone Breach: Visual exceeds horizontal safe margins [-3.8, 3.8] (left={left:.2f}, right={right:.2f}). Scale or center visual."

    # Extract elements
    texts = []
    shapes = []

    def extract(m):
        # Treat Text and CleanText as atomic
        if hasattr(m, "text") or m.__class__.__name__ in ("Text", "CleanText", "MarkupText", "MathTex", "Tex", "Paragraph"):
            texts.append(m)
            return
        if len(m.submobjects) > 0:
            for sub in m.submobjects:
                extract(sub)
        else:
            # Skip invisible elements
            fill_op = getattr(m, "fill_opacity", 0.0)
            stroke_op = getattr(m, "stroke_opacity", 1.0)
            stroke_w = getattr(m, "stroke_width", 1.0)
            if fill_op == 0.0 and (stroke_op == 0.0 or stroke_w == 0.0):
                return
            shapes.append(m)

    extract(visual)

    def effective_aabb(m):
        l, r = m.get_left()[0], m.get_right()[0]
        b, t = m.get_bottom()[1], m.get_top()[1]
        if r - l < 0.04:
            cx = (l + r) / 2
            l, r = cx - 0.02, cx + 0.02
        if t - b < 0.04:
            cy = (b + t) / 2
            b, t = cy - 0.02, cy + 0.02
        return l, r, b, t

    def get_overlap(bb1, bb2):
        dx = min(bb1[1], bb2[1]) - max(bb1[0], bb2[0])
        dy = min(bb1[3], bb2[3]) - max(bb1[2], bb2[2])
        return dx, dy

    # 2. Text vs Text Collisions
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            t1, t2 = texts[i], texts[j]
            dx, dy = get_overlap(effective_aabb(t1), effective_aabb(t2))
            if dx > 0.04 and dy > 0.04:
                area = dx * dy
                if area > 0.005:
                    lbl1 = getattr(t1, "text", t1.__class__.__name__).strip()
                    lbl2 = getattr(t2, "text", t2.__class__.__name__).strip()
                    return False, (
                        f"Text Collision: Label '{lbl1}' overlaps label '{lbl2}' by dx={dx:.2f}, dy={dy:.2f}. "
                        f"Stack them vertically (.arrange(DOWN, buff=0.25)) or separate their positions."
                    )

    # 3. Text vs Shape Collisions & Container Overflow
    for t in texts:
        t_bb = effective_aabb(t)
        t_lbl = getattr(t, "text", "Label").strip()
        t_center = t.get_center()

        for s in shapes:
            s_bb = effective_aabb(s)
            dx, dy = get_overlap(t_bb, s_bb)
            if dx > 0.06 and dy > 0.06:
                s_cls = s.__class__.__name__
                is_container_type = s_cls in ("Rectangle", "RoundedRectangle", "Circle", "Ellipse")
                dist_centers = np.linalg.norm(s.get_center() - t_center)
                s_fill = getattr(s, "fill_opacity", 0.0)

                # Check if s was positioned as an enclosing container for t (e.g. text inside pill/card)
                if is_container_type and dist_centers < 0.20:
                    if t.width > s.width - 0.05 or t.height > s.height - 0.05:
                        return False, (
                            f"Container Overflow: Label '{t_lbl}' (w={t.width:.2f}, h={t.height:.2f}) "
                            f"overflows container {s_cls} (w={s.width:.2f}, h={s.height:.2f}). "
                            f"Scale text down or widen container."
                        )
                    continue  # Clean container

                # Check if s is a large background panel containing t
                is_large_container = (
                    is_container_type and
                    (s_cls in ("Rectangle", "RoundedRectangle") or s_fill >= 0.2) and
                    s.width >= t.width - 0.05 and s.height >= t.height - 0.05 and
                    dist_centers <= min(s.width, s.height) * 0.25
                )
                if is_large_container:
                    continue

                # Otherwise it is an unwanted collision with a shape (bar, path, line, or circle)
                return False, (
                    f"Text-Shape Collision: Label '{t_lbl}' collides with {s_cls} "
                    f"by dx={dx:.2f}, dy={dy:.2f}. Reposition label to avoid overlapping geometry."
                )

    # 4. Heavy Shape vs Shape Collisions
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            s1, s2 = shapes[i], shapes[j]
            s1_2d = s1.__class__.__name__ in ("Rectangle", "RoundedRectangle", "Circle", "Ellipse", "Polygon", "Square", "Star")
            s2_2d = s2.__class__.__name__ in ("Rectangle", "RoundedRectangle", "Circle", "Ellipse", "Polygon", "Square", "Star")
            if s1_2d and s2_2d:
                op1 = getattr(s1, "fill_opacity", 0.0)
                op2 = getattr(s2, "fill_opacity", 0.0)
                if op1 > 0.25 and op2 > 0.25:
                    dx, dy = get_overlap(effective_aabb(s1), effective_aabb(s2))
                    if dx > 0.10 and dy > 0.10:
                        dist_centers = np.linalg.norm(s1.get_center() - s2.get_center())
                        # Concentric rings / glow / halos are allowed
                        if dist_centers < 0.12:
                            continue
                        area_intersect = dx * dy
                        area1 = s1.width * s1.height
                        area2 = s2.width * s2.height
                        iou = area_intersect / (area1 + area2 - area_intersect + 1e-6)
                        if iou > 0.35:
                            return False, (
                                f"Shape Collision: {s1.__class__.__name__} and {s2.__class__.__name__} "
                                f"heavily overlap (IoU={iou:.2f}). Space them apart."
                            )

    return True, None


def validate_code_in_process(code_str: str) -> Tuple[bool, Optional[str]]:
    """
    Executes dry-run in-process using an isolated namespace (sub-second performance).
    AST validation has already verified that no unsafe functions or imports exist.
    """
    try:
        from manim import config, Scene, VGroup
        from manim_engine.primitives.typography import CleanText
        import numpy as np

        # Safe execution namespace
        import manim
        safe_ns = {k: getattr(manim, k) for k in dir(manim) if not k.startswith("__")}
        safe_ns["CleanText"] = CleanText
        safe_ns["np"] = np

        # Configure fast dry run
        config.dry_run = True
        config.write_to_movie = False
        config.quality = "low_quality"
        config.verbosity = "WARNING"

        compiled = compile(code_str, "<synthesized_visual>", "exec")
        exec(compiled, safe_ns)

        bespoke_cls = safe_ns.get("BespokeBeatVisual")
        if not bespoke_cls:
            return False, "BespokeBeatVisual class not found in executed code"

        visual = bespoke_cls()
        if not isinstance(visual, VGroup):
            return False, "BespokeBeatVisual must inherit from VGroup (e.g. class BespokeBeatVisual(VGroup):)"

        # Check bounds
        width = visual.width
        height = visual.height
        if width > MAX_VISUAL_WIDTH:
            return False, f"Visual width ({width:.2f}) exceeds 9:16 safe-zone limit {MAX_VISUAL_WIDTH}"
        if height > MAX_VISUAL_HEIGHT:
            return False, f"Visual height ({height:.2f}) exceeds 9:16 safe-zone limit {MAX_VISUAL_HEIGHT}"

        # Programmatic geometric & collision gate
        bounds_ok, bounds_err = check_mobject_collisions_and_bounds(visual)
        if not bounds_ok:
            return False, bounds_err

        # Test animation execution
        scene = Scene()
        scene.add(visual)

        ent_anim = visual.get_entrance_animation(run_time=0.1)
        if ent_anim is None:
            return False, "get_entrance_animation() returned None instead of an Animation"
        scene.play(ent_anim)

        kin_anim = visual.get_kinetic_animation(run_time=0.1)
        if kin_anim is None:
            return False, "get_kinetic_animation() returned None instead of an Animation"
        scene.play(kin_anim)

        if "get_ambient_animation" in visual.__class__.__dict__:
            amb_anim = visual.get_ambient_animation(run_time=0.1)
            if amb_anim is not None:
                scene.play(amb_anim)

        return True, None
    except Exception as e:
        import traceback
        tb = traceback.format_exc().splitlines()
        return False, f"Execution error in BespokeBeatVisual:\n" + "\n".join(tb[-8:])


def validate_code_headless_execution(code_str: str, timeout_seconds: float = 20.0) -> Tuple[bool, Optional[str]]:
    """
    Subprocess fallback for headless validation.
    """
    test_harness = f"""
import sys
import os
sys.path.append('{str(PROJECT_ROOT)}')

from manim import *
from manim_engine.primitives.typography import CleanText

# Headless fast validation config
config.dry_run = True
config.write_to_movie = False
config.quality = "low_quality"
config.verbosity = "WARNING"

{code_str}

scene = Scene()
visual = BespokeBeatVisual()

# 1. Bounding Box & Dimension Validation
width = visual.width
height = visual.height
center = visual.get_center()

if width > {MAX_VISUAL_WIDTH}:
    raise ValueError(f"Visual width ({{width:.2f}}) exceeds 9:16 safe-zone width {MAX_VISUAL_WIDTH}")
if height > {MAX_VISUAL_HEIGHT}:
    raise ValueError(f"Visual height ({{height:.2f}}) exceeds 9:16 safe-zone height {MAX_VISUAL_HEIGHT}")

from pipeline.code_sandbox import check_mobject_collisions_and_bounds
bounds_ok, bounds_err = check_mobject_collisions_and_bounds(visual)
if not bounds_ok:
    raise ValueError(bounds_err)

# 2. Animation Execution Validation
scene.add(visual)
ent_anim = visual.get_entrance_animation(run_time=0.1)
scene.play(ent_anim)

kin_anim = visual.get_kinetic_animation(run_time=0.1)
scene.play(kin_anim)

if "get_ambient_animation" in visual.__class__.__dict__:
    amb_anim = visual.get_ambient_animation(run_time=0.1)
    if amb_anim is not None:
        scene.play(amb_anim)

print("SUCCESS_DRY_RUN_OK")
"""

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(test_harness)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(PROJECT_ROOT)
        )
        if proc.returncode != 0:
            combined_err = f"{proc.stdout}\n{proc.stderr}".strip()
            tb_lines = [
                line for line in combined_err.splitlines()
                if not line.startswith("Manim Community v")
                and "ev_poll_posix" not in line
                and "FD from fork" not in line
                and "gRPC" not in line
            ]
            return False, "\n".join(tb_lines[-12:]) if tb_lines else "Subprocess failed with non-zero exit code"
        if "SUCCESS_DRY_RUN_OK" in proc.stdout:
            return True, None
        return False, f"Unexpected dry-run output: {proc.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout_seconds}s"
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def validate_synthesized_visual_code(code_str: str) -> Tuple[bool, Optional[str]]:
    """Complete 2-stage verification: AST safety check followed by fast in-process dry-run."""
    ast_ok, ast_err = validate_code_ast(code_str)
    if not ast_ok:
        return False, ast_err

    # Try fast in-process execution check first
    run_ok, run_err = validate_code_in_process(code_str)
    if run_ok:
        return True, None

    # If in-process had a collision or bounds violation, do not fallback to subprocess
    if run_err and any(indicator in run_err for indicator in ("Collision", "Safe-Zone", "Container", "overflow", "width", "height")):
        return False, run_err

    # If in-process had an issue (or missing manim), verify via isolated subprocess
    return validate_code_headless_execution(code_str)

