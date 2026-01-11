"""
ScenarioLoader - Loads and manages the scenarios knowledge base

This module provides access to the structured YAML-based scenarios repository,
enabling dynamic loading of domains, emotional markers, interventions, prompts,
and response templates without code changes.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache


class ScenarioLoader:
    """
    Loads and provides access to the scenarios knowledge base.

    The scenarios directory contains structured YAML files for:
    - domains/: Risk domains (money, health, relationships, etc.)
    - emotional_markers/: Intensity levels and their markers
    - interventions/: Dependency, session boundaries, graduation paths
    - prompts/: Check-ins, mindfulness, styles
    - responses/: Fallbacks, safe alternatives, base prompts
    """

    def __init__(self, scenarios_path: Optional[str] = None):
        """
        Initialize the ScenarioLoader.

        Args:
            scenarios_path: Path to the scenarios directory.
                          Defaults to project_root/scenarios/
        """
        if scenarios_path:
            self.scenarios_path = Path(scenarios_path)
        else:
            # Default to project_root/scenarios/
            project_root = Path(__file__).parent.parent.parent
            self.scenarios_path = project_root / "scenarios"

        self._cache: Dict[str, Any] = {}
        self._validate_scenarios_path()

    def _validate_scenarios_path(self) -> None:
        """Verify the scenarios directory exists."""
        if not self.scenarios_path.exists():
            raise FileNotFoundError(
                f"Scenarios directory not found: {self.scenarios_path}"
            )

    def _load_yaml(self, file_path: Path) -> Dict:
        """Load a single YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_directory(self, subdir: str) -> Dict[str, Dict]:
        """Load all YAML files from a subdirectory."""
        cache_key = f"dir_{subdir}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        dir_path = self.scenarios_path / subdir
        if not dir_path.exists():
            return {}

        result = {}
        for yaml_file in dir_path.glob("*.yaml"):
            name = yaml_file.stem
            result[name] = self._load_yaml(yaml_file)

        self._cache[cache_key] = result
        return result

    # ==================== DOMAINS ====================

    def get_all_domains(self) -> Dict[str, Dict]:
        """Load all domain configurations."""
        return self._load_directory("domains")

    def get_domain(self, domain_name: str) -> Optional[Dict]:
        """Get a specific domain configuration."""
        domains = self.get_all_domains()
        return domains.get(domain_name)

    def get_domain_triggers(self) -> Dict[str, List[str]]:
        """Get all domain triggers as a mapping of domain -> trigger words."""
        domains = self.get_all_domains()
        return {
            name: config.get("triggers", [])
            for name, config in domains.items()
        }

    def get_domain_weights(self) -> Dict[str, float]:
        """Get risk weights for all domains."""
        domains = self.get_all_domains()
        return {
            name: config.get("risk_weight", 1.0)
            for name, config in domains.items()
        }

    def get_domain_response_rules(self, domain_name: str) -> List[str]:
        """Get response rules for a specific domain."""
        domain = self.get_domain(domain_name)
        if domain:
            return domain.get("response_rules", [])
        return []

    def get_domain_redirects(self, domain_name: str) -> Dict[str, Dict]:
        """Get redirect scenarios for a specific domain."""
        domain = self.get_domain(domain_name)
        if domain:
            return domain.get("redirects", {})
        return {}

    # ==================== EMOTIONAL MARKERS ====================

    def get_all_emotional_markers(self) -> Dict[str, Dict]:
        """Load all emotional marker configurations."""
        return self._load_directory("emotional_markers")

    def get_emotional_markers_by_level(self) -> Dict[str, List[str]]:
        """Get markers grouped by intensity level."""
        markers = self.get_all_emotional_markers()
        return {
            name: config.get("markers", [])
            for name, config in markers.items()
        }

    def get_emotional_score(self, level: str) -> float:
        """Get the score for an emotional intensity level."""
        markers = self.get_all_emotional_markers()
        if level in markers:
            return markers[level].get("score", 3.0)
        return 3.0

    def get_emotional_response_modifier(self, level: str) -> str:
        """Get the response modifier for an emotional intensity level."""
        markers = self.get_all_emotional_markers()
        if level in markers:
            return markers[level].get("response_modifier", "")
        return ""

    # ==================== INTERVENTIONS ====================

    def get_all_interventions(self) -> Dict[str, Dict]:
        """Load all intervention configurations."""
        return self._load_directory("interventions")

    def get_dependency_config(self) -> Dict:
        """Get dependency intervention configuration."""
        interventions = self.get_all_interventions()
        return interventions.get("dependency", {})

    def get_dependency_levels(self) -> List[Dict]:
        """Get dependency intervention levels."""
        config = self.get_dependency_config()
        return config.get("levels", [])

    def get_dependency_intervention(self, score: float) -> Optional[Dict]:
        """Get the appropriate intervention for a dependency score."""
        levels = self.get_dependency_levels()
        intervention = None
        for level in levels:
            if score >= level.get("threshold", 0):
                intervention = level
        return intervention

    def get_session_boundaries(self) -> Dict:
        """Get session boundary configuration."""
        interventions = self.get_all_interventions()
        return interventions.get("session_boundaries", {})

    def get_graduation_skills(self) -> List[Dict]:
        """Get graduation skill-building configurations."""
        interventions = self.get_all_interventions()
        graduation = interventions.get("graduation", {})
        return graduation.get("skills", [])

    # ==================== PROMPTS ====================

    def get_all_prompts(self) -> Dict[str, Dict]:
        """Load all prompt configurations."""
        return self._load_directory("prompts")

    def get_check_in_prompts(self) -> Dict[str, List[str]]:
        """Get check-in prompts by category."""
        prompts = self.get_all_prompts()
        check_ins = prompts.get("check_ins", {})
        # Return all categories except metadata
        return {
            k: v for k, v in check_ins.items()
            if isinstance(v, list)
        }

    def get_mindfulness_prompts(self) -> Dict[str, List[str]]:
        """Get mindfulness prompts by category."""
        prompts = self.get_all_prompts()
        mindfulness = prompts.get("mindfulness", {})
        return {
            k: v for k, v in mindfulness.items()
            if isinstance(v, list)
        }

    def get_human_connection_prompts(self) -> Dict:
        """Get human connection prompts and templates."""
        prompts = self.get_all_prompts()
        return prompts.get("human_connection", {})

    def get_style_config(self, style_name: str) -> Optional[Dict]:
        """Get configuration for a specific communication style."""
        prompts = self.get_all_prompts()
        styles = prompts.get("styles", {})
        return styles.get(style_name.lower())

    def get_style_modifier(self, style_name: str) -> str:
        """Get the prompt modifier for a style."""
        config = self.get_style_config(style_name)
        if config:
            return config.get("modifier", "")
        return ""

    # ==================== RESPONSES ====================

    def get_all_responses(self) -> Dict[str, Dict]:
        """Load all response configurations."""
        return self._load_directory("responses")

    def get_fallback_responses(self, category: str = "general") -> List[str]:
        """Get fallback responses by category."""
        responses = self.get_all_responses()
        fallbacks = responses.get("fallbacks", {})
        return fallbacks.get(category, fallbacks.get("general", []))

    def get_safe_alternative_responses(self) -> List[str]:
        """Get safe alternative responses for harmful content."""
        responses = self.get_all_responses()
        safe_alts = responses.get("safe_alternatives", {})
        return safe_alts.get("harmful_content_detected", [])

    def get_harmful_patterns(self) -> List[str]:
        """Get patterns that indicate potentially harmful responses."""
        responses = self.get_all_responses()
        safe_alts = responses.get("safe_alternatives", {})
        return safe_alts.get("harmful_patterns", [])

    def get_base_prompt_config(self) -> Dict:
        """Get base prompt configuration."""
        responses = self.get_all_responses()
        return responses.get("base_prompt", {})

    # ==================== UTILITY METHODS ====================

    def clear_cache(self) -> None:
        """Clear the internal cache to force reload from files."""
        self._cache.clear()

    def reload(self) -> None:
        """Reload all scenarios from disk."""
        self.clear_cache()

    def get_all_triggers_flat(self) -> Dict[str, str]:
        """
        Get a flat mapping of trigger word -> domain.
        Useful for quick lookups.
        """
        triggers = self.get_domain_triggers()
        flat = {}
        for domain, words in triggers.items():
            for word in words:
                flat[word.lower()] = domain
        return flat


# Singleton instance for convenience
_loader_instance: Optional[ScenarioLoader] = None


def get_scenario_loader(scenarios_path: Optional[str] = None) -> ScenarioLoader:
    """
    Get the singleton ScenarioLoader instance.

    Args:
        scenarios_path: Optional path to scenarios directory.
                       Only used on first call.

    Returns:
        ScenarioLoader instance
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ScenarioLoader(scenarios_path)
    return _loader_instance


def reset_scenario_loader() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _loader_instance
    _loader_instance = None
