"""
EmotionalWeightAssessor — Emotional intensity and weight classification.

Extracted from RiskClassifier (Phase 16.8.5) to isolate the concern of
assessing *how emotionally heavy a task is*, separate from domain detection,
dependency scoring, and intent detection.

Key distinction:
  - Emotional INTENSITY = how the USER feels (markers: "desperate", "scared")
  - Emotional WEIGHT = how heavy the TASK is (triggers: "breakup message", "resignation")
  A calm user can ask for a high-weight task, and a stressed user can ask
  for a low-weight task.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EmotionalWeightAssessor:
    """Assesses emotional intensity and task weight from user text.

    Args:
        loader: ScenarioLoader instance for fetching triggers, markers, and scores.
    """

    def __init__(self, loader):
        self.loader = loader
        self._weight_trigger_cache: Optional[Dict[str, str]] = None

    def measure_intensity(self, text: str) -> float:
        """Measure emotional intensity (0-10) based on scenario markers.

        Checks high → medium → low intensity markers in order, returning
        the score for the first matched level.
        """
        t = text.lower()
        markers_by_level = self.loader.get_emotional_markers_by_level()

        for level in ["high_intensity", "medium_intensity", "low_intensity"]:
            if level in markers_by_level:
                markers = markers_by_level[level]
                if any(marker.lower() in t for marker in markers):
                    return self.loader.get_emotional_score(level)

        return self.loader.get_emotional_score("neutral")

    def get_weight_triggers(self) -> Dict[str, str]:
        """Get cached trigger→weight_level mapping, ordered by priority.

        Triggers are loaded in priority order (reflection_redirect > high > medium)
        and sorted by length descending so more specific triggers match first.
        """
        if self._weight_trigger_cache is None:
            weight_triggers = self.loader.get_emotional_weight_triggers()
            self._weight_trigger_cache = {}

            for level in ["reflection_redirect", "high_weight", "medium_weight"]:
                triggers = weight_triggers.get(level, [])
                for trigger in sorted(triggers, key=len, reverse=True):
                    trigger_lower = trigger.lower()
                    if trigger_lower not in self._weight_trigger_cache:
                        self._weight_trigger_cache[trigger_lower] = level
        return self._weight_trigger_cache

    def assess_weight(self, text: str) -> Tuple[str, float]:
        """Assess the emotional weight of a TASK (not the user's state).

        Returns:
            (weight_level, weight_score) where weight_level is one of:
            'reflection_redirect', 'high_weight', 'medium_weight', 'low_weight'
        """
        t = text.lower()
        weight_triggers = self.get_weight_triggers()

        for trigger in sorted(weight_triggers.keys(), key=len, reverse=True):
            if trigger in t:
                level = weight_triggers[trigger]
                score = self.loader.get_emotional_weight_score(level)
                return (level, score)

        return ("low_weight", self.loader.get_emotional_weight_score("low_weight"))

    def needs_reflection_redirect(self, text: str) -> bool:
        """Check if input requires reflection instead of task completion.

        These are personal messages that should come from the person, not AI:
        breakup messages, personal apologies, coming out messages, etc.
        """
        weight_level, _ = self.assess_weight(text)
        return weight_level == "reflection_redirect"

    def get_reflection_response(self) -> str:
        """Get a reflection redirect response from scenarios."""
        return self.loader.get_reflection_redirect_response()

    def get_response_modifier(self, intensity: float) -> str:
        """Get response tone modifier based on emotional intensity level."""
        if intensity >= 9.0:
            return self.loader.get_emotional_response_modifier("high_intensity")
        elif intensity >= 6.0:
            return self.loader.get_emotional_response_modifier("medium_intensity")
        elif intensity >= 4.0:
            return self.loader.get_emotional_response_modifier("low_intensity")
        return self.loader.get_emotional_response_modifier("neutral")

    def invalidate_cache(self) -> None:
        """Clear cached triggers (call after scenario reload)."""
        self._weight_trigger_cache = None
