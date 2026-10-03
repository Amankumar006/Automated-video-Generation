"""
The Model Verse — Robust LLM JSON Sanitizer & Parser
Handles arbitrary LaTeX backslashes, unescaped control chars, trailing commas,
and markdown fences produced by LLMs (Gemini, Claude, GPT).
"""

import json
import re
from typing import Any, Dict, Optional

try:
    import dirtyjson
    HAS_DIRTYJSON = True
except ImportError:
    HAS_DIRTYJSON = False


def sanitize_llm_json(raw: str) -> str:
    r"""
    Bulletproof sanitization of LLM-generated JSON:
    1. Extracts outermost JSON object { ... } and strips markdown code fences.
    2. Scans inside string literals and escapes any invalid JSON escape sequences
       (like LaTeX backslashes \mathrm, \alpha, \frac, \utilization, \tau, etc.).
    3. Preserves legitimate escapes: \", \\, \/, \n, \r, \t (when not a LaTeX command),
       and valid \uXXXX unicode escapes.
    4. Strips trailing commas.
    5. Balances unmatched brackets/braces if the LLM output was truncated.
    """
    if not raw:
        return "{}"

    text = raw.strip()

    # 1. Strip markdown code fence if present
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            text = m.group(1).strip()
        else:
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()

    # Find the outermost { and }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace + 1]

    # 2. Character-by-character scan inside JSON string literals
    out = []
    i = 0
    n = len(text)
    in_string = False

    while i < n:
        c = text[i]
        if not in_string:
            if c == "\"":
                in_string = True
                out.append(c)
                i += 1
            else:
                out.append(c)
                i += 1
        else:
            if c == "\"":
                in_string = False
                out.append(c)
                i += 1
            elif c == "\\":
                if i + 1 >= n:
                    # Trailing backslash at the very end
                    out.append("\\\\")
                    i += 1
                    continue

                nxt = text[i + 1]
                # Escaped quote \" or forward slash \/
                if nxt in ("\"", "/"):
                    out.append("\\")
                    out.append(nxt)
                    i += 2
                # Escaped backslash \\
                elif nxt == "\\":
                    out.append("\\\\")
                    i += 2
                # Unicode escape: \uXXXX (strictly 4 hex digits)
                elif nxt == "u":
                    if i + 5 < n and all(ch in "0123456789abcdefABCDEF" for ch in text[i + 2:i + 6]):
                        out.append("\\u")
                        out.append(text[i + 2:i + 6])
                        i += 6
                    else:
                        # e.g. \utilization, \uparrow, \underline -> escape the backslash!
                        out.append("\\\\")
                        out.append(nxt)
                        i += 2
                # Control character escapes: \b, \f, \n, \r, \t
                # In LaTeX, math commands often start with these letters:
                # e.g. \frac, \beta, \text, \times, \tau, \nabla, \rho, etc.
                elif nxt in ("b", "f", "n", "r", "t"):
                    latex_starters = {
                        "f": ("frac", "forall", "flat", "fbox"),
                        "b": ("beta", "bar", "begin", "mathbf", "boldsymbol", "bmod", "big", "bullet", "bmatrix", "binom"),
                        "r": ("rho", "right", "rangle", "rm", "rightarrow", "Rightarrow", "real"),
                        "t": ("text", "times", "tau", "theta", "tilde", "to", "top", "textbf", "textit", "tan", "tr"),
                        "n": ("nabla", "neq", "neg", "nu", "norm", "notin", "not", "natural", "ni"),
                    }
                    is_latex = any(text.startswith(cmd, i + 1) for cmd in latex_starters.get(nxt, ()))
                    if is_latex:
                        out.append("\\\\")
                        out.append(nxt)
                        i += 2
                    else:
                        out.append("\\")
                        out.append(nxt)
                        i += 2
                else:
                    # Invalid escape in JSON (e.g. \m in \mathrm, \a in \alpha, \s in \sum, \ , \%, \_, etc.)
                    # Escape the backslash so JSON receives a literal backslash
                    out.append("\\\\")
                    out.append(nxt)
                    i += 2
            else:
                out.append(c)
                i += 1

    sanitized = "".join(out)

    # 3. Remove trailing commas before } or ]
    sanitized = re.sub(r",\s*([\]}])", r"\1", sanitized)

    # 4. Auto-balance unmatched brackets/braces if truncated
    open_curly = sanitized.count("{") - sanitized.count("}")
    open_square = sanitized.count("[") - sanitized.count("]")
    if open_square > 0:
        sanitized += "]" * open_square
    if open_curly > 0:
        sanitized += "}" * open_curly

    return sanitized


def robust_json_loads(raw: str, fallback_defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Attempts to decode a JSON string using progressive error-recovery:
    1. Standard json.loads(..., strict=False)
    2. sanitize_llm_json() + json.loads(..., strict=False)
    3. dirtyjson.loads() (if available)
    4. fallback_defaults (if provided) or raises JSONDecodeError
    """
    if not raw or not raw.strip():
        if fallback_defaults is not None:
            return fallback_defaults
        raise ValueError("Empty string provided to robust_json_loads")

    # Step 1: Direct JSON parsing
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        pass

    # Step 2: Sanitized parsing
    sanitized = sanitize_llm_json(raw)
    try:
        return json.loads(sanitized, strict=False)
    except json.JSONDecodeError as err:
        # Step 3: dirtyjson fallback
        if HAS_DIRTYJSON:
            try:
                dj_obj = dirtyjson.loads(sanitized)
                # Convert dirtyjson Dict/List types to standard Python dicts/lists
                return json.loads(json.dumps(dj_obj))
            except Exception:
                pass

        if fallback_defaults is not None:
            print(f"⚠️ robust_json_loads: All recovery attempts failed ({err}). Using fallback defaults.")
            return fallback_defaults

        raise err
