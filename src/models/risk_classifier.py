"""
RiskClassifier - estimates domain and influence / dependency risk
Used by WellnessGuide to become influence-aware without taking over decisions.

Now powered by the scenarios knowledge base for dynamic, extensible configuration.
"""

from typing import List, Dict, Optional

from utils.scenario_loader import get_scenario_loader, ScenarioLoader


class RiskClassifier:
    """
    Detect rough domain, emotional intensity, and dependency risk
    based on the current user input and recent conversation history.

    Uses the scenarios knowledge base for triggers, weights, and thresholds.
    """

    def __init__(self, scenario_loader: Optional[ScenarioLoader] = None):
        """
        Initialize the RiskClassifier.

        Args:
            scenario_loader: Optional ScenarioLoader instance.
                           If not provided, uses the singleton.
        """
        self.loader = scenario_loader or get_scenario_loader()
        self._trigger_cache: Optional[Dict[str, str]] = None

    def _get_triggers(self) -> Dict[str, str]:
        """Get cached trigger -> domain mapping."""
        if self._trigger_cache is None:
            self._trigger_cache = self.loader.get_all_triggers_flat()
        return self._trigger_cache

    def classify(
        self,
        user_input: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Return a simple risk assessment dictionary.

        Example:
        {
            "domain": "spirituality",
            "emotional_intensity": 7.0,
            "dependency_risk": 3.0,
            "risk_weight": 8.1,
            "intervention": {...}  # if dependency threshold met
        }
        """
        domain = self._detect_domain(user_input)
        emotional_intensity = self._measure_emotional_intensity(user_input)
        dependency_risk = self._assess_dependency(conversation_history)

        risk_weight = self._combine_scores(domain, emotional_intensity, dependency_risk)

        result = {
            "domain": domain,
            "emotional_intensity": emotional_intensity,
            "dependency_risk": dependency_risk,
            "risk_weight": risk_weight
        }

        # Check for dependency intervention
        intervention = self.loader.get_dependency_intervention(dependency_risk)
        if intervention and intervention.get("intervention"):
            result["intervention"] = intervention

        return result

    def _detect_domain(self, text: str) -> str:
        """
        Keyword-based domain detection using scenarios knowledge base.
        """
        t = text.lower()
        triggers = self._get_triggers()

        # Check each trigger word
        for trigger, domain in triggers.items():
            if trigger in t:
                return domain

        return "logistics"

    def _measure_emotional_intensity(self, text: str) -> float:
        """
        Emotional intensity scale 0–10 based on markers from scenarios.
        """
        t = text.lower()
        markers_by_level = self.loader.get_emotional_markers_by_level()

        # Check in order of intensity (high first)
        for level in ["high_intensity", "medium_intensity", "low_intensity"]:
            if level in markers_by_level:
                markers = markers_by_level[level]
                if any(marker in t for marker in markers):
                    return self.loader.get_emotional_score(level)

        # Default neutral score
        return self.loader.get_emotional_score("neutral")

    def _assess_dependency(self, history: List[Dict]) -> float:
        """
        Dependency heuristic based on conversation patterns.

        Uses configuration from scenarios/interventions/dependency.yaml
        """
        if not history:
            return 0.0

        # Get configuration from scenarios
        config = self.loader.get_dependency_config()
        calculation = config.get("calculation", {})

        base_factor = calculation.get("base_factor", 0.7)
        base_cap = calculation.get("base_cap", 6.0)
        repetition_boost_max = calculation.get("repetition_boost", 4.0)
        lookback = calculation.get("lookback_messages", 12)

        recent = history[-lookback:]
        user_messages = [m["content"] for m in recent if m.get("role") == "user"]

        if not user_messages:
            return 0.0

        n = len(user_messages)

        # Base on frequency: many recent user turns → higher score
        base = min(n * base_factor, base_cap)

        # Check repetition of similar openings
        repetition_config = config.get("repetition", {})
        prefix_length = repetition_config.get("prefix_length", 60)

        prefixes = [m[:prefix_length].lower() for m in user_messages]
        unique_prefixes = len(set(prefixes))
        repetition_ratio = 1.0 - (unique_prefixes / max(len(prefixes), 1))

        repetition_boost = repetition_ratio * repetition_boost_max

        score = base + repetition_boost
        return min(score, 10.0)

    def _combine_scores(self, domain: str, intensity: float, dependency: float) -> float:
        """
        Combine domain, intensity, and dependency to a single 0–10 risk score.
        """
        domain_weights = self.loader.get_domain_weights()
        base = domain_weights.get(domain, 2.0)

        score = base
        score += 0.3 * intensity
        score += 0.2 * dependency

        return float(min(score, 10.0))

    def get_domain_response_rules(self, domain: str) -> List[str]:
        """Get response rules for the detected domain."""
        return self.loader.get_domain_response_rules(domain)

    def get_domain_redirects(self, domain: str) -> Dict[str, Dict]:
        """Get redirect scenarios for the detected domain."""
        return self.loader.get_domain_redirects(domain)

    def get_emotional_response_modifier(self, intensity: float) -> str:
        """Get response modifier based on emotional intensity."""
        if intensity >= 9.0:
            return self.loader.get_emotional_response_modifier("high_intensity")
        elif intensity >= 6.0:
            return self.loader.get_emotional_response_modifier("medium_intensity")
        elif intensity >= 4.0:
            return self.loader.get_emotional_response_modifier("low_intensity")
        return self.loader.get_emotional_response_modifier("neutral")

    def reload_scenarios(self) -> None:
        """Reload scenarios from disk (useful for hot-reloading)."""
        self.loader.reload()
        self._trigger_cache = None
