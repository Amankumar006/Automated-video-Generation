"""
Generates high-precision mathematical vector SVGs using Matplotlib's MathText engine.
Provides authentic Computer Modern / LaTeX mathematical notation without requiring pdflatex.
"""

import os
import matplotlib.pyplot as plt

os.makedirs("public/math_svgs", exist_ok=True)

import xml.etree.ElementTree as ET
import re

def sanitize_latex(latex_str: str) -> str:
    """Sanitizes LaTeX strings for Matplotlib mathtext compatibility."""
    if not latex_str:
        return latex_str
    # Replace \text{...} with \mathrm{...}
    cleaned = re.sub(r'\\text\{([^}]+)\}', r'\\mathrm{\1}', latex_str)
    # Strip \underbrace{...}_{...} or \underbrace{...}
    cleaned = re.sub(r'\\underbrace\{([^}]+)\}(?:_\{[^}]+\})?', r'\1', cleaned)
    # Strip \overbrace{...}^{...} or \overbrace{...}
    cleaned = re.sub(r'\\overbrace\{([^}]+)\}(?:\^\{[^}]+\})?', r'\1', cleaned)
    # Replace \mathbb{R} with \mathbf{R}
    cleaned = re.sub(r'\\mathbb\{([A-Za-z])\}', r'\\mathbf{\1}', cleaned)
    # Fix dollar signs reliably
    cleaned = cleaned.strip("$").strip()
    return f"${cleaned}$"

def render_math_to_svg(latex_str: str, filename: str, fontsize: int = 24, color: str = "white"):
    clean_latex = sanitize_latex(latex_str)
    fig = plt.figure(figsize=(6, 1.2))
    fig.patch.set_alpha(0.0)
    # Render with Computer Modern math font
    plt.rcParams['mathtext.fontset'] = 'cm'
    fig.text(0.5, 0.5, clean_latex, fontsize=fontsize, color=color, ha='center', va='center')
    filepath = os.path.join("public/math_svgs", filename)
    plt.savefig(filepath, format='svg', transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    
    # Post-process XML for svgelements / Manim compatibility
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Remove background patch_1 bounding box so Manim doesn't render phantom lines
    for g in list(root.iter()):
        for child in list(g):
            if child.attrib.get('id') == 'patch_1':
                g.remove(child)

    for elem in root.iter():
        if elem.tag.endswith('path') and 'd' not in elem.attrib:
            elem.set('d', 'M 0 0')
    tree.write(filepath, encoding='utf-8')
    
    print(f"✅ Generated and patched math SVG: {filepath}")
    return filepath



if __name__ == "__main__":
    # 1. Parameter scale notation
    render_math_to_svg(r"$N = 671 \times 10^9 \text{ Parameters}$", "param_scale.svg", fontsize=28)
    
    # 2. Dense Matrix multiplication
    render_math_to_svg(r"$\mathbf{y} = W \cdot \mathbf{x} \quad (W \in \mathbb{R}^{d \times d})$", "dense_matmul.svg", fontsize=24)
    render_math_to_svg(r"$\mathcal{O}(d^2) \text{ operations per token}$", "dense_compute.svg", fontsize=22)
    
    # 3. MoE Partition
    render_math_to_svg(r"$W \longrightarrow \{E_1, E_2, \dots, E_{256}\} \oplus E_s$", "moe_partition.svg", fontsize=24)
    
    # 4. Gating router formula
    render_math_to_svg(r"$\mathrm{Gate}(\mathbf{x}) = \mathrm{Top8}\left( \sigma(W_g \mathbf{x} + b) \right)$", "gating_formula.svg", fontsize=24)
    render_math_to_svg(r"$E_s(\mathbf{x}) \quad \text{Shared Foundation Expert}$", "shared_expert.svg", fontsize=22)
    
    # 5. MoE Synthesis output equation
    render_math_to_svg(r"$\mathbf{y} = \sum_{i \in \mathrm{Top8}} g_i E_i(\mathbf{x}) + E_s(\mathbf{x})$", "moe_output.svg", fontsize=26)
    
    # 6. Active efficiency equation
    render_math_to_svg(r"$\frac{37\text{B Active}}{671\text{B Total}} = 5.5\% \quad \Rightarrow \quad 94.5\% \text{ Compute Saved}$", "efficiency_math.svg", fontsize=22)
    render_math_to_svg(r"$\text{Active Compute: } 37\text{B} \ll 671\text{B}$", "flop_reduction.svg", fontsize=24)
    
    # 7. Dedicated glyph for Shared Expert node
    render_math_to_svg(r"$E_s$", "es_glyph.svg", fontsize=32, color="black")

    # 8. Benchmark News formulas
    render_math_to_svg(r"$\mathrm{AIME\,2024}: 79.8\% \quad (\text{Pass@1})$", "aime_benchmark.svg", fontsize=24, color="#34D399")
    render_math_to_svg(r"$\mathrm{MATH\text{-}500}: 97.3\% \quad \text{Accuracy}$", "math500_score.svg", fontsize=24, color="#F59E0B")
    render_math_to_svg(r"$\mathcal{J}_{\mathrm{GRPO}}(\theta) = \mathbb{E}_{q, \{o_i\}}\left[\frac{1}{G}\sum_{i=1}^G \min\left(r_i \hat{A}_i, \text{clip}(r_i)\hat{A}_i\right)\right]$", "grpo_formula.svg", fontsize=20, color="white")
    render_math_to_svg(r"$\frac{\text{Cost}_{\mathrm{R1}}}{\text{Cost}_{\mathrm{o1}}} = \frac{\$0.55}{\$15.00} = 3.7\% \quad \Rightarrow \quad 27\times \text{Cheaper}$", "cost_disparity_r1.svg", fontsize=21, color="#34D399")
    render_math_to_svg(r"$\Delta \mathrm{Score} = +14.4\% \quad (\text{Codeforces } 96.3^{\mathrm{th}} \% \text{ile})$", "accuracy_delta.svg", fontsize=22, color="#38BDF8")


