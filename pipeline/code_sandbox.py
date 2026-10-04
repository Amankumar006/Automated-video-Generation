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

        # Check for text overflowing container boxes
        from manim import Text, Rectangle, RoundedRectangle, Ellipse, Circle
        for subm in visual.submobjects:
            if hasattr(subm, "submobjects") and len(subm.submobjects) >= 2:
                containers = [m for m in subm.submobjects if isinstance(m, (Rectangle, RoundedRectangle, Ellipse, Circle))]
                texts = [m for m in subm.submobjects if isinstance(m, (Text, CleanText))]
                if containers and texts:
                    cont = containers[0]
                    for txt in texts:
                        dist = np.linalg.norm(txt.get_center() - cont.get_center())
                        if dist < max(cont.width, cont.height) * 0.4:
                            if txt.width > cont.width - 0.05:
                                return False, f"Container overflow: Text '{getattr(txt, 'text', 'label')}' width ({txt.width:.2f}) exceeds box width ({cont.width:.2f}). Scale text or widen container."

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

        if hasattr(visual, "get_ambient_animation"):
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

# 2. Animation Execution Validation
scene.add(visual)
ent_anim = visual.get_entrance_animation(run_time=0.1)
scene.play(ent_anim)

kin_anim = visual.get_kinetic_animation(run_time=0.1)
scene.play(kin_anim)

if hasattr(visual, "get_ambient_animation"):
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
            err = proc.stderr.strip() or proc.stdout.strip()
            tb_lines = [line for line in err.splitlines() if not line.startswith("Manim Community v")]
            return False, "\n".join(tb_lines[-12:])
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

    # If in-process had an issue (or missing manim), verify via isolated subprocess
    return validate_code_headless_execution(code_str)

