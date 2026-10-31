"""Topic-aware visual recipes for mechanism-first Manim beats.

The language model still composes the final scene, but it receives a concrete
causal drawing plan instead of a generic request for a "technical visual".
The recipes are deliberately renderer-agnostic: they describe the objects and
relationships that must be visible, while the synthesizer chooses the exact
Manim primitives.
"""

from __future__ import annotations

import re
from typing import Any, Dict


MECHANISM_RECIPES: Dict[str, Dict[str, Any]] = {
    "diffusion_flow": {
        "aliases": ("diffusion", "flow matching", "flow field", "rectified flow", "denois"),
        "visual_goal": "Show noisy latent particles being advected by a velocity field toward a structured target.",
        "hero_objects": "fixed streamlines or curved trajectories, particles travelling on them, and a target manifold or shape",
        "motion": "move particles along the field first, then transform the field/target to reveal the straighter learned path",
        "proof": "the path becomes shorter or more coherent while the particles converge",
        "avoid": "a cloud of decorative dots, a generic progress bar, or a static before/after card",
        "label": "FIELD → TRAJECTORY",
    },
    "attention_cache": {
        "aliases": ("attention", "kv cache", "multi-head latent", "mla", "key-value", "latent attention"),
        "visual_goal": "Show a query reading stored keys and values, then compressing redundant memory into a shared latent state.",
        "hero_objects": "query token, key/value memory slots, a bottleneck latent vector, and reconstruction arrows",
        "motion": "route the query through the stored state, collapse repeated key/value branches into one latent path, then fan the result back out",
        "proof": "many memory branches become one compact state without losing the outgoing attention routes",
        "avoid": "a spreadsheet-like matrix, a wall of identical cache boxes, or an isolated memory meter",
        "label": "QUERY → LATENT → HEADS",
    },
    "moe_routing": {
        "aliases": ("mixture of experts", "moe", "expert routing", "router", "sparse expert"),
        "visual_goal": "Show a router assigning each token to a small subset of experts instead of activating every path.",
        "hero_objects": "token particles, a router node, expert nodes, weighted route arrows, and a muted inactive path",
        "motion": "tokens enter the router, split along selected paths, and merge after expert processing",
        "proof": "only selected experts brighten and carry particles while the unused graph remains quiet",
        "avoid": "six labeled circles with no routing motion, a generic network wallpaper, or all experts glowing at once",
        "label": "ROUTE TOP-K",
    },
    "speculative_decoding": {
        "aliases": ("speculative decoding", "draft model", "draft token", "verification", "verify token"),
        "visual_goal": "Show a cheap draft branch proposing several tokens and a verifier accepting the matching prefix in one pass.",
        "hero_objects": "draft token chain, verifier gate, accepted prefix, and a rejected branch",
        "motion": "draft tokens advance quickly, the verifier sweep travels across the chain, then accepted tokens lock while one mismatch peels away",
        "proof": "multiple accepted tokens advance the sequence per verification step",
        "avoid": "a generic latency bar, a UI table of token names, or a split-screen card comparison",
        "label": "DRAFT → VERIFY",
    },
    "latent_compression": {
        "aliases": ("compression", "low-rank", "latent vector", "projection", "factorization", "rank"),
        "visual_goal": "Show a high-dimensional structure projected onto a compact latent axis and reconstructed from that axis.",
        "hero_objects": "source lattice or matrix, projection rays, a compact axis, and a reconstruction fan",
        "motion": "project points onto the compact axis, compress them into a moving latent packet, then reconstruct the output geometry",
        "proof": "many source coordinates share one compact representation while the output preserves the important shape",
        "avoid": "a shrinking rectangle with no projection relationship or a numeric badge standing in for compression",
        "label": "PROJECT → COMPRESS → REBUILD",
    },
    "generic_mechanism": {
        "aliases": (),
        "visual_goal": "Show the subject's causal transformation with connected geometry rather than a summary panel.",
        "hero_objects": "one dominant object, one source or constraint, and one visible transformation path",
        "motion": "animate the source acting on the hero object and expose the resulting state change",
        "proof": "the geometry makes the claimed improvement visible without relying on a metric card",
        "avoid": "generic cards, repeated status badges, and disconnected decorative shapes",
        "label": "CAUSE → EFFECT",
    },
}


def _search_text(spec: Dict[str, Any], beat: Dict[str, Any]) -> str:
    fields = [
        spec.get("id"),
        spec.get("title"),
        spec.get("domain_taxonomy"),
        spec.get("hook_tag"),
        spec.get("physical_analogy"),
        beat.get("text"),
        beat.get("visual_focus"),
        beat.get("math_formula"),
        beat.get("svo_action", {}).get("subject"),
        beat.get("svo_action", {}).get("direct_object"),
        beat.get("visual_blueprint", {}).get("title"),
        beat.get("visual_blueprint", {}).get("sub"),
    ]
    return " ".join(str(value or "") for value in fields).lower()


def resolve_mechanism_family(spec: Dict[str, Any], beat: Dict[str, Any]) -> str:
    """Resolve a topic family using stable domain and narrative signals."""
    text = _search_text(spec, beat)
    ordered = (
        "diffusion_flow",
        "speculative_decoding",
        "moe_routing",
        "attention_cache",
        "latent_compression",
    )
    for family in ordered:
        aliases = MECHANISM_RECIPES[family]["aliases"]
        if any(re.search(rf"\b{re.escape(alias)}\b", text) for alias in aliases):
            return family
    return "generic_mechanism"


def mechanism_recipe(spec: Dict[str, Any], beat: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy-safe recipe enriched with the selected topic family."""
    family = resolve_mechanism_family(spec, beat)
    recipe = dict(MECHANISM_RECIPES[family])
    recipe["family"] = family
    return recipe


def mechanism_prompt_block(spec: Dict[str, Any], beat: Dict[str, Any]) -> str:
    """Format the recipe as an explicit art-direction block for the model."""
    recipe = mechanism_recipe(spec, beat)
    return "\n".join(
        (
            f"Mechanism family: {recipe['family']}",
            f"Visual goal: {recipe['visual_goal']}",
            f"Hero objects: {recipe['hero_objects']}",
            f"Required motion: {recipe['motion']}",
            f"Visible proof: {recipe['proof']}",
            f"Avoid: {recipe['avoid']}",
            f"Optional short label: {recipe['label']}",
        )
    )


def validate_mechanism_semantics(code_str: str, spec: Dict[str, Any], beat: Dict[str, Any]) -> tuple[bool, str | None]:
    """Reject obvious cross-topic drift that structural lint cannot see."""
    family = resolve_mechanism_family(spec, beat)
    source = code_str.lower()
    requirements = {
        "diffusion_flow": ("field", "trajectory", "stream", "flow", "particle"),
        "attention_cache": ("query", "cache", "latent", "key", "value", "head"),
        "moe_routing": ("router", "expert", "route", "top-k"),
        "speculative_decoding": ("draft", "verify", "accept", "token"),
        "latent_compression": ("project", "compress", "latent", "rank", "rebuild"),
        "generic_mechanism": (),
    }
    required = requirements[family]
    if required and not any(term in source for term in required):
        return False, f"Mechanism semantic contract: generated scene does not name or draw the required {family.replace('_', ' ')} relationship."

    forbidden = {
        "diffusion_flow": ("attention map", "kv cache", "mixture of experts", "draft token"),
        "attention_cache": ("attention map",),
        "moe_routing": ("attention map", "diffusion field"),
        "speculative_decoding": ("attention map", "diffusion field"),
        "latent_compression": ("attention map", "diffusion field"),
        "generic_mechanism": (),
    }
    for phrase in forbidden[family]:
        if phrase in source:
            return False, f"Mechanism semantic contract: '{phrase}' belongs to another topic family; redraw the assigned mechanism."
    return True, None

