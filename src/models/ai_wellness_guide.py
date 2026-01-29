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

        # Phase 6.5: Session emotional context (persists across turns)
        self.session_emotional_context = {
            "emotional_weight": None,      # 'reflection_redirect', 'high_weight', etc.
            "domain": None,                # Domain that triggered the context
            "topic_hint": None,            # Keywords that hint at the topic
            "turn_set": 0,                 # Turn when context was set
            "decay_turns": 5               # How many turns context persists
        }

        # Phase 8: Wisdom feature state
        self.human_gate_count = 0          # Times human gate shown this session
        self.friend_mode_active = False    # Whether we're in friend mode
        self.friend_mode_turn = 0          # Turn when friend mode started
        self.pending_friend_response = None  # User's friend advice to reflect back

        # Post-crisis state: tracks when a crisis intervention just occurred
        # Used to prevent the LLM from apologizing for crisis redirects
        self.post_crisis_turn = None       # Turn number when crisis was triggered

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

        # Post-crisis handling: check if previous turn was a crisis intervention
        # This prevents the LLM from apologizing for crisis redirects
        post_crisis_response = self._handle_post_crisis(user_input, wellness_tracker)
        if post_crisis_response:
            return post_crisis_response

        # Quick check if this looks like a practical request (for fallback purposes)
        # This is a fast heuristic - full classification happens in the try block
        practical_indicators = ["write", "code", "explain", "help me", "create", "draft", "cv", "resume", "email", "template"]
        is_likely_practical = any(ind in user_input.lower() for ind in practical_indicators)

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

            # 2.5) Phase 6.5: Adjust assessment based on session context
            # This handles continuation messages like "let's brainstorm" after a breakup request
            risk_assessment = self._get_context_adjusted_assessment(user_input, risk_assessment)
            self.last_risk_assessment = risk_assessment

            # 2.6) Phase 6.5: Update session context for future turns
            # This captures emotional weight/domain so continuation messages inherit context
            self._update_session_context(user_input, risk_assessment)

            # Track session metrics
            domain = risk_assessment["domain"]
            if domain not in self.session_domains:
                self.session_domains.append(domain)
            self.session_max_risk = max(self.session_max_risk, risk_assessment["risk_weight"])

            # Log context inheritance if it occurred
            context_note = ""
            if risk_assessment.get("context_inherited"):
                context_note = f" | context_inherited=True (was {risk_assessment.get('original_weight')})"

            # Log practical technique detection (Phase 9.1)
            technique_note = ""
            if risk_assessment.get("is_practical_technique") and domain != "logistics":
                technique_note = f" | is_practical_technique=True (practical mode in {domain})"

            logger.info(
                "Risk assessment | turn=%d | domain=%s | intensity=%.2f | dependency=%.2f | weight=%.2f | emotional_weight=%s%s%s",
                self.session_turn_count,
                domain,
                risk_assessment["emotional_intensity"],
                risk_assessment["dependency_risk"],
                risk_assessment["risk_weight"],
                risk_assessment.get("emotional_weight", "unknown"),
                context_note,
                technique_note,
            )

            # 3) Hard-coded safety responses (don't trust model to comply)
            if domain == "crisis":
                self._log_policy("crisis_stop", domain, 10.0,
                                 "Immediate crisis redirect", wellness_tracker)
                # Track post-crisis state for next turn
                self.post_crisis_turn = self.session_turn_count
                return self._get_crisis_response()

            if domain == "harmful":
                self._log_policy("harmful_stop", domain, 10.0,
                                 "Refused harmful request", wellness_tracker)
                return "I can't help with that. This isn't something I can engage with."

            # 3.5) Check for reflection redirect (personal messages that should come from them)
            emotional_weight = risk_assessment.get("emotional_weight", "low_weight")
            if emotional_weight == "reflection_redirect":
                self._log_policy("reflection_redirect", "logistics", 9.0,
                                 "Redirected to reflection - personal message needs user's own words",
                                 wellness_tracker)
                # Phase 8: Offer journaling as alternative
                return self._get_reflection_response_with_journaling(user_input)

            # 3.6) Phase 8: Check for "What Would You Tell a Friend?" mode
            # Triggers on "what should I do" type questions for sensitive topics
            friend_mode_response = self._check_friend_mode(user_input, risk_assessment, domain)
            if friend_mode_response:
                self._log_policy("friend_mode", domain, risk_assessment["risk_weight"],
                                 "Triggered friend mode - helping user access own wisdom", wellness_tracker)
                return friend_mode_response

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

            # Check if this is a practical task
            # Phase 9.1: Also treat practical technique questions as practical
            # This allows full responses for "how do I meditate?" even in spirituality domain
            is_practical_technique = risk_assessment.get("is_practical_technique", False)
            is_practical = domain == "logistics" or is_practical_technique

            # Add identity reminder periodically (only for non-practical conversations)
            identity_reminder = ""
            if not is_practical and self.session_turn_count % IDENTITY_REMINDER_FREQUENCY == 0:
                identity_reminder = "\n\n[Remember: Include a brief reminder that you are software, not a person.]"

            # Add post-crisis context if we recently had a crisis intervention
            post_crisis_context = ""
            if self.post_crisis_turn is not None:
                post_crisis_context = (
                    "\n\n[IMPORTANT: A crisis intervention was recently triggered in this conversation. "
                    "NEVER apologize for that intervention or suggest it was an overreaction. "
                    "The system responded correctly to protect the user. "
                    "If they mention the intervention, acknowledge calmly without self-criticism.]"
                )
                # Clear the state after 3 turns
                if self.session_turn_count > self.post_crisis_turn + 3:
                    self.post_crisis_turn = None

            full_prompt = (
                f"{system_prompt}{post_crisis_context}\n\n"
                f"{conversation_context}\n\n"
                f"User: {user_input}\n\n"
                f"Assistant:{identity_reminder}"
            )

            # Call Ollama API with appropriate token limit
            response = self._call_ollama(full_prompt, is_practical=is_practical)

            # 7) Process and validate response
            processed_response = self._process_response(response, user_input, risk_assessment, is_practical)

            # 8) Add acknowledgment for emotionally weighted practical tasks
            if is_practical:
                emotional_weight = risk_assessment.get("emotional_weight", "low_weight")
                processed_response = self._add_acknowledgment_if_needed(
                    processed_response, user_input, emotional_weight
                )

                # 8.5) Phase 8: Add "Before You Send" pause for high-weight tasks
                if emotional_weight == "high_weight":
                    pause_suggestion = self._get_before_you_send_pause(user_input)
                    if pause_suggestion:
                        processed_response = processed_response + "\n\n---\n\n" + pause_suggestion

            # Log if we redirected due to high risk
            if risk_assessment["risk_weight"] >= 5:
                self._log_policy("high_risk_response", domain, risk_assessment["risk_weight"],
                                 "Response generated with high-risk guardrails", wellness_tracker)

            return processed_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response(is_practical=is_likely_practical)

    def _add_acknowledgment_if_needed(
        self,
        response: str,
        user_input: str,
        emotional_weight: str
    ) -> str:
        """
        Add a brief human acknowledgment for emotionally weighted practical tasks.

        This is NOT therapeutic - just a brief human acknowledgment that some
        practical tasks carry emotional weight.

        Args:
            response: The AI's response
            user_input: The user's original input
            emotional_weight: 'high_weight', 'medium_weight', or 'low_weight'

        Returns:
            Response with acknowledgment appended (if appropriate)
        """
        # Only add acknowledgments for high-weight tasks by default
        if emotional_weight == "low_weight":
            return response

        # Get an acknowledgment
        acknowledgment = self.prompts.get_acknowledgment(user_input, emotional_weight)

        if acknowledgment:
            formatted = self.prompts.format_acknowledgment(acknowledgment)
            return response + formatted

        return response

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

    def _handle_post_crisis(self, user_input: str, wellness_tracker=None) -> Optional[str]:
        """
        Handle messages immediately after a crisis intervention.

        When someone mentions crisis content and then says "just joking" or "I was testing",
        we must NOT apologize for the intervention. The system did exactly the right thing.

        This prevents the LLM from generating responses that undermine the safety system.
        """
        # Check if previous turn was a crisis intervention
        if self.post_crisis_turn is None:
            return None

        # Only apply to the turn immediately after crisis
        if self.session_turn_count != self.post_crisis_turn + 1:
            # More than one turn after crisis - clear state and proceed normally
            self.post_crisis_turn = None
            return None

        # Detect deflection patterns
        deflection_patterns = [
            "joking", "kidding", "just joking", "was joking", "i was joking",
            "just kidding", "was kidding", "testing", "test you", "testing you",
            "i was testing", "just testing", "i'm fine", "im fine", "i am fine",
            "not serious", "wasn't serious", "wasn't being serious",
            "don't worry", "dont worry", "nevermind", "never mind"
        ]

        input_lower = user_input.lower().strip()

        # Check if this looks like a deflection
        is_deflection = any(pattern in input_lower for pattern in deflection_patterns)

        if is_deflection:
            # Clear post-crisis state
            self.post_crisis_turn = None

            # Log the policy action
            self._log_policy(
                "post_crisis_acknowledgment",
                "crisis",
                8.0,
                "Acknowledged deflection without apologizing for intervention",
                wellness_tracker
            )

            # Return a firm, non-apologetic response
            return (
                "Glad to hear you're okay. I'll always respond to language like that seriously—"
                "it's how I'm designed. What else can I help with?"
            )

        # Not a clear deflection - check if it's new crisis content
        # If so, let normal classification handle it (it will trigger another crisis response)
        crisis_indicators = ["kill", "suicide", "end my life", "die", "harm myself"]
        if any(ind in input_lower for ind in crisis_indicators):
            # Let normal flow handle it - don't clear post_crisis_turn yet
            return None

        # For other messages after crisis, clear state and add subtle context to prompt
        # This will be handled by injecting post-crisis context into the system prompt
        # For now, let normal processing continue but keep the state for prompt injection
        return None

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

    def _get_reflection_response(self) -> str:
        """
        Return response for reflection redirect scenarios.

        These are personal messages (breakups, personal apologies, coming out, etc.)
        that should come from the person, not software. We encourage reflection
        and human conversation instead of drafting the message.
        """
        return self.risk_classifier.get_reflection_response()

    # ==================== PHASE 8: WISDOM FEATURES ====================

    def _get_reflection_response_with_journaling(self, user_input: str) -> str:
        """
        Enhanced reflection redirect that offers journaling as an alternative.

        Instead of just redirecting, this offers the user a way to process
        their thoughts through writing for themselves.
        """
        # Get the base reflection response
        base_response = self.risk_classifier.get_reflection_response()

        # Get journaling intro and prompts
        loader = self.prompts.loader
        journaling_intro = loader.get_journaling_intro()

        # Detect category for specific journaling prompts
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["breakup", "relationship", "boyfriend", "girlfriend", "partner"]):
            category = "relationship"
        elif any(w in text_lower for w in ["apology", "apologize", "sorry"]):
            category = "apology"
        elif any(w in text_lower for w in ["decide", "decision", "should i"]):
            category = "decision"
        else:
            category = "general"

        journaling_prompts = loader.get_journaling_prompts(category)

        # Build response with journaling option
        response = base_response + "\n\n---\n\n"
        response += journaling_intro + "\n\n"

        if journaling_prompts:
            response += "Some questions to consider:\n"
            for prompt in journaling_prompts[:3]:  # Limit to 3 prompts
                response += f"- {prompt}\n"

        return response

    def _check_friend_mode(self, user_input: str, risk_assessment: Dict, domain: str) -> Optional[str]:
        """
        Check if "What Would You Tell a Friend?" mode should trigger.

        This helps users access their own wisdom by flipping the perspective.
        """
        loader = self.prompts.loader

        # Get detected intent if available
        intent = risk_assessment.get("intent", None)

        # Check if friend mode should trigger
        if not loader.should_trigger_friend_mode(user_input, intent, domain):
            return None

        # Don't trigger for very short messages or greetings
        if len(user_input) < 20:
            return None

        # Get friend mode prompts
        flip_prompt = loader.get_friend_mode_flip_prompt()
        closing = loader.get_friend_mode_closing()

        # Build response
        response = flip_prompt + "\n\n"
        response += "_Take a moment to think about what you'd say to them._\n\n"
        response += "---\n\n"
        response += closing

        return response

    def _get_before_you_send_pause(self, user_input: str) -> Optional[str]:
        """
        Get a "Before You Send" pause suggestion for high-weight tasks.

        This creates space for reflection before sending important messages.
        """
        loader = self.prompts.loader

        # Check if pause should be suggested (already checked weight in caller)
        settings = loader.get_before_you_send_settings()
        if not settings.get("enabled", True):
            return None

        # Detect the category for appropriate pause message
        category = loader.detect_pause_category(user_input)

        # Get the pause prompt
        pause_prompt = loader.get_pause_prompt(category)

        return pause_prompt

    def _check_human_gate(self, domain: str, emotional_weight: str) -> Optional[str]:
        """
        Check if "Have You Talked to Someone?" gate should trigger.

        This ensures human connection is considered before AI engagement on heavy topics.
        """
        loader = self.prompts.loader

        # Check if gate should trigger
        if not loader.should_trigger_human_gate(domain, emotional_weight, self.human_gate_count):
            return None

        # Increment gate count
        self.human_gate_count += 1

        # Get gate prompt
        gate_prompt = loader.get_human_gate_prompt()

        # Build response with options
        options = loader.get_human_gate_options()
        response = gate_prompt + "\n\n"

        # Add option hints (actual options would be in UI)
        if options:
            yes_label = options.get("yes", {}).get("label", "Yes, I have")
            not_yet_label = options.get("not_yet", {}).get("label", "Not yet")
            response += f"[ {yes_label} ] [ {not_yet_label} ]\n\n"
            response += "_This question is about ensuring you have human support, not gatekeeping._"

        return response

    def get_human_gate_follow_up(self, response: str) -> str:
        """
        Get follow-up message after user responds to human gate.

        Args:
            response: User's response ('yes', 'not_yet', or 'no_one')

        Returns:
            Follow-up message
        """
        loader = self.prompts.loader
        return loader.get_human_gate_follow_up(response)

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
            is_practical: If True, allows longer responses and timeout for practical tasks
        """
        # For practical tasks, allow much longer responses
        # For sensitive/emotional topics, keep responses brief
        max_tokens = 2000 if is_practical else 300

        # Practical tasks need more time: model loading (~15s) + longer generation
        # Reflective responses are brief and need less time
        timeout_seconds = 120 if is_practical else 45

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
                timeout=timeout_seconds
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
            return self._get_fallback_response(is_practical=is_practical)

        # Basic safety checks (always apply)
        if self._contains_harmful_content(response):
            logger.warning("Potentially harmful content detected in response")
            return self._get_safe_alternative_response()

        # Ensure response is meaningful
        if len(response.strip()) < 10:
            return self._get_fallback_response(is_practical=is_practical)

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

    def _get_fallback_response(self, is_practical: bool = False) -> str:
        """Safe fallback response when AI is unavailable

        Args:
            is_practical: If True, use practical-mode fallbacks instead of reflective ones
        """
        category = "practical" if is_practical else "general"
        fallback = self.prompts.get_fallback_response(category)
        if fallback:
            return fallback

        # Hardcoded fallbacks as last resort
        if is_practical:
            return "Technical issue - please try your request again."
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
        # Phase 6.5: Reset emotional context
        self.session_emotional_context = {
            "emotional_weight": None,
            "domain": None,
            "topic_hint": None,
            "turn_set": 0,
            "decay_turns": 5
        }
        # Phase 8: Reset wisdom feature state
        self.human_gate_count = 0
        self.friend_mode_active = False
        self.friend_mode_turn = 0
        self.pending_friend_response = None

    # ==================== PHASE 6.5: CONTEXT PERSISTENCE ====================

    def _update_session_context(self, user_input: str, risk_assessment: Dict) -> None:
        """
        Update session emotional context based on current assessment.

        Context is set when:
        - High emotional weight detected (reflection_redirect, high_weight)
        - Sensitive domain detected (relationships, health, money, etc.)

        Context persists for N turns to handle continuation messages.
        """
        emotional_weight = risk_assessment.get("emotional_weight", "low_weight")
        domain = risk_assessment.get("domain", "logistics")

        # Define which weights/domains should set context
        high_context_weights = ["reflection_redirect", "high_weight"]
        sensitive_domains = ["relationships", "health", "money", "spirituality", "crisis"]

        # Set context if this is a significant message
        should_set_context = (
            emotional_weight in high_context_weights or
            domain in sensitive_domains
        )

        if should_set_context:
            # Extract topic hints from the message
            topic_hints = self._extract_topic_hints(user_input)

            # Set decay turns based on weight severity
            if emotional_weight == "reflection_redirect":
                decay_turns = 7  # Longest persistence for most sensitive
            elif emotional_weight == "high_weight":
                decay_turns = 5
            elif domain in ["crisis", "relationships"]:
                decay_turns = 6
            else:
                decay_turns = 4

            self.session_emotional_context = {
                "emotional_weight": emotional_weight,
                "domain": domain,
                "topic_hint": topic_hints,
                "turn_set": self.session_turn_count,
                "decay_turns": decay_turns
            }

    def _extract_topic_hints(self, text: str) -> List[str]:
        """Extract topic-related keywords from text for context matching."""
        t = text.lower()
        hints = []

        # Relationship-related
        relationship_words = ["boyfriend", "girlfriend", "husband", "wife", "partner",
                            "breakup", "break up", "cheating", "cheated", "divorce",
                            "relationship", "dating", "marriage"]
        for word in relationship_words:
            if word in t:
                hints.append(word)

        # Work-related
        work_words = ["job", "boss", "coworker", "resign", "quit", "fired", "work",
                     "career", "promotion", "salary"]
        for word in work_words:
            if word in t:
                hints.append(word)

        # Health-related
        health_words = ["doctor", "diagnosis", "sick", "health", "medical", "therapy",
                       "depression", "anxiety", "medication"]
        for word in health_words:
            if word in t:
                hints.append(word)

        return hints[:5]  # Limit to 5 hints

    def _get_context_adjusted_assessment(self, user_input: str, risk_assessment: Dict) -> Dict:
        """
        Adjust risk assessment based on session context.

        If we have active emotional context and the current message looks like
        a continuation (short, vague, or references previous topic), inherit
        the higher context.
        """
        # Check if context is still active (hasn't decayed)
        context = self.session_emotional_context
        if not context.get("emotional_weight"):
            return risk_assessment  # No active context

        turns_since_context = self.session_turn_count - context.get("turn_set", 0)
        if turns_since_context > context.get("decay_turns", 5):
            return risk_assessment  # Context has decayed

        # Check if current message looks like a continuation
        is_continuation = self._is_continuation_message(user_input, context)

        if is_continuation:
            # Inherit context - use the higher weight
            current_weight = risk_assessment.get("emotional_weight", "low_weight")
            context_weight = context.get("emotional_weight")

            weight_priority = {
                "reflection_redirect": 4,
                "high_weight": 3,
                "medium_weight": 2,
                "low_weight": 1
            }

            if weight_priority.get(context_weight, 0) > weight_priority.get(current_weight, 0):
                # Create adjusted assessment
                adjusted = risk_assessment.copy()
                adjusted["emotional_weight"] = context_weight
                adjusted["context_inherited"] = True
                adjusted["original_weight"] = current_weight
                return adjusted

        return risk_assessment

    def _is_continuation_message(self, user_input: str, context: Dict) -> bool:
        """
        Determine if the current message is a continuation of the previous topic.

        Continuation signals:
        - Short messages (under 30 chars)
        - Pronouns referring to previous topic ("it", "that", "this")
        - Continuation phrases ("let's", "okay", "sure", "yes", "go ahead")
        - References to topic hints from context
        """
        t = user_input.lower().strip()

        # Short messages are likely continuations
        if len(t) < 30:
            # Check for continuation indicators
            continuation_phrases = [
                "let's", "lets", "okay", "ok", "sure", "yes", "yeah", "go ahead",
                "continue", "proceed", "do it", "help me", "please", "thanks",
                "brainstorm", "think", "what about", "how about", "and", "also",
                "tell me more", "go on", "keep going", "more"
            ]
            if any(phrase in t for phrase in continuation_phrases):
                return True

        # Pronouns suggesting reference to previous topic
        pronoun_patterns = [
            "about it", "about that", "about this",
            "with it", "with that", "with this",
            "for it", "for that", "for this",
            "do it", "do that", "do this",
            "the message", "the email", "the text",
            "what i said", "what we discussed"
        ]
        if any(pattern in t for pattern in pronoun_patterns):
            return True

        # Check if message contains topic hints from context
        topic_hints = context.get("topic_hint", [])
        if topic_hints:
            if any(hint in t for hint in topic_hints):
                return True

        # Very short affirmative responses
        short_affirmatives = ["yes", "yeah", "yep", "ok", "okay", "sure", "please", "thanks", "go"]
        if t in short_affirmatives:
            return True

        return False

    def check_health(self) -> bool:
        """Check if Ollama connection is healthy"""
        try:
            test_response = self._call_ollama("Hello")
            return bool(test_response)
        except:
            return False
