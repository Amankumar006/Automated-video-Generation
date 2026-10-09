"""
The Model Verse — Persistent Retention Genome Memory Ledger (Engine 7.0)
Stores, updates, and evolves the algorithmic recipes of winning vs. losing
hooks, visual blueprints, physical analogies, and pacing across generations.
"""

import os
import re
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GENOME_PATH = DATA_DIR / "retention_genome.json"


# Default seed priors calibrated to YouTube Shorts engineering audience distributions
DEFAULT_GENOME: Dict[str, Any] = {
    "version": "7.0",
    "generation": 1,
    "last_evolved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "total_autopsies_recorded": 0,
    "pacing": {
        "recommended_tts_speed": 1.12,
        "recommended_wpm": 165,
        "max_hook_duration_s": 3.0,
        "optimal_total_duration_s": 48.0
    },
    "hook_archetypes": {
        "absurd_paradox": {
            "score": 9.0,
            "avg_3s_retention": 82.5,
            "sample_count": 5,
            "description": "Shocking compute waste, paradoxical inefficiency, or inverted expectations directly from the paper."
        },
        "shock_metric": {
            "score": 8.5,
            "avg_3s_retention": 79.0,
            "sample_count": 4,
            "description": "Explosive benchmark disparity or order-of-magnitude leap (e.g. 10x faster or major efficiency gain)."
        },
        "villain_first": {
            "score": 8.2,
            "avg_3s_retention": 76.5,
            "sample_count": 3,
            "description": "Immediate identification of the mechanical bottleneck suffocating modern AI."
        },
        "curiosity_trap": {
            "score": 8.4,
            "avg_3s_retention": 78.0,
            "sample_count": 3,
            "description": "Revealing hidden mechanics behind complex algorithms and architectures."
        },
        "textbook_lecture": {
            "score": 2.0,
            "avg_3s_retention": 45.0,
            "sample_count": 2,
            "description": "BANNED: Academic openings ('Today we explore...', 'In this paper...'). Severe viewer drop-off."
        }
    },
    "visual_blueprints": {
        "BlueprintHorizontalRaceBars": {
            "multiplier": 1.30,
            "avg_retention": 78.5,
            "win_count": 6,
            "loss_count": 0,
            "recommendation": "PRIORITIZE for Act 4 benchmark showdown."
        },
        "BlueprintSplitFlow": {
            "multiplier": 1.25,
            "avg_retention": 76.0,
            "win_count": 5,
            "loss_count": 1,
            "recommendation": "EXCELLENT for bifurcated flows, dual-pass verification, or router dispatch."
        },
        "BlueprintGridMemory": {
            "multiplier": 1.20,
            "avg_retention": 74.5,
            "win_count": 5,
            "loss_count": 1,
            "recommendation": "STRONG for VRAM, SRAM, KV cache tiling, and matrix memory walls."
        },
        "BlueprintChalkboardCodeBlock": {
            "multiplier": 1.22,
            "avg_retention": 75.0,
            "win_count": 4,
            "loss_count": 0,
            "recommendation": "HIGH RETENTION with developer audiences when active line sweep is synced to audio."
        },
        "BlueprintPipelineStages": {
            "multiplier": 1.15,
            "avg_retention": 71.0,
            "win_count": 4,
            "loss_count": 1,
            "recommendation": "SOLID for multistage pipelines (prefill, decode, verify)."
        },
        "BlueprintTreeHierarchy": {
            "multiplier": 1.10,
            "avg_retention": 69.5,
            "win_count": 3,
            "loss_count": 1,
            "recommendation": "GOOD for speculative verification trees and Monte Carlo search."
        },
        "generic_sine_wave": {
            "multiplier": 0.50,
            "avg_retention": 46.0,
            "win_count": 0,
            "loss_count": 4,
            "recommendation": "BANNED: Flat generic animation trigger. Causes immediate cognitive drop-off."
        }
    },
    "physical_analogies": {
        "assembly_line_stall": {"score": 9.2, "sample_count": 4, "status": "elite"},
        "relay_race_baton_drop": {"score": 8.7, "sample_count": 3, "status": "active"},
        "highway_traffic_bottleneck": {"score": 8.5, "sample_count": 3, "status": "active"},
        "sculpting_marble": {"score": 8.3, "sample_count": 2, "status": "active"},
        "toy_safe_drawers": {"score": 2.0, "sample_count": 2, "status": "banned_baby_talk"}
    }
}


class RetentionGenomeLedger:
    """
    Manages persistent genome memory, incorporates live autopsy findings,
    and evolves algorithmic priors over time.
    """

    def __init__(self, ledger_path: Path = GENOME_PATH):
        self.ledger_path = ledger_path
        self.genome = self._load_or_initialize()

    def _load_or_initialize(self) -> Dict[str, Any]:
        """Loads genome from disk or initializes with default priors."""
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "visual_blueprints" in data and "hook_archetypes" in data:
                        return data
            except Exception as e:
                print(f"⚠️ Could not read genome from {self.ledger_path} ({e}). Re-initializing.")

        # Ensure directory exists and write default
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_GENOME, f, indent=2)
        return dict(DEFAULT_GENOME)

    def save(self):
        """Persists genome to disk."""
        self.genome["last_evolved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(self.genome, f, indent=2)

    def record_autopsy(self, autopsy_report: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Incorporates autopsy report signals into the genome memory ledger:
        - Updates Hook Archetype 3s retention & score using exponential moving average.
        - Boosts winning visual blueprint multipliers; penalizes drop-off blueprints.
        - Evolves generation counter every 5 autopsies.
        """
        alpha = 0.35  # Learning rate / adaptation weight
        hook_3s = float(autopsy_report.get("hook_3s_retention_pct", 75.0))
        hook_passed = bool(autopsy_report.get("hook_passed", True))

        # 1. Update Hook Archetype
        hook_tag = spec.get("hook_tag", "absurd_paradox").lower().replace(" ", "_")
        if hook_tag not in self.genome["hook_archetypes"]:
            self.genome["hook_archetypes"][hook_tag] = {
                "score": 7.5,
                "avg_3s_retention": hook_3s,
                "sample_count": 0,
                "description": f"Auto-discovered hook archetype: {hook_tag}"
            }

        ha = self.genome["hook_archetypes"][hook_tag]
        ha["sample_count"] += 1
        ha["avg_3s_retention"] = round((1 - alpha) * ha["avg_3s_retention"] + alpha * hook_3s, 2)
        target_score = 9.5 if hook_passed else 4.0
        ha["score"] = round((1 - alpha) * ha["score"] + alpha * target_score, 2)

        # 2. Update Visual Blueprints
        signals = autopsy_report.get("evolutionary_signals", {})
        winning_genes = signals.get("winning_genes", [])
        losing_genes = signals.get("losing_genes", [])

        # Process winning blueprints
        for wg in winning_genes:
            if wg.get("type") == "visual_blueprint":
                layout = wg.get("layout", "")
                if layout:
                    if layout not in self.genome["visual_blueprints"]:
                        self.genome["visual_blueprints"][layout] = {
                            "multiplier": 1.0,
                            "avg_retention": 70.0,
                            "win_count": 0,
                            "loss_count": 0,
                            "recommendation": "Auto-discovered layout."
                        }
                    bp = self.genome["visual_blueprints"][layout]
                    bp["win_count"] += 1
                    bp["multiplier"] = min(1.50, round(bp["multiplier"] + 0.05, 2))
                    if "retention_exit" in wg:
                        bp["avg_retention"] = round((1 - alpha) * bp["avg_retention"] + alpha * wg["retention_exit"], 2)

        # Process losing blueprints
        for lg in losing_genes:
            if lg.get("type") == "visual_blueprint":
                layout = lg.get("layout", "")
                if layout:
                    if layout not in self.genome["visual_blueprints"]:
                        self.genome["visual_blueprints"][layout] = {
                            "multiplier": 1.0,
                            "avg_retention": 50.0,
                            "win_count": 0,
                            "loss_count": 0,
                            "recommendation": "Auto-discovered layout."
                        }
                    bp = self.genome["visual_blueprints"][layout]
                    bp["loss_count"] += 1
                    bp["multiplier"] = max(0.40, round(bp["multiplier"] - 0.08, 2))

        # 3. Increment counters & evolve generation
        self.genome["total_autopsies_recorded"] += 1
        if self.genome["total_autopsies_recorded"] % 5 == 0:
            self.genome["generation"] += 1

        self.save()

        return {
            "genome_version": self.genome["version"],
            "generation": self.genome["generation"],
            "total_autopsies": self.genome["total_autopsies_recorded"],
            "updated_hook_archetype": hook_tag,
            "hook_score": ha["score"],
            "hook_avg_3s_retention": ha["avg_3s_retention"]
        }

    def get_blueprint_multiplier(self, layout: str) -> float:
        """Returns the retention multiplier for a given blueprint layout (0.4x to 1.5x)."""
        blueprints = self.genome.get("visual_blueprints", {})
        if layout in blueprints:
            return blueprints[layout].get("multiplier", 1.0)
        # Check partial case-insensitive match (with and without underscores/prefixes)
        layout_norm = re.sub(r"[^a-zA-Z0-9]", "", layout).lower()
        for k, v in blueprints.items():
            k_norm = re.sub(r"[^a-zA-Z0-9]", "", k).lower()
            if k_norm == layout_norm or layout_norm in k_norm or k_norm in layout_norm:
                return v.get("multiplier", 1.0)
        return 1.0

    def get_evolutionary_directives(self) -> Dict[str, Any]:
        """
        Returns actionable generation directives for scriptwriters and visual directors:
        - Top performing hook archetypes
        - High-retention blueprint priorities
        - Penalized blueprints to avoid
        - Pacing parameters
        """
        hooks = self.genome.get("hook_archetypes", {})
        sorted_hooks = sorted(
            [(k, v) for k, v in hooks.items() if v["score"] >= 6.0],
            key=lambda x: x[1]["score"],
            reverse=True
        )
        best_hook = sorted_hooks[0][0] if sorted_hooks else "absurd_paradox"

        bps = self.genome.get("visual_blueprints", {})
        prioritized_bps = [
            k for k, v in sorted(bps.items(), key=lambda x: x[1]["multiplier"], reverse=True)
            if v["multiplier"] >= 1.10
        ]
        penalized_bps = [
            k for k, v in bps.items()
            if v["multiplier"] <= 0.80
        ]

        return {
            "generation": self.genome.get("generation", 1),
            "top_hook_archetype": best_hook,
            "recommended_hook_guideline": hooks.get(best_hook, {}).get("description", "Pattern interrupt."),
            "prioritized_blueprints": prioritized_bps,
            "penalized_blueprints": penalized_bps,
            "recommended_tts_speed": self.genome.get("pacing", {}).get("recommended_tts_speed", 1.12),
            "max_hook_duration_s": self.genome.get("pacing", {}).get("max_hook_duration_s", 3.0),
            "directives_prompt_injection": (
                f"RETENTION GENOME MEMORY DIRECTIVES (Gen {self.genome.get('generation', 1)}):\n"
                f"- Top Performing Hook Style: '{best_hook}' ({hooks.get(best_hook, {}).get('description', '')})\n"
                f"- Prioritize High-Retention Visual Blueprints: {', '.join(prioritized_bps[:4])}\n"
                f"- Strictly Avoid Deprecated / High Drop-off Visuals: {', '.join(penalized_bps) if penalized_bps else 'generic_sine_wave'}\n"
                f"- Maximum Hook Duration: 3.0s (Deliver punchline within 12-18 words)."
            )
        }


# Singleton instance
retention_genome = RetentionGenomeLedger()
