"""
Wellness-focused prompts for empathetic AI conversations
Designed to promote healthy AI relationships and digital wellness

Now powered by the scenarios knowledge base for dynamic, extensible configuration.
These prompts enforce structured, behavioral output rather than vague personas.
"""

from typing import Dict, List, Optional
import random

from utils.scenario_loader import get_scenario_loader, ScenarioLoader


class WellnessPrompts:
    """
    Collection of structured prompts that enforce specific behaviors.

    Loads prompts, styles, and response rules from the scenarios knowledge base.
    """

    def __init__(self, scenario_loader: Optional[ScenarioLoader] = None):
        """
        Initialize WellnessPrompts.

        Args:
            scenario_loader: Optional ScenarioLoader instance.
                           If not provided, uses the singleton.
        """
        self.loader = scenario_loader or get_scenario_loader()

    def get_system_prompt(self, wellness_mode: str, risk_context: Dict = None) -> str:
        """
        Build a complete system prompt with:
        1. Base behavioral rules (always applied)
        2. Style modifier (Gentle/Direct/Balanced)
        3. Risk-aware instructions (if risk_context provided)
        """
        prompt_parts = [self._get_base_rules()]

        # Add style modifier
        modifier = self._get_style_modifier(wellness_mode)
        if modifier:
            prompt_parts.append(modifier)

        # Add risk-aware instructions if context provided
        if risk_context:
            risk_instructions = self._get_risk_instructions(risk_context)
            prompt_parts.append(risk_instructions)

        return "\n\n".join(prompt_parts)

    def _get_base_rules(self) -> str:
        """Core behavioral rules - always enforced."""
        base_config = self.loader.get_base_prompt_config()

        identity = base_config.get("identity", {})
        identity_rules = identity.get("rules", [])
        identity_rules_text = "\n".join(f"- {rule}" for rule in identity_rules)

        output_format = base_config.get("output_format", {})
        output_rules = output_format.get("rules", [])
        output_rules_text = "\n".join(f"{rule}" for rule in output_rules)

        behavioral_rules = base_config.get("behavioral_rules", [])
        behavioral_rules_text = "\n".join(f"- {rule}" for rule in behavioral_rules)

        forbidden = base_config.get("forbidden_topics", {})
        forbidden_topics = forbidden.get("topics", [])
        forbidden_text = ", ".join(forbidden_topics)
        forbidden_redirect = forbidden.get("redirect", "")

        core_purpose = base_config.get("core_purpose", "").strip()

        return f"""You are EmpathySync, a clarity tool that helps humans think—not a therapist, advisor, or friend.

## IDENTITY RULES (never violate)
{identity_rules_text}

## OUTPUT FORMAT
{output_rules_text}

## BEHAVIORAL RULES
{behavioral_rules_text}

## FORBIDDEN TOPICS (redirect immediately)
If the user asks for advice on: {forbidden_text}—respond ONLY with:
"{forbidden_redirect}"

## REMINDER
{core_purpose}"""

    def _get_style_modifier(self, wellness_mode: str) -> str:
        """Get the style modifier for the given wellness mode."""
        return self.loader.get_style_modifier(wellness_mode)

    def _get_risk_instructions(self, risk_context: Dict) -> str:
        """Generate risk-aware instructions based on classifier output."""
        domain = risk_context.get("domain", "logistics")
        risk_weight = risk_context.get("risk_weight", 0)
        emotional_intensity = risk_context.get("emotional_intensity", 0)
        dependency_risk = risk_context.get("dependency_risk", 0)

        instructions = ["## RISK-AWARE INSTRUCTIONS FOR THIS MESSAGE"]

        # Domain-specific rules from scenarios
        domain_config = self.loader.get_domain(domain)
        if domain_config:
            response_rules = domain_config.get("response_rules", [])
            if response_rules:
                instructions.append(f"Topic: {domain_config.get('description', domain)}")
                instructions.extend(response_rules)

            # Check for crisis or harmful domain special responses
            if domain == "crisis":
                crisis_response = domain_config.get("crisis_response", "")
                if crisis_response:
                    instructions.append(f"RESPOND ONLY WITH:\n{crisis_response.strip()}")
            elif domain == "harmful":
                refusal = domain_config.get("refusal_response", "")
                if refusal:
                    instructions.append(f"RESPOND ONLY WITH: {refusal}")

        # Risk weight modifiers
        if risk_weight >= 8:
            instructions.append("HIGH RISK: Keep response under 30 words. Redirect to human support immediately.")
        elif risk_weight >= 5:
            instructions.append("MODERATE RISK: Keep response under 50 words. Include redirect suggestion.")

        # Emotional intensity modifiers
        if emotional_intensity >= 7:
            instructions.append("High emotional intensity detected. Do not mirror the intensity. Stay calm and brief.")

        # Dependency modifiers
        if dependency_risk >= 5:
            instructions.append("Dependency pattern detected. Shorten response. Do not encourage continued conversation.")

        # Include intervention message if present
        intervention = risk_context.get("intervention")
        if intervention:
            intervention_data = intervention.get("intervention", {})
            if intervention_data:
                instruction = intervention_data.get("instruction", "")
                if instruction:
                    instructions.append(f"DEPENDENCY INTERVENTION: {instruction}")

        return "\n".join(instructions)

    def get_check_in_prompts(self) -> List[str]:
        """Get various check-in prompts for user reflection."""
        check_ins = self.loader.get_check_in_prompts()
        # Flatten all categories into a single list
        all_prompts = []
        for prompts in check_ins.values():
            if isinstance(prompts, list):
                all_prompts.extend(prompts)
        return all_prompts

    def get_mindfulness_prompts(self) -> List[str]:
        """Get mindfulness-focused prompts for digital wellness."""
        mindfulness = self.loader.get_mindfulness_prompts()
        # Flatten all categories into a single list
        all_prompts = []
        for prompts in mindfulness.values():
            if isinstance(prompts, list):
                all_prompts.extend(prompts)
        return all_prompts

    def get_random_check_in(self, category: str = None) -> str:
        """Get a random check-in prompt, optionally from a specific category."""
        check_ins = self.loader.get_check_in_prompts()
        if category and category in check_ins:
            prompts = check_ins[category]
        else:
            prompts = self.get_check_in_prompts()
        return random.choice(prompts) if prompts else ""

    def get_random_mindfulness(self, category: str = None) -> str:
        """Get a random mindfulness prompt, optionally from a specific category."""
        mindfulness = self.loader.get_mindfulness_prompts()
        if category and category in mindfulness:
            prompts = mindfulness[category]
        else:
            prompts = self.get_mindfulness_prompts()
        return random.choice(prompts) if prompts else ""

    def get_fallback_response(self, category: str = "general") -> str:
        """Get a random fallback response."""
        responses = self.loader.get_fallback_responses(category)
        return random.choice(responses) if responses else ""

    def get_safe_alternative_response(self) -> str:
        """Get a random safe alternative response."""
        responses = self.loader.get_safe_alternative_responses()
        return random.choice(responses) if responses else ""

    def get_dependency_intervention_response(self, dependency_score: float) -> Optional[str]:
        """Get an intervention response based on dependency score."""
        intervention = self.loader.get_dependency_intervention(dependency_score)
        if intervention:
            intervention_data = intervention.get("intervention", {})
            if intervention_data:
                responses = intervention_data.get("responses", [])
                if responses:
                    return random.choice(responses)
        return None

    def get_graduation_prompt(self, skill: str = None) -> Optional[str]:
        """Get a graduation/skill-building prompt."""
        skills = self.loader.get_graduation_skills()
        if not skills:
            return None

        if skill:
            for s in skills:
                if s.get("name") == skill:
                    prompts = s.get("prompts", [])
                    if prompts:
                        return random.choice(prompts)
        else:
            # Get a random prompt from any skill
            all_prompts = []
            for s in skills:
                all_prompts.extend(s.get("prompts", []))
            if all_prompts:
                return random.choice(all_prompts)
        return None

    def reload_scenarios(self) -> None:
        """Reload scenarios from disk (useful for hot-reloading)."""
        self.loader.reload()
