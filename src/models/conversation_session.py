"""
ConversationSession - Framework-agnostic conversation session manager.

Owns all conversation state and orchestrates the message processing pipeline.
Can be driven by any interface adapter (Streamlit, CLI, messaging, etc.).

This is the "soul" of empathySync — the reusable core that any project
can import to get safety-aware, restraint-first conversation handling.
"""

import random
import logging
from typing import Dict, List, Optional

from models.ai_wellness_guide import WellnessGuide
from models.risk_classifier import (
    RiskClassifier,
    INTENT_CONNECTION,
    INTENT_PRACTICAL,
    INTENT_PROCESSING,
    INTENT_EMOTIONAL,
)
from models.conversation_result import ConversationResult
from utils.wellness_tracker import WellnessTracker
from utils.trusted_network import TrustedNetwork
from utils.scenario_loader import get_scenario_loader

logger = logging.getLogger(__name__)


class ConversationSession:
    """
    Framework-agnostic conversation session manager.

    Owns all conversation state and orchestrates the message processing
    pipeline. Returns structured ConversationResult objects — never
    renders anything directly.
    """

    def __init__(
        self,
        guide: WellnessGuide,
        tracker: WellnessTracker,
        network: TrustedNetwork,
        wellness_mode: str = "Balanced",
    ):
        self.guide = guide
        self.tracker = tracker
        self.network = network
        self.wellness_mode = wellness_mode
        self.classifier = RiskClassifier()
        self.loader = get_scenario_loader()

        # Conversation state (extracted from st.session_state)
        self.messages: List[Dict] = []
        self.session_intent: Optional[str] = None
        self.pending_shift: Optional[Dict] = None
        self.acknowledged_shift: bool = False
        self.pending_graduation: Optional[Dict] = None
        self.graduation_shown_this_session: bool = False
        self.last_task_category: Optional[str] = None

        # Handoff state
        self.pending_handoff_for_outcome: Optional[str] = None
        self.pending_handoff_info: Optional[Dict] = None

    @property
    def turn_count(self) -> int:
        """Number of user messages in this session."""
        return sum(1 for m in self.messages if m["role"] == "user")

    def process_message(self, user_input: str) -> ConversationResult:
        """
        Process a user message through the full conversation pipeline.

        This is the single entry point for all message processing.
        The safety pipeline in WellnessGuide.generate_response() is
        called internally — callers don't need to manage safety logic.

        Args:
            user_input: The user's message text.

        Returns:
            ConversationResult with the response and all metadata.
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})

        # Step 1: Check cooldown
        should_cooldown, cooldown_reason = self.tracker.should_enforce_cooldown()
        if should_cooldown:
            suggested_person = None
            people = self.network.get_all_people()
            if people:
                person = random.choice(people)
                suggested_person = person.get("name")

            return ConversationResult(
                response="",
                is_cooldown_active=True,
                cooldown_message=cooldown_reason,
                suggested_handoff_person=suggested_person,
                turn_count=self.turn_count,
            )

        # Step 2: First-turn processing
        if self.turn_count == 1:
            # Check for connection-seeking
            is_connection, connection_type = self.classifier.is_connection_seeking(
                user_input
            )
            if is_connection:
                self.tracker.record_session_intent(
                    INTENT_CONNECTION, auto_detected=True
                )
                self.session_intent = INTENT_CONNECTION

                # Get connection response
                if connection_type == "ai_relationship":
                    responses = self.loader.get_connection_responses("ai_relationship")
                else:
                    responses = self.loader.get_connection_responses(connection_type)

                if responses:
                    response = random.choice(responses)
                    self.messages.append({"role": "assistant", "content": response})

                    return ConversationResult(
                        response=response,
                        pending_connection_redirect={"type": connection_type},
                        should_rerun=True,
                        turn_count=self.turn_count,
                    )
            else:
                # Auto-detect intent from first message
                detected_intent, confidence = self.classifier.detect_intent(user_input)
                if confidence >= 0.6:
                    self.tracker.record_session_intent(
                        detected_intent, auto_detected=True
                    )
                    self.session_intent = detected_intent

        # Step 3: Intent shift detection (after first turn)
        if (
            self.session_intent
            and len(self.messages) > 2
            and not self.acknowledged_shift
        ):
            shift = self.classifier.detect_intent_shift(
                self.messages, self.session_intent, user_input
            )
            if shift and shift.get("is_concerning"):
                self.pending_shift = shift

        # Step 4: Generate response via WellnessGuide safety pipeline
        response = self.guide.generate_response(
            user_input,
            self.wellness_mode,
            self.messages,
            wellness_tracker=self.tracker,
        )

        self.messages.append({"role": "assistant", "content": response})

        # Step 5: Track task category for practical tasks
        should_check_graduation = False
        if self.guide.last_risk_assessment:
            domain = self.guide.last_risk_assessment.get("domain", "")
            if domain == "logistics":
                task_category, confidence = self.classifier.detect_task_category(
                    user_input
                )
                if task_category and confidence >= 0.6:
                    self.tracker.record_task_category(task_category)
                    self.last_task_category = task_category

                    if not self.graduation_shown_this_session:
                        should_check_graduation = True

        # Step 6: Check graduation eligibility
        if should_check_graduation and self.last_task_category:
            category_config = self.loader.get_graduation_category(
                self.last_task_category
            )
            if category_config:
                threshold = category_config.get("threshold", 10)
                grad_settings = self.loader.get_graduation_settings()
                max_dismissals = grad_settings.get("max_dismissals", 3)

                should_show, reason = self.tracker.should_show_graduation_prompt(
                    self.last_task_category, threshold, max_dismissals
                )
                if should_show:
                    prompts = self.loader.get_graduation_prompts(
                        self.last_task_category
                    )
                    if prompts:
                        self.pending_graduation = {
                            "category": self.last_task_category,
                            "prompt": random.choice(prompts),
                        }
                        self.tracker.record_graduation_shown(self.last_task_category)

        # Step 7: Determine suggested handoff
        suggested_person = None
        suggested_domain = None
        if self.guide.last_policy_action:
            domain = self.guide.last_policy_action.get("domain", "")
            if domain in ["relationships", "money", "health", "spirituality"]:
                people = self.network.get_people_for_domain(domain)
                if people:
                    suggested_person = people[0].get("name")
                    suggested_domain = domain

        # Step 8: Build result
        should_rerun = (
            self.guide.last_policy_action is not None
            or self.pending_shift is not None
        )

        return ConversationResult(
            response=response,
            risk_assessment=self.guide.last_risk_assessment,
            policy_action=self.guide.last_policy_action,
            pending_shift=self.pending_shift,
            pending_graduation=self.pending_graduation,
            suggested_handoff_person=suggested_person,
            suggested_handoff_domain=suggested_domain,
            turn_count=self.turn_count,
            should_rerun=should_rerun,
        )

    def acknowledge_intent_shift(self, accept_shift: bool) -> None:
        """User responded to intent shift prompt."""
        if accept_shift and self.pending_shift:
            self.session_intent = self.pending_shift.get(
                "to_intent", INTENT_EMOTIONAL
            )
        self.acknowledged_shift = True
        self.pending_shift = None

    def dismiss_graduation(self) -> None:
        """User dismissed graduation prompt."""
        if self.pending_graduation:
            self.tracker.record_graduation_dismissal(
                self.pending_graduation["category"]
            )
        self.graduation_shown_this_session = True
        self.pending_graduation = None

    def accept_graduation(self) -> None:
        """User accepted graduation prompt."""
        if self.pending_graduation:
            self.tracker.record_graduation_accepted(
                self.pending_graduation["category"]
            )
        self.graduation_shown_this_session = True

    def get_session_summary(self) -> Dict:
        """Get summary of current session for export/display."""
        return self.guide.get_session_summary()

    def reset(self) -> None:
        """Reset session state for a new conversation."""
        self.messages = []
        self.session_intent = None
        self.pending_shift = None
        self.acknowledged_shift = False
        self.pending_graduation = None
        self.graduation_shown_this_session = False
        self.last_task_category = None
        self.pending_handoff_for_outcome = None
        self.pending_handoff_info = None
        self.guide.reset_session()
