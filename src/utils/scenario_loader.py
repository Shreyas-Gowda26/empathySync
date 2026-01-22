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

    def get_acknowledgments(self) -> Dict:
        """Get acknowledgment templates for emotionally weighted tasks."""
        responses = self.get_all_responses()
        return responses.get("acknowledgments", {})

    def get_acknowledgment_by_category(self, style: str, category: str) -> List[str]:
        """
        Get acknowledgment templates for a specific style and category.

        Args:
            style: 'warm' or 'brief'
            category: e.g., 'endings', 'apologies', 'grief', 'general'

        Returns:
            List of acknowledgment strings
        """
        acknowledgments = self.get_acknowledgments()
        style_data = acknowledgments.get(style, {})
        return style_data.get(category, style_data.get("general", []))

    def get_acknowledgment_config(self) -> Dict:
        """Get acknowledgment configuration."""
        acknowledgments = self.get_acknowledgments()
        return acknowledgments.get("config", {})

    # ==================== EMOTIONAL WEIGHT ====================

    def get_all_emotional_weights(self) -> Dict[str, Dict]:
        """Load all emotional weight configurations."""
        return self._load_directory("emotional_weight")

    def get_task_weights(self) -> Dict:
        """Get task weight configuration."""
        weights = self.get_all_emotional_weights()
        return weights.get("task_weights", {})

    def get_emotional_weight_triggers(self) -> Dict[str, List[str]]:
        """
        Get emotional weight triggers grouped by weight level.

        Returns:
            Dict with 'high_weight' and 'medium_weight' trigger lists
        """
        task_weights = self.get_task_weights()
        return {
            "high_weight": task_weights.get("high_weight", {}).get("triggers", []),
            "medium_weight": task_weights.get("medium_weight", {}).get("triggers", [])
        }

    def get_emotional_weight_score(self, level: str) -> float:
        """
        Get the weight score for an emotional weight level.

        Args:
            level: 'high_weight', 'medium_weight', or 'low_weight'

        Returns:
            Weight score (0-10)
        """
        task_weights = self.get_task_weights()
        level_config = task_weights.get(level, {})
        return level_config.get("weight_score", 2.0)

    def get_acknowledgment_style_for_weight(self, level: str) -> str:
        """
        Get the acknowledgment style for an emotional weight level.

        Args:
            level: 'high_weight', 'medium_weight', or 'low_weight'

        Returns:
            'warm', 'brief', or 'none'
        """
        task_weights = self.get_task_weights()
        level_config = task_weights.get(level, {})
        return level_config.get("acknowledgment_style", "none")

    def get_acknowledgment_category_mapping(self) -> Dict[str, str]:
        """
        Get the keyword to category mapping for acknowledgments.

        Returns:
            Dict mapping keywords to acknowledgment categories
        """
        ack_config = self.get_acknowledgment_config()
        return ack_config.get("category_matching", {})

    # ==================== INTENTS ====================

    def get_all_intents(self) -> Dict[str, Dict]:
        """Load all intent configurations."""
        return self._load_directory("intents")

    def get_session_intent_config(self) -> Dict:
        """Get session intent check-in configuration."""
        intents = self.get_all_intents()
        return intents.get("session_intents", {})

    def get_intent_check_in_config(self) -> Dict:
        """Get the check-in configuration for session start."""
        config = self.get_session_intent_config()
        return config.get("check_in", {})

    def get_intent_indicators(self) -> Dict[str, Dict[str, List[str]]]:
        """Get intent indicators for auto-detection."""
        config = self.get_session_intent_config()
        return config.get("intent_indicators", {})

    def get_intent_shift_config(self) -> Dict:
        """Get configuration for intent shift detection."""
        config = self.get_session_intent_config()
        return config.get("shift_detection", {})

    def get_connection_responses(self, response_type: str = "explicit") -> List[str]:
        """
        Get connection-seeking response templates.

        Args:
            response_type: 'explicit', 'implicit', or 'ai_relationship'

        Returns:
            List of response strings
        """
        config = self.get_session_intent_config()
        responses = config.get("connection_responses", {})
        return responses.get(response_type, [])

    # ==================== GRADUATION ====================

    def get_all_graduation_config(self) -> Dict[str, Dict]:
        """Load all graduation configurations."""
        return self._load_directory("graduation")

    def get_practical_skills_config(self) -> Dict:
        """Get practical skills graduation configuration."""
        graduation = self.get_all_graduation_config()
        return graduation.get("practical_skills", {})

    def get_graduation_settings(self) -> Dict:
        """Get global graduation settings."""
        config = self.get_practical_skills_config()
        return config.get("settings", {})

    def get_graduation_categories(self) -> Dict[str, Dict]:
        """
        Get all task categories for graduation tracking.

        Returns:
            Dict mapping category name to category config
        """
        config = self.get_practical_skills_config()
        return config.get("categories", {})

    def get_graduation_category(self, category_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific task category.

        Args:
            category_name: e.g., 'email_drafting', 'code_help'

        Returns:
            Dict with threshold, prompts, skill_tips, celebration
        """
        categories = self.get_graduation_categories()
        return categories.get(category_name)

    def get_graduation_prompts(self, category_name: str) -> List[str]:
        """Get graduation prompts for a category."""
        category = self.get_graduation_category(category_name)
        if category:
            return category.get("graduation_prompts", [])
        return []

    def get_skill_tips(self, category_name: str) -> List[Dict]:
        """Get skill tips for a category."""
        category = self.get_graduation_category(category_name)
        if category:
            return category.get("skill_tips", [])
        return []

    def get_graduation_celebration(self, category_name: str) -> List[str]:
        """Get celebration messages for completing tasks independently."""
        category = self.get_graduation_category(category_name)
        if category:
            return category.get("celebration", [])
        return []

    def get_independence_config(self) -> Dict:
        """Get independence tracking configuration."""
        config = self.get_practical_skills_config()
        return config.get("independence", {})

    def get_independence_celebrations(self) -> List[str]:
        """Get general independence celebration messages."""
        independence = self.get_independence_config()
        return independence.get("celebration_messages", [])

    def get_independence_button_labels(self) -> List[str]:
        """Get button label options for 'I did it myself'."""
        independence = self.get_independence_config()
        return independence.get("button_labels", ["I did it myself!"])

    # ==================== HANDOFF ====================

    def get_all_handoff_config(self) -> Dict[str, Dict]:
        """Load all handoff configurations."""
        return self._load_directory("handoff")

    def get_contextual_templates_config(self) -> Dict:
        """Get contextual handoff templates configuration."""
        handoff = self.get_all_handoff_config()
        return handoff.get("contextual_templates", {})

    def get_handoff_settings(self) -> Dict:
        """Get handoff behavior settings."""
        config = self.get_contextual_templates_config()
        return config.get("settings", {})

    def get_handoff_context_rules(self) -> Dict[str, Dict]:
        """
        Get context detection rules for handoff templates.

        Returns:
            Dict mapping context name to rule config
        """
        config = self.get_contextual_templates_config()
        return config.get("context_rules", {})

    def get_handoff_templates(self) -> Dict[str, Dict]:
        """
        Get all handoff template categories.

        Returns:
            Dict mapping category name to template config
        """
        config = self.get_contextual_templates_config()
        return config.get("templates", {})

    def get_handoff_template_category(self, category: str) -> Optional[Dict]:
        """
        Get a specific handoff template category.

        Args:
            category: e.g., 'after_difficult_task', 'processing_decision'

        Returns:
            Dict with name, description, intro_prompts, messages
        """
        templates = self.get_handoff_templates()
        return templates.get(category)

    def get_handoff_intro_prompts(self, category: str) -> List[str]:
        """Get intro prompts for a handoff category."""
        template = self.get_handoff_template_category(category)
        if template:
            return template.get("intro_prompts", [])
        return []

    def get_handoff_messages(self, category: str, domain: str = None) -> List[str]:
        """
        Get handoff message templates for a category.

        Args:
            category: Template category (e.g., 'after_difficult_task')
            domain: Optional domain for domain-specific messages

        Returns:
            List of message templates
        """
        template = self.get_handoff_template_category(category)
        if not template:
            return []

        messages = template.get("messages", [])

        # Check for domain-specific messages first
        if domain and "by_domain" in template.get("messages", {}):
            by_domain = template["messages"].get("by_domain", {})
            domain_messages = by_domain.get(domain, by_domain.get("general", []))
            if domain_messages:
                return domain_messages

        # Return general messages
        result = []
        for msg_group in messages:
            if isinstance(msg_group, dict) and "templates" in msg_group:
                result.extend(msg_group.get("templates", []))
            elif isinstance(msg_group, str):
                result.append(msg_group)

        return result

    def get_handoff_follow_up_prompts(self, category: str) -> List[str]:
        """Get follow-up prompts for a handoff category."""
        template = self.get_handoff_template_category(category)
        if template:
            return template.get("follow_up_prompts", [])
        return []

    def get_handoff_follow_up_options(self) -> Dict:
        """Get self-report options for handoff follow-up."""
        config = self.get_contextual_templates_config()
        return config.get("follow_up_options", {})

    def get_handoff_celebrations(self, outcome: str = "reached_out") -> List[str]:
        """
        Get celebration messages for handoff outcomes.

        Args:
            outcome: 'reached_out', 'very_helpful', 'not_yet', etc.

        Returns:
            List of celebration messages
        """
        follow_up = self.get_handoff_follow_up_options()
        celebrations = follow_up.get("celebrations", {})
        return celebrations.get(outcome, [])

    def detect_handoff_context(
        self,
        emotional_weight: str = None,
        session_intent: str = None,
        domain: str = None,
        dependency_score: float = 0,
        is_late_night: bool = False,
        sessions_today: int = 0
    ) -> str:
        """
        Detect the appropriate handoff context based on session state.

        Args:
            emotional_weight: 'high_weight', 'medium_weight', or 'low_weight'
            session_intent: 'practical', 'processing', 'emotional', 'connection'
            domain: Current conversation domain
            dependency_score: User's dependency score (0-10)
            is_late_night: Whether it's a late night session
            sessions_today: Number of sessions today

        Returns:
            Context category name (e.g., 'after_difficult_task')
        """
        rules = self.get_handoff_context_rules()

        # Check rules in priority order
        sorted_rules = sorted(
            rules.items(),
            key=lambda x: x[1].get("priority", 10)
        )

        for context_name, rule in sorted_rules:
            triggers = rule.get("triggers", [])

            # Check if any triggers match
            for trigger in triggers:
                if trigger == "high_emotional_weight_task" and emotional_weight == "high_weight":
                    return context_name
                if trigger == "session_intent_processing" and session_intent == "processing":
                    return context_name
                if trigger.startswith("domain_") and domain == trigger.replace("domain_", ""):
                    return context_name
                if trigger == "high_dependency_score" and dependency_score >= 7:
                    return context_name
                if trigger == "late_night_session" and is_late_night:
                    return context_name
                if trigger == "multiple_sessions_today" and sessions_today >= 3:
                    return context_name

        return "general"

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

        IMPORTANT: Domains are processed in order of risk_weight (highest first).
        This ensures "friend is addicted" matches health (7.0) before relationships (5.0).
        """
        triggers = self.get_domain_triggers()
        weights = self.get_domain_weights()

        # Sort domains by risk_weight (highest first) so high-risk triggers take priority
        sorted_domains = sorted(triggers.keys(), key=lambda d: weights.get(d, 1.0), reverse=True)

        flat = {}
        for domain in sorted_domains:
            words = triggers.get(domain, [])
            for word in words:
                # Only add if not already present (higher-priority domain wins)
                word_lower = word.lower()
                if word_lower not in flat:
                    flat[word_lower] = domain
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
