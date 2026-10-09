"""Project Aether Multi-Critic VLM Context Cache Manager.

Implements prefix caching and prompt structuring with static prefix ordering
(cache_control breakpoints for Anthropic Claude, and Gemini Context Caching markers)
so repetitive video frame tensors, scene graph schemas, and critic rubrics
achieve 90% token cost discounts across the 6 specialized critics (WBS 1.5 / RSK-003).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from aether.compiler.schemas import ShotRequirement
from aether.council.schemas import CriticType, HardGateType
from aether.state.schemas import SceneState


# Standard Project Aether Master Rubrics for VLM Critic Inspections
MASTER_COUNCIL_RUBRIC = """# PROJECT AETHER MULTI-CRITIC INSPECTION PROTOCOL
Enforce strict physical, anatomical, and cinematic standards across candidate video shots.

## CRITICAL HARD GATES (BINARY PASS / FAIL):
1. ANATOMICAL_INTEGRITY: Zero tolerance for polydactyly, extra limbs, fused digits, or morphing facial geometry.
2. CHARACTER_IDENTITY: Persistent facial features, hair, eye color, wardrobe state, and visible injuries.
3. PROP_CONTINUITY: Held props must not teleport, spontaneously duplicate, or disappear during handoffs.
4. LIP_SYNC_ALIGNMENT: Phoneme-viseme temporal synchronization within +/- 45ms.
5. PHYSICAL_TRAJECTORY: Adherence to gravity, parabolic arcs, inertia, and non-penetrating collision boundaries.

## SOFT AESTHETIC DIMENSIONS (0.0 - 10.0):
- Cinematography & Lighting consistency
- Visual Aesthetic fidelity & grain texture
- Narrative Pacing & dramatic tension
"""

CRITIC_SPECIFIC_RUBRICS: Dict[CriticType, str] = {
    CriticType.VISUAL: (
        "Focus on anatomical structure, digit count, facial symmetry, texture resolution, "
        "and absence of AI generation artifacts (plastic skin, floating limbs)."
    ),
    CriticType.TEMPORAL: (
        "Focus on frame-to-frame coherence, temporal flickering, strobing artifacts, "
        "motion vector consistency, and edge boundary jitter across cuts."
    ),
    CriticType.CONTINUITY: (
        "Focus on scene state persistence, actor position relative to previous beat, "
        "wardrobe wear/damage consistency, and persistent environmental lighting."
    ),
    CriticType.PERFORMANCE: (
        "Focus on actor emotional micro-expressions, eyeline vectors, head orientation, "
        "and synchronous mouth/lip movements during dialogue lines."
    ),
    CriticType.PHYSICS: (
        "Focus on kinematics, rigid/soft body collisions, fluid splashing realism, "
        "clothing drape dynamics, and realistic mass/momentum interaction."
    ),
    CriticType.AUDIO: (
        "Focus on speech clarity, background foley acoustic matching, spatial reverb, "
        "and dynamic range without digital clipping or phasing distortion."
    ),
}


class VLMContextCacheManager:
    """Manages static prefix ordering and context cache payloads for multi-critic VLM queries."""

    def __init__(
        self,
        master_rubric: Optional[str] = None,
        cached_ttl_seconds: int = 300,
        model_gemini: str = "gemini-2.5-pro",
        model_anthropic: str = "claude-3-7-sonnet-20250219",
    ) -> None:
        self.master_rubric = master_rubric or MASTER_COUNCIL_RUBRIC.strip()
        self.cached_ttl_seconds = cached_ttl_seconds
        self.model_gemini = model_gemini
        self.model_anthropic = model_anthropic

    # -----------------------------------------------------------------------
    # 1. Deterministic Cache Key
    # -----------------------------------------------------------------------

    def compute_prefix_cache_key(
        self,
        scene_state: Optional[Union[SceneState, Dict[str, Any]]] = None,
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        frame_uris: Optional[Sequence[str]] = None,
    ) -> str:
        """Computes deterministic SHA256 cache key representing the frozen static prefix."""
        hasher = hashlib.sha256()
        hasher.update(self.master_rubric.encode("utf-8"))

        if scene_state:
            s_dict = scene_state if isinstance(scene_state, dict) else scene_state.model_dump(mode="json")
            hasher.update(json.dumps(s_dict, sort_keys=True).encode("utf-8"))

        if shot_requirement:
            r_dict = shot_requirement if isinstance(shot_requirement, dict) else shot_requirement.model_dump(mode="json")
            hasher.update(json.dumps(r_dict, sort_keys=True).encode("utf-8"))

        if frame_uris:
            hasher.update(",".join(sorted(frame_uris)).encode("utf-8"))

        return hasher.hexdigest()

    # -----------------------------------------------------------------------
    # 2. Static Prefix Serialization
    # -----------------------------------------------------------------------

    def _format_scene_context_block(
        self,
        scene_state: Optional[Union[SceneState, Dict[str, Any]]] = None,
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
    ) -> str:
        """Formats immutable scene metadata block."""
        parts = ["## SCENE CONTEXT & ACTIVE SHOT REQUIREMENTS"]

        if shot_requirement:
            req = shot_requirement if isinstance(shot_requirement, ShotRequirement) else ShotRequirement(**shot_requirement)
            parts.append(
                f"- Shot ID: {req.shot_id} | Duration: {req.target_duration}s | Aspect: {req.aspect_ratio} | Res: {req.resolution}\n"
                f"- Focal Intent: {req.target_focal_intent or 'Default cinematic'}\n"
                f"- Camera Motion: {req.camera_movement or 'Static'} ({req.camera_velocity_mps:.1f} m/s)\n"
                f"- Active Characters: {', '.join(req.character_ids_involved) or 'None specified'}\n"
                f"- Continuity Critical: {req.continuity_critical}"
            )
            if req.has_dialogue:
                parts.append(f"- Spoken Dialogue: \"{req.audio.dialogue_transcript or 'Unspecified speech'}\"")

        if scene_state:
            st = scene_state if isinstance(scene_state, SceneState) else SceneState(**scene_state)
            parts.append(
                f"- Location: {st.location} | Timestamp: {st.timestamp}\n"
                f"- Environment: {st.environment.weather} weather, {st.environment.lighting} lighting, wetness {st.environment.wetness:.2f}"
            )
            if st.character_roster:
                char_summaries = []
                for cid, char in st.character_roster.items():
                    char_summaries.append(f"  * {char.name or cid}: emotional_state={char.emotional_state}, facing={char.facing_angle:.0f}°")
                parts.append("- Character Roster:\n" + "\n".join(char_summaries))

        return "\n\n".join(parts)

    def _format_frame_references_block(self, frame_uris: Optional[Sequence[str]] = None) -> str:
        """Formats repetitive video frame tensor / URI inspection block."""
        if not frame_uris:
            return "## VIDEO FRAMES UNDER INSPECTION\n[No discrete keyframes provided; evaluating stream]"
        uris_str = "\n".join(f"- Frame [{i:03d}]: {uri}" for i, uri in enumerate(frame_uris))
        return f"## VIDEO FRAMES UNDER INSPECTION ({len(frame_uris)} frames loaded):\n{uris_str}"

    # -----------------------------------------------------------------------
    # 3. Anthropic Claude Prefix Caching Payload
    # -----------------------------------------------------------------------

    def build_anthropic_payload(
        self,
        critic_type: Union[CriticType, str],
        query: Optional[str] = None,
        scene_state: Optional[Union[SceneState, Dict[str, Any]]] = None,
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        frame_uris: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Constructs an Anthropic Messages API payload with explicit cache_control breakpoints."""
        c_type = CriticType.from_str(critic_type)
        critic_rubric = CRITIC_SPECIFIC_RUBRICS.get(c_type, "")
        dynamic_query = query or (
            f"You are the {c_type.value} Critic for Project Aether. "
            f"Audit the candidate generation according to your domain rubric: {critic_rubric} "
            "Emit a structured report with hard gate PASS/FAIL, identified defects, and numeric score (0-10)."
        )

        scene_block = self._format_scene_context_block(scene_state, shot_requirement)
        frames_block = self._format_frame_references_block(frame_uris)

        # System message contains Master Rubric with cache_control breakpoint
        system_blocks = [
            {
                "type": "text",
                "text": self.master_rubric,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        # User message begins with static scene context & frames (cached), ending with dynamic critic query
        user_content_blocks = [
            {
                "type": "text",
                "text": scene_block,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": frames_block,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": dynamic_query,
            },
        ]

        cache_key = self.compute_prefix_cache_key(scene_state, shot_requirement, frame_uris)

        return {
            "model": self.model_anthropic,
            "system": system_blocks,
            "messages": [
                {
                    "role": "user",
                    "content": user_content_blocks,
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
            "_metadata": {
                "critic_type": c_type.value,
                "cache_provider": "anthropic",
                "cache_control_enabled": True,
                "prefix_cache_key": cache_key,
            },
        }

    # -----------------------------------------------------------------------
    # 4. Google Gemini Context Caching Payload
    # -----------------------------------------------------------------------

    def build_gemini_payload(
        self,
        critic_type: Union[CriticType, str],
        query: Optional[str] = None,
        scene_state: Optional[Union[SceneState, Dict[str, Any]]] = None,
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        frame_uris: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Constructs a Google Gemini GenerateContent payload with context caching markers."""
        c_type = CriticType.from_str(critic_type)
        critic_rubric = CRITIC_SPECIFIC_RUBRICS.get(c_type, "")
        dynamic_query = query or (
            f"You are the {c_type.value} Critic for Project Aether. "
            f"Audit the candidate generation according to your domain rubric: {critic_rubric} "
            "Emit a structured report with hard gate PASS/FAIL, identified defects, and numeric score (0-10)."
        )

        scene_block = self._format_scene_context_block(scene_state, shot_requirement)
        frames_block = self._format_frame_references_block(frame_uris)
        cache_key = self.compute_prefix_cache_key(scene_state, shot_requirement, frame_uris)

        # Gemini static prefix includes master rubric, scene graph, and video frames
        static_prefix_text = (
            f"{self.master_rubric}\n\n"
            f"{scene_block}\n\n"
            f"{frames_block}"
        )

        return {
            "model": self.model_gemini,
            "cached_content": f"cachedContents/aether_council_{cache_key[:16]}",
            "cached_content_config": {
                "name": f"cachedContents/aether_council_{cache_key[:16]}",
                "ttl": f"{self.cached_ttl_seconds}s",
                "model": self.model_gemini,
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": static_prefix_text}],
                        "gemini_cache_marker": True,
                    }
                ],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": dynamic_query}],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 2048,
            },
            "_metadata": {
                "critic_type": c_type.value,
                "cache_provider": "gemini",
                "gemini_cache_marker": True,
                "prefix_cache_key": cache_key,
                "ttl_seconds": self.cached_ttl_seconds,
            },
        }

    # -----------------------------------------------------------------------
    # 5. Multi-Critic Batch Formatting & Cost Telemetry
    # -----------------------------------------------------------------------

    def format_council_batch(
        self,
        scene_state: Optional[Union[SceneState, Dict[str, Any]]] = None,
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        frame_uris: Optional[Sequence[str]] = None,
        critic_types: Optional[List[CriticType]] = None,
        provider: str = "anthropic",
    ) -> Dict[CriticType, Dict[str, Any]]:
        """Formats the entire suite of 6 critic queries sharing the identical cached prefix."""
        target_critics = critic_types or [
            CriticType.VISUAL,
            CriticType.TEMPORAL,
            CriticType.CONTINUITY,
            CriticType.PERFORMANCE,
            CriticType.PHYSICS,
            CriticType.AUDIO,
        ]

        batch: Dict[CriticType, Dict[str, Any]] = {}
        for c_type in target_critics:
            c_enum = CriticType.from_str(c_type)
            if provider.lower() == "gemini":
                batch[c_enum] = self.build_gemini_payload(
                    critic_type=c_enum,
                    scene_state=scene_state,
                    shot_requirement=shot_requirement,
                    frame_uris=frame_uris,
                )
            else:
                batch[c_enum] = self.build_anthropic_payload(
                    critic_type=c_enum,
                    scene_state=scene_state,
                    shot_requirement=shot_requirement,
                    frame_uris=frame_uris,
                )

        return batch

    @staticmethod
    def calculate_token_savings(
        total_tokens_per_call: int,
        cached_prefix_tokens: int,
        num_critics: int = 6,
        cost_per_million_input: float = 2.50,
        cached_discount_rate: float = 0.90,
    ) -> Dict[str, float]:
        """Calculates token costs and monetary savings enabled by prefix caching.

        With 6 critics running concurrently on identical video keyframes and rubrics,
        subsequent calls achieve a 90% discount on cached input tokens.
        """
        uncached_cost_per_token = cost_per_million_input / 1_000_000.0
        cached_cost_per_token = (cost_per_million_input * (1.0 - cached_discount_rate)) / 1_000_000.0

        # Baseline: All critics pay full price for all tokens
        baseline_cost = num_critics * total_tokens_per_call * uncached_cost_per_token

        # With caching: First critic pays full input price for prefix.
        # Remaining (num_critics - 1) critics pay discounted price for prefix.
        # Dynamic tokens always pay full input price.
        dynamic_tokens = max(0, total_tokens_per_call - cached_prefix_tokens)

        first_call_cost = total_tokens_per_call * uncached_cost_per_token
        subsequent_calls_cost = (num_critics - 1) * (
            (cached_prefix_tokens * cached_cost_per_token) + (dynamic_tokens * uncached_cost_per_token)
        )
        cached_total_cost = first_call_cost + subsequent_calls_cost

        savings = max(0.0, baseline_cost - cached_total_cost)
        discount_percentage = (savings / baseline_cost * 100.0) if baseline_cost > 0 else 0.0

        subsequent_call_cost = (cached_prefix_tokens * cached_cost_per_token) + (dynamic_tokens * uncached_cost_per_token)
        full_call_cost = total_tokens_per_call * uncached_cost_per_token
        subsequent_query_discount = (1.0 - (subsequent_call_cost / full_call_cost)) * 100.0 if full_call_cost > 0 else 0.0

        return {
            "baseline_cost_usd": round(baseline_cost, 6),
            "cached_total_cost_usd": round(cached_total_cost, 6),
            "savings_usd": round(savings, 6),
            "discount_percentage": round(discount_percentage, 2),
            "prefix_discount_percentage": round(cached_discount_rate * 100.0, 2),
            "subsequent_query_discount_percentage": round(subsequent_query_discount, 2),
            "num_critics": num_critics,
            "cached_prefix_tokens": cached_prefix_tokens,
            "total_tokens_per_call": total_tokens_per_call,
        }
