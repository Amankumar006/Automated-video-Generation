"""AetherBench Scenario Registry.

Manages registration, discovery, filtering, validation, serialization,
and querying of cinematic benchmark test scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set, Union

from aether.bench.schemas import (
    AetherScenario,
    ComplexityLevel,
    PhysicsDifficulty,
    StressTestCategory,
)


class ScenarioRegistry:
    """In-memory and persistent catalog of AetherBench benchmark scenarios."""

    def __init__(self) -> None:
        self._scenarios: Dict[str, AetherScenario] = {}
        self._lock = threading.RLock()

    def register(self, scenario: AetherScenario, allow_overwrite: bool = False) -> None:
        """Register a scenario into the catalog.

        Args:
            scenario: The validated AetherScenario to store.
            allow_overwrite: If True, replaces existing scenario with the same ID.

        Raises:
            ValueError: If scenario ID already exists and allow_overwrite is False.
        """
        with self._lock:
            if not allow_overwrite and scenario.id in self._scenarios:
                raise ValueError(f"Scenario with ID '{scenario.id}' already registered in registry.")
            self._scenarios[scenario.id] = scenario

    def register_many(self, scenarios: List[AetherScenario], allow_overwrite: bool = False) -> int:
        """Register multiple scenarios. Returns count of registered scenarios."""
        count = 0
        for s in scenarios:
            self.register(s, allow_overwrite=allow_overwrite)
            count += 1
        return count

    def unregister(self, scenario_id: str) -> bool:
        """Remove a scenario by ID. Returns True if removed, False if not found."""
        with self._lock:
            if scenario_id in self._scenarios:
                del self._scenarios[scenario_id]
                return True
            return False

    def get(self, scenario_id: str) -> Optional[AetherScenario]:
        """Retrieve a scenario by ID, or None if not found."""
        with self._lock:
            return self._scenarios.get(scenario_id)

    def get_or_raise(self, scenario_id: str) -> AetherScenario:
        """Retrieve a scenario by ID or raise KeyError."""
        with self._lock:
            if scenario_id not in self._scenarios:
                raise KeyError(f"Scenario '{scenario_id}' not found in registry.")
            return self._scenarios[scenario_id]

    def list_all(self) -> List[AetherScenario]:
        """Return list of all registered scenarios."""
        with self._lock:
            return list(self._scenarios.values())

    def list_ids(self) -> List[str]:
        """Return list of all registered scenario IDs."""
        with self._lock:
            return list(self._scenarios.keys())

    def count(self) -> int:
        """Return total number of registered scenarios."""
        with self._lock:
            return len(self._scenarios)

    def clear(self) -> None:
        """Clear all registered scenarios."""
        with self._lock:
            self._scenarios.clear()

    def filter(
        self,
        category: Optional[Union[StressTestCategory, str]] = None,
        complexity_level: Optional[Union[ComplexityLevel, int]] = None,
        physics_difficulty: Optional[Union[PhysicsDifficulty, str]] = None,
        min_characters: Optional[int] = None,
        max_characters: Optional[int] = None,
        tags: Optional[List[str]] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
    ) -> List[AetherScenario]:
        """Filter scenarios matching all specified criteria."""
        results: List[AetherScenario] = []

        target_cat = StressTestCategory(category) if isinstance(category, str) else category
        target_diff = PhysicsDifficulty(physics_difficulty) if isinstance(physics_difficulty, str) else physics_difficulty
        target_tags = set(tags) if tags else set()

        with self._lock:
            scenarios_copy = list(self._scenarios.values())

        for s in scenarios_copy:
            if target_cat is not None and s.category != target_cat:
                continue
            if complexity_level is not None and int(s.complexity_level) != int(complexity_level):
                continue
            if target_diff is not None and s.physics_profile.difficulty != target_diff:
                continue
            char_count = len(s.characters)
            if min_characters is not None and char_count < min_characters:
                continue
            if max_characters is not None and char_count > max_characters:
                continue
            if target_tags and not target_tags.issubset(set(s.tags)):
                continue
            if min_duration is not None and s.duration_seconds < min_duration:
                continue
            if max_duration is not None and s.duration_seconds > max_duration:
                continue

            results.append(s)

        return results

    def summary(self) -> Dict[str, Any]:
        """Compute aggregate statistics of the registered scenarios."""
        categories: Dict[str, int] = {}
        complexity_levels: Dict[int, int] = {}
        physics_difficulties: Dict[str, int] = {}
        total_duration = 0.0
        total_characters = 0

        with self._lock:
            scenarios_copy = list(self._scenarios.values())

        for s in scenarios_copy:
            cat = s.category.value
            categories[cat] = categories.get(cat, 0) + 1

            comp = int(s.complexity_level)
            complexity_levels[comp] = complexity_levels.get(comp, 0) + 1

            diff = s.physics_profile.difficulty.value
            physics_difficulties[diff] = physics_difficulties.get(diff, 0) + 1

            total_duration += s.duration_seconds
            total_characters += len(s.characters)

        total_count = len(scenarios_copy)
        avg_dur = round(total_duration / total_count, 2) if total_count > 0 else 0.0

        return {
            "total_scenarios": total_count,
            "categories": categories,
            "complexity_levels": complexity_levels,
            "physics_difficulties": physics_difficulties,
            "total_duration_seconds": round(total_duration, 2),
            "average_duration_seconds": avg_dur,
            "total_characters": total_characters,
        }

    def export_to_json(self, file_path: Union[str, Path]) -> int:
        """Export all scenarios to a single JSON file. Returns count exported."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = [json.loads(s.model_dump_json()) for s in self._scenarios.values()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return len(data)

    def import_from_json(self, file_path: Union[str, Path], allow_overwrite: bool = False) -> int:
        """Import scenarios from a single JSON file. Returns count imported."""
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError(f"Expected a JSON list of scenarios in {file_path}")

        count = 0
        for item in raw_data:
            scenario = AetherScenario.model_validate(item)
            self.register(scenario, allow_overwrite=allow_overwrite)
            count += 1
        return count

    def export_to_dir(self, dir_path: Union[str, Path]) -> int:
        """Export each scenario as a separate JSON file in a directory. Returns count."""
        path = Path(dir_path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        count = 0
        with self._lock:
            scenarios_copy = list(self._scenarios.values())

        for s in scenarios_copy:
            # Sanitize filename to prevent directory traversal
            clean_filename = "".join(c for c in s.id if c.isalnum() or c in ("-", "_")) or "scenario"
            file_path = (path / f"{clean_filename}.json").resolve()
            if not str(file_path).startswith(str(path)):
                raise ValueError(f"Illegal path traversal in scenario ID: '{s.id}'")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(s.model_dump_json(indent=2))
            count += 1
        return count

    def import_from_dir(self, dir_path: Union[str, Path], allow_overwrite: bool = False) -> int:
        """Import all .json scenario files from a directory. Returns count."""
        path = Path(dir_path)
        if not path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        count = 0
        for file_path in sorted(path.glob("*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                item = json.load(f)
            scenario = AetherScenario.model_validate(item)
            self.register(scenario, allow_overwrite=allow_overwrite)
            count += 1
        return count


# Global default registry instance
_DEFAULT_REGISTRY: Optional[ScenarioRegistry] = None


def get_default_registry() -> ScenarioRegistry:
    """Retrieve the global default scenario registry singleton."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ScenarioRegistry()
    return _DEFAULT_REGISTRY


def register_scenario(scenario: AetherScenario, allow_overwrite: bool = False) -> None:
    """Register a scenario in the default registry."""
    get_default_registry().register(scenario, allow_overwrite=allow_overwrite)
