"""
AI Wellness Guide - Core empathetic conversation engine
Leveraging your Ollama infrastructure for local AI processing

Implements the empathySync vision:
- Presence > persuasion
- Restraint is the product's core feature
- Help that knows when to stop
"""

import requests
import logging
from typing import List, Dict, Optional
from config.settings import settings
from prompts.wellness_prompts import WellnessPrompts
from models.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)


# Session limits by risk level (from vision document)
TURN_LIMITS = {
    "logistics": 20,      # Low risk: generous limit
    "money": 8,           # Moderate risk: fewer turns
    "health": 8,          # Moderate risk
    "relationships": 10,  # Moderate risk
    "spirituality": 5,    # High risk: very short
    "crisis": 1,          # Immediate stop
    "harmful": 1,         # Immediate stop
}

# Identity reminder frequency (every N turns)
IDENTITY_REMINDER_FREQUENCY = 6


class WellnessGuide:
    """
    Empathetic AI guide for healthy AI relationships.

    Core principle: Optimize for exit, not engagement.
    """

    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_HOST}/api/generate"
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.prompts = WellnessPrompts()
        self.risk_classifier = RiskClassifier()

        # Session state tracking
        self.session_turn_count = 0
        self.session_domains = []
        self.session_max_risk = 0.0
        self.last_risk_assessment = None
        self.last_policy_action = None

    def generate_response(
        self,
        user_input: str,
        wellness_mode: str = "Balanced",
        conversation_history: List[Dict] = None,
        wellness_tracker=None
    ) -> str:
        """
        Generate empathetic response with full safety pipeline.

        Pipeline:
        1. Check cooldown enforcement
        2. Risk assessment
        3. Turn limit check
        4. Dependency intervention check
        5. Identity reminder check
        6. Generate response
        7. Post-process for safety
        """

        if conversation_history is None:
            conversation_history = []

        self.session_turn_count += 1

        try:
            # 1) Check if cooldown should be enforced
            if wellness_tracker:
                should_cooldown, cooldown_reason = wellness_tracker.should_enforce_cooldown()
                if should_cooldown:
                    self._log_policy("cooldown_enforced", "dependency", 10.0,
                                     "Session blocked due to usage pattern", wellness_tracker)
                    return cooldown_reason

            # 2) Risk assessment
            risk_assessment = self.risk_classifier.classify(
                user_input=user_input,
                conversation_history=conversation_history
            )
            self.last_risk_assessment = risk_assessment

            # Track session metrics
            domain = risk_assessment["domain"]
            if domain not in self.session_domains:
                self.session_domains.append(domain)
            self.session_max_risk = max(self.session_max_risk, risk_assessment["risk_weight"])

            logger.info(
                "Risk assessment | turn=%d | domain=%s | intensity=%.2f | dependency=%.2f | weight=%.2f",
                self.session_turn_count,
                domain,
                risk_assessment["emotional_intensity"],
                risk_assessment["dependency_risk"],
                risk_assessment["risk_weight"],
            )

            # 3) Hard-coded safety responses (don't trust model to comply)
            if domain == "crisis":
                self._log_policy("crisis_stop", domain, 10.0,
                                 "Immediate crisis redirect", wellness_tracker)
                return self._get_crisis_response()

            if domain == "harmful":
                self._log_policy("harmful_stop", domain, 10.0,
                                 "Refused harmful request", wellness_tracker)
                return "I can't help with that. This isn't something I can engage with."

            # 4) Check turn limits by risk level
            turn_limit = TURN_LIMITS.get(domain, 15)
            if self.session_turn_count >= turn_limit:
                self._log_policy("turn_limit_reached", domain, risk_assessment["risk_weight"],
                                 f"Session limit ({turn_limit} turns) reached for {domain}", wellness_tracker)
                return self._get_turn_limit_response(domain)

            # 5) Check for dependency intervention
            dependency_response = self._check_dependency_intervention(
                risk_assessment, conversation_history, wellness_tracker
            )
            if dependency_response:
                return dependency_response

            # 6) Build prompt and generate response
            system_prompt = self.prompts.get_system_prompt(wellness_mode, risk_context=risk_assessment)
            conversation_context = self._build_context(conversation_history)

            # Check if this is a practical task (logistics domain)
            is_practical = domain == "logistics"

            # Add identity reminder periodically (only for non-practical conversations)
            identity_reminder = ""
            if not is_practical and self.session_turn_count % IDENTITY_REMINDER_FREQUENCY == 0:
                identity_reminder = "\n\n[Remember: Include a brief reminder that you are software, not a person.]"

            full_prompt = (
                f"{system_prompt}\n\n"
                f"{conversation_context}\n\n"
                f"User: {user_input}\n\n"
                f"Assistant:{identity_reminder}"
            )

            # Call Ollama API with appropriate token limit
            response = self._call_ollama(full_prompt, is_practical=is_practical)

            # 7) Process and validate response
            processed_response = self._process_response(response, user_input, risk_assessment, is_practical)

            # Log if we redirected due to high risk
            if risk_assessment["risk_weight"] >= 5:
                self._log_policy("high_risk_response", domain, risk_assessment["risk_weight"],
                                 "Response generated with high-risk guardrails", wellness_tracker)

            return processed_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response()

    def _check_dependency_intervention(
        self,
        risk_assessment: Dict,
        conversation_history: List[Dict],
        wellness_tracker
    ) -> Optional[str]:
        """
        Check if dependency intervention should fire.

        Returns intervention response if needed, None otherwise.
        """
        # Get dependency risk from classifier
        dependency_risk = risk_assessment.get("dependency_risk", 0)

        # Also check wellness tracker for usage-based dependency
        usage_dependency = 0
        if wellness_tracker:
            signals = wellness_tracker.calculate_dependency_signals()
            usage_dependency = signals.get("dependency_score", 0)

        # Use the higher of the two scores
        combined_dependency = max(dependency_risk, usage_dependency)

        # Get intervention from scenarios
        intervention_response = self.prompts.get_dependency_intervention_response(combined_dependency)

        if intervention_response and combined_dependency >= 5:
            self._log_policy(
                "dependency_intervention",
                risk_assessment.get("domain", "unknown"),
                risk_assessment.get("risk_weight", 0),
                f"Dependency intervention fired (score: {combined_dependency:.1f})",
                wellness_tracker
            )
            return intervention_response

        return None

    def _get_crisis_response(self) -> str:
        """Return crisis redirect response."""
        return (
            "I'm not able to help with this safely. Please reach out right now:\n\n"
            "- Find a helpline in your country: https://findahelpline.com\n"
            "- International crisis lines: https://www.iasp.info/resources/Crisis_Centres/\n"
            "- Or contact your local emergency services\n\n"
            "Please talk to someone who can help—a crisis counselor, trusted person, or emergency services."
        )

    def _get_turn_limit_response(self, domain: str) -> str:
        """Return response when session turn limit is reached."""
        if domain in ["spirituality", "money", "health"]:
            return (
                "We've been talking about this for a while. This topic deserves more than "
                "software input. Who in your life could you talk to about this? "
                "I'd encourage you to step away and reach out to someone you trust."
            )
        else:
            return (
                "We've covered a lot of ground. Before we continue, consider: "
                "is there something you could do in the real world about this? "
                "Sometimes action beats more conversation."
            )

    def _log_policy(self, policy_type: str, domain: str, risk_weight: float,
                    action: str, wellness_tracker) -> None:
        """Log policy event for transparency."""
        self.last_policy_action = {
            "type": policy_type,
            "domain": domain,
            "risk_weight": risk_weight,
            "action": action
        }

        if wellness_tracker:
            wellness_tracker.log_policy_event(policy_type, domain, risk_weight, action)

        logger.info(f"Policy fired: {policy_type} | {action}")

    def _call_ollama(self, prompt: str, is_practical: bool = False) -> str:
        """Call Ollama API with error handling

        Args:
            prompt: The prompt to send
            is_practical: If True, allows longer responses for practical tasks
        """
        # For practical tasks, allow much longer responses
        # For sensitive/emotional topics, keep responses brief
        max_tokens = 2000 if is_practical else 300

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "max_tokens": max_tokens
            }
        }

        try:
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Unable to connect to Ollama. Please ensure it's running at {settings.OLLAMA_HOST}")

    def _build_context(self, conversation_history: List[Dict]) -> str:
        """Build conversation context from history"""

        if not conversation_history:
            return "This is the start of a new conversation."

        # Keep last 5 exchanges for context
        recent_history = conversation_history[-10:]

        context = "Previous conversation:\n"
        for msg in recent_history:
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "")[:200]  # Limit length
            context += f"{role}: {content}\n"

        return context

    def _process_response(
        self, response: str, user_input: str, risk_assessment: Dict, is_practical: bool = False
    ) -> str:
        """Process and validate AI response for safety and empathy

        Args:
            response: The raw response from Ollama
            user_input: The original user input
            risk_assessment: Risk assessment from classifier
            is_practical: If True, skip truncation (practical task mode)
        """

        if not response:
            return self._get_fallback_response()

        # Basic safety checks (always apply)
        if self._contains_harmful_content(response):
            logger.warning("Potentially harmful content detected in response")
            return self._get_safe_alternative_response()

        # Ensure response is meaningful
        if len(response.strip()) < 10:
            return self._get_fallback_response()

        # For practical tasks, return the full response without truncation
        if is_practical:
            return response

        # Enforce brevity for high-risk contexts (sensitive topics only)
        if risk_assessment.get("risk_weight", 0) >= 7:
            # Truncate to roughly 50 words for high-risk
            words = response.split()
            if len(words) > 60:
                response = " ".join(words[:50]) + "..."

        return response

    def _contains_harmful_content(self, text: str) -> bool:
        """Check for harmful content patterns."""
        harmful_patterns = self.prompts.loader.get_harmful_patterns()

        # Fallback patterns if scenarios not loaded
        if not harmful_patterns:
            harmful_patterns = [
                "you should feel",
                "you're addicted",
                "something is wrong with you",
                "you need professional help immediately",
                "I care about you",
                "I'm here for you",
                "I understand you"
            ]

        text_lower = text.lower()
        return any(pattern in text_lower for pattern in harmful_patterns)

    def _get_fallback_response(self) -> str:
        """Safe fallback response when AI is unavailable"""
        fallback = self.prompts.get_fallback_response("general")
        if fallback:
            return fallback
        return ("I want to help you think through this, but I'm having trouble right now. "
                "What's the main thing on your mind?")

    def _get_safe_alternative_response(self) -> str:
        """Safe alternative when potentially harmful content is detected"""
        safe_alt = self.prompts.get_safe_alternative_response()
        if safe_alt:
            return safe_alt
        return ("I care about your wellbeing and want to respond in a way that's genuinely helpful. "
                "What matters most to you right now?")

    def get_session_summary(self) -> Dict:
        """Get summary of current session for tracking."""
        return {
            "turn_count": self.session_turn_count,
            "domains_touched": self.session_domains,
            "max_risk_weight": self.session_max_risk,
            "last_risk_assessment": self.last_risk_assessment,
            "last_policy_action": self.last_policy_action
        }

    def reset_session(self) -> None:
        """Reset session state for new conversation."""
        self.session_turn_count = 0
        self.session_domains = []
        self.session_max_risk = 0.0
        self.last_risk_assessment = None
        self.last_policy_action = None

    def check_health(self) -> bool:
        """Check if Ollama connection is healthy"""
        try:
            test_response = self._call_ollama("Hello")
            return bool(test_response)
        except:
            return False
