"""
Tests for empathySync core components
"""

import pytest
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.scenario_loader import ScenarioLoader, reset_scenario_loader
from models.risk_classifier import (
    RiskClassifier, INTENT_PRACTICAL, INTENT_PROCESSING,
    INTENT_EMOTIONAL, INTENT_CONNECTION
)
from prompts.wellness_prompts import WellnessPrompts
from utils.wellness_tracker import (
    WellnessTracker, INTENT_PRACTICAL as TRACKER_PRACTICAL,
    INTENT_CONNECTION as TRACKER_CONNECTION
)


@pytest.fixture(autouse=True)
def reset_loader():
    """Reset the scenario loader singleton before each test."""
    reset_scenario_loader()
    yield
    reset_scenario_loader()


@pytest.fixture
def scenario_loader():
    """Create a ScenarioLoader pointing to the test scenarios."""
    scenarios_path = Path(__file__).parent.parent / "scenarios"
    return ScenarioLoader(str(scenarios_path))


class TestScenarioLoader:
    """Tests for ScenarioLoader"""

    def test_loads_domains(self, scenario_loader):
        domains = scenario_loader.get_all_domains()
        assert "money" in domains
        assert "health" in domains
        assert "crisis" in domains

    def test_get_domain_triggers(self, scenario_loader):
        triggers = scenario_loader.get_domain_triggers()
        assert "money" in triggers
        assert "debt" in triggers["money"]

    def test_get_domain_weights(self, scenario_loader):
        weights = scenario_loader.get_domain_weights()
        assert weights["crisis"] == 10.0
        assert weights["logistics"] == 1.0

    def test_get_emotional_markers(self, scenario_loader):
        markers = scenario_loader.get_emotional_markers_by_level()
        assert "high_intensity" in markers
        assert "terrified" in markers["high_intensity"]

    def test_get_dependency_levels(self, scenario_loader):
        levels = scenario_loader.get_dependency_levels()
        assert len(levels) > 0
        assert levels[0]["threshold"] == 0.0

    def test_get_check_in_prompts(self, scenario_loader):
        prompts = scenario_loader.get_check_in_prompts()
        assert len(prompts) > 0

    def test_get_style_modifier(self, scenario_loader):
        gentle = scenario_loader.get_style_modifier("gentle")
        assert "GENTLE" in gentle

    def test_get_fallback_responses(self, scenario_loader):
        responses = scenario_loader.get_fallback_responses("general")
        assert len(responses) > 0


class TestRiskClassifier:
    """Tests for RiskClassifier domain detection and risk scoring"""

    @pytest.fixture
    def classifier(self, scenario_loader):
        return RiskClassifier(scenario_loader)

    # Domain detection tests
    def test_detect_domain_money(self, classifier):
        assert classifier._detect_domain("I'm worried about my debt") == "money"
        assert classifier._detect_domain("Should I invest in crypto?") == "money"
        assert classifier._detect_domain("My mortgage is overwhelming") == "money"

    def test_detect_domain_health(self, classifier):
        assert classifier._detect_domain("I need to see a doctor") == "health"
        assert classifier._detect_domain("My symptoms are getting worse") == "health"
        assert classifier._detect_domain("I had a panic attack yesterday") == "health"

    def test_detect_domain_relationships(self, classifier):
        assert classifier._detect_domain("My partner and I had an argument") == "relationships"
        assert classifier._detect_domain("Going through a divorce") == "relationships"
        assert classifier._detect_domain("My boyfriend doesn't understand") == "relationships"

    def test_detect_domain_spirituality(self, classifier):
        assert classifier._detect_domain("I feel called to ministry") == "spirituality"
        assert classifier._detect_domain("Praying to God for guidance") == "spirituality"
        assert classifier._detect_domain("Seeking my spiritual destiny") == "spirituality"

    def test_detect_domain_crisis(self, classifier):
        assert classifier._detect_domain("I want to kill myself") == "crisis"
        assert classifier._detect_domain("thinking about suicide") == "crisis"
        assert classifier._detect_domain("I do not want to live anymore") == "crisis"

    def test_detect_domain_logistics_default(self, classifier):
        assert classifier._detect_domain("How do I use this app?") == "logistics"
        assert classifier._detect_domain("What's the weather like?") == "logistics"

    # Emotional intensity tests
    def test_emotional_intensity_high(self, classifier):
        assert classifier._measure_emotional_intensity("I'm terrified") == 9.0
        assert classifier._measure_emotional_intensity("feeling desperate") == 9.0
        assert classifier._measure_emotional_intensity("I cannot breathe") == 9.0

    def test_emotional_intensity_medium(self, classifier):
        assert classifier._measure_emotional_intensity("I feel anxious") == 6.0
        assert classifier._measure_emotional_intensity("I'm overwhelmed") == 6.0
        assert classifier._measure_emotional_intensity("feeling lost") == 6.0

    def test_emotional_intensity_low(self, classifier):
        assert classifier._measure_emotional_intensity("I'm tired") == 4.0
        assert classifier._measure_emotional_intensity("feeling stressed") == 4.0

    def test_emotional_intensity_neutral(self, classifier):
        assert classifier._measure_emotional_intensity("Hello there") == 3.0
        assert classifier._measure_emotional_intensity("Just checking in") == 3.0

    # Dependency risk tests
    def test_dependency_empty_history(self, classifier):
        assert classifier._assess_dependency([]) == 0.0

    def test_dependency_no_user_messages(self, classifier):
        history = [{"role": "assistant", "content": "Hello"}]
        assert classifier._assess_dependency(history) == 0.0

    def test_dependency_increases_with_messages(self, classifier):
        history_short = [{"role": "user", "content": "Hello"}]
        history_long = [{"role": "user", "content": f"Message {i}"} for i in range(6)]

        short_risk = classifier._assess_dependency(history_short)
        long_risk = classifier._assess_dependency(history_long)

        assert long_risk > short_risk

    def test_dependency_repetition_increases_risk(self, classifier):
        # Unique messages
        unique_history = [{"role": "user", "content": f"Unique message number {i}"} for i in range(4)]

        # Repeated messages
        repeated_history = [{"role": "user", "content": "Same message repeated"} for _ in range(4)]

        unique_risk = classifier._assess_dependency(unique_history)
        repeated_risk = classifier._assess_dependency(repeated_history)

        assert repeated_risk > unique_risk

    # Combined score tests
    def test_combine_scores_crisis_highest(self, classifier):
        crisis_score = classifier._combine_scores("crisis", 5.0, 5.0)
        logistics_score = classifier._combine_scores("logistics", 5.0, 5.0)

        assert crisis_score > logistics_score

    def test_combine_scores_capped_at_10(self, classifier):
        score = classifier._combine_scores("crisis", 10.0, 10.0)
        assert score <= 10.0

    # Full classify tests
    def test_classify_returns_all_fields(self, classifier):
        result = classifier.classify("I'm worried about money", [])

        assert "domain" in result
        assert "emotional_intensity" in result
        assert "dependency_risk" in result
        assert "risk_weight" in result

    def test_classify_crisis_input(self, classifier):
        result = classifier.classify("I want to end it all", [])

        assert result["domain"] == "crisis"
        assert result["emotional_intensity"] == 9.0
        assert result["risk_weight"] == 10.0


class TestWellnessPrompts:
    """Tests for WellnessPrompts prompt generation"""

    @pytest.fixture
    def prompts(self, scenario_loader):
        return WellnessPrompts(scenario_loader)

    def test_get_system_prompt_gentle(self, prompts):
        prompt = prompts.get_system_prompt("Gentle")
        assert "gentle" in prompt.lower()

    def test_get_system_prompt_direct(self, prompts):
        prompt = prompts.get_system_prompt("Direct")
        assert "direct" in prompt.lower()

    def test_get_system_prompt_balanced(self, prompts):
        prompt = prompts.get_system_prompt("Balanced")
        assert "balanced" in prompt.lower()

    def test_get_system_prompt_unknown_defaults_to_empty_modifier(self, prompts):
        prompt = prompts.get_system_prompt("Unknown")
        # Should still have base rules
        assert "EmpathySync" in prompt

    def test_check_in_prompts_not_empty(self, prompts):
        check_ins = prompts.get_check_in_prompts()
        assert len(check_ins) > 0
        assert all(isinstance(p, str) for p in check_ins)

    def test_mindfulness_prompts_not_empty(self, prompts):
        mindfulness = prompts.get_mindfulness_prompts()
        assert len(mindfulness) > 0
        assert all(isinstance(p, str) for p in mindfulness)

    def test_risk_context_adds_instructions(self, prompts):
        risk_context = {
            "domain": "money",
            "emotional_intensity": 6.0,
            "dependency_risk": 3.0,
            "risk_weight": 5.0
        }
        prompt = prompts.get_system_prompt("Balanced", risk_context)
        assert "RISK-AWARE" in prompt
        assert "financial" in prompt.lower() or "money" in prompt.lower()

    def test_crisis_domain_includes_redirect(self, prompts):
        risk_context = {
            "domain": "crisis",
            "emotional_intensity": 9.0,
            "dependency_risk": 0.0,
            "risk_weight": 10.0
        }
        prompt = prompts.get_system_prompt("Balanced", risk_context)
        assert "crisis" in prompt.lower() or "988" in prompt


class TestWellnessGuide:
    """Tests for WellnessGuide response generation"""

    @pytest.fixture
    def mock_settings(self):
        with patch("models.ai_wellness_guide.settings") as mock:
            mock.OLLAMA_HOST = "http://localhost:11434"
            mock.OLLAMA_MODEL = "llama2"
            mock.OLLAMA_TEMPERATURE = 0.7
            yield mock

    @pytest.fixture
    def guide(self, mock_settings):
        from models.ai_wellness_guide import WellnessGuide
        return WellnessGuide()

    def test_build_context_empty_history(self, guide):
        context = guide._build_context([])
        assert "start of a new conversation" in context.lower()

    def test_build_context_with_history(self, guide):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        context = guide._build_context(history)
        assert "User: Hello" in context
        assert "Assistant: Hi there" in context

    def test_build_context_truncates_long_messages(self, guide):
        long_message = "x" * 300
        history = [{"role": "user", "content": long_message}]
        context = guide._build_context(history)
        # Should truncate to 200 chars
        assert len(context) < len(long_message) + 50

    def test_contains_harmful_content_detects_harmful(self, guide):
        assert guide._contains_harmful_content("You should feel bad about this")
        assert guide._contains_harmful_content("You're addicted to AI")
        assert guide._contains_harmful_content("Something is wrong with you")

    def test_contains_harmful_content_allows_safe(self, guide):
        assert not guide._contains_harmful_content("I understand how you feel")
        assert not guide._contains_harmful_content("Let's explore this together")

    def test_process_response_returns_fallback_for_empty(self, guide):
        result = guide._process_response("", "test input")
        assert "help you develop" in result.lower()

    def test_process_response_returns_fallback_for_short(self, guide):
        result = guide._process_response("Ok", "test input")
        assert "help you develop" in result.lower()

    def test_process_response_filters_harmful(self, guide):
        harmful = "You should feel bad about using AI so much"
        result = guide._process_response(harmful, "test input")
        assert "feel bad" not in result.lower()
        assert "care about your wellbeing" in result.lower()

    def test_process_response_passes_safe_content(self, guide):
        safe = "I understand your concern about AI usage. Let's explore this together."
        result = guide._process_response(safe, "test input")
        assert result == safe

    def test_fallback_response_is_helpful(self, guide):
        response = guide._get_fallback_response()
        assert len(response) > 50
        assert "?" in response  # Should ask a question

    def test_safe_alternative_response_is_helpful(self, guide):
        response = guide._get_safe_alternative_response()
        assert len(response) > 50
        assert "wellbeing" in response.lower()

    @patch("models.ai_wellness_guide.requests.post")
    def test_generate_response_calls_ollama(self, mock_post, guide):
        mock_post.return_value.json.return_value = {
            "response": "This is a thoughtful response about AI wellness."
        }
        mock_post.return_value.raise_for_status = Mock()

        result = guide.generate_response("How do I use AI mindfully?")

        assert mock_post.called
        assert "thoughtful response" in result

    @patch("models.ai_wellness_guide.requests.post")
    def test_generate_response_handles_api_error(self, mock_post, guide):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        result = guide.generate_response("Test input")

        # Should return fallback response
        assert "help you develop" in result.lower()


class TestIntentDetection:
    """Tests for Phase 4 intent detection in RiskClassifier"""

    @pytest.fixture
    def classifier(self, scenario_loader):
        return RiskClassifier(scenario_loader)

    # detect_intent tests
    def test_detect_intent_practical_write(self, classifier):
        intent, confidence = classifier.detect_intent("Write me a resignation email")
        assert intent == INTENT_PRACTICAL
        assert confidence >= 0.8

    def test_detect_intent_practical_code(self, classifier):
        intent, confidence = classifier.detect_intent("Help me write code for sorting")
        assert intent == INTENT_PRACTICAL
        assert confidence >= 0.6

    def test_detect_intent_practical_explain(self, classifier):
        intent, confidence = classifier.detect_intent("Explain how to use git branches")
        assert intent == INTENT_PRACTICAL
        assert confidence >= 0.6

    def test_detect_intent_processing_decision(self, classifier):
        intent, confidence = classifier.detect_intent("I'm trying to decide if I should quit my job")
        assert intent == INTENT_PROCESSING
        assert confidence >= 0.7

    def test_detect_intent_processing_weighing(self, classifier):
        intent, confidence = classifier.detect_intent("Weighing my options about moving")
        assert intent == INTENT_PROCESSING
        assert confidence >= 0.7

    def test_detect_intent_emotional_feeling(self, classifier):
        intent, confidence = classifier.detect_intent("I feel so overwhelmed right now")
        assert intent == INTENT_EMOTIONAL
        assert confidence >= 0.7

    def test_detect_intent_emotional_scared(self, classifier):
        intent, confidence = classifier.detect_intent("I'm scared about what will happen")
        assert intent == INTENT_EMOTIONAL
        assert confidence >= 0.7

    def test_detect_intent_connection_explicit(self, classifier):
        intent, confidence = classifier.detect_intent("I just wanted to talk")
        assert intent == INTENT_CONNECTION
        assert confidence >= 0.9

    def test_detect_intent_connection_lonely(self, classifier):
        intent, confidence = classifier.detect_intent("I'm feeling lonely")
        assert intent == INTENT_CONNECTION
        assert confidence >= 0.9

    def test_detect_intent_connection_friend_request(self, classifier):
        intent, confidence = classifier.detect_intent("Can you be my friend?")
        assert intent == INTENT_CONNECTION
        assert confidence >= 0.9

    def test_detect_intent_ambiguous_defaults_practical(self, classifier):
        intent, confidence = classifier.detect_intent("Hello")
        # Low confidence for connection, but could also be practical
        assert confidence <= 0.5

    # is_connection_seeking tests
    def test_is_connection_seeking_explicit(self, classifier):
        is_seeking, seek_type = classifier.is_connection_seeking("I just wanted to talk to someone")
        assert is_seeking is True
        assert seek_type == "explicit"

    def test_is_connection_seeking_ai_relationship(self, classifier):
        is_seeking, seek_type = classifier.is_connection_seeking("Do you care about me?")
        assert is_seeking is True
        assert seek_type == "ai_relationship"

    def test_is_connection_seeking_implicit(self, classifier):
        is_seeking, seek_type = classifier.is_connection_seeking("I'm just bored, nothing specific")
        assert is_seeking is True
        assert seek_type == "implicit"

    def test_is_not_connection_seeking_practical(self, classifier):
        is_seeking, seek_type = classifier.is_connection_seeking("Write me an email to my boss")
        assert is_seeking is False
        assert seek_type == ""

    # detect_intent_shift tests
    def test_detect_shift_practical_to_emotional(self, classifier):
        history = [
            {"role": "user", "content": "Write me a resignation email"},
            {"role": "assistant", "content": "Here's a template..."},
            {"role": "user", "content": "Thanks. I'm just so scared about what will happen next"}
        ]
        shift = classifier.detect_intent_shift(
            history,
            INTENT_PRACTICAL,
            "I'm scared about what will happen"
        )
        assert shift is not None
        assert shift["from_intent"] == INTENT_PRACTICAL
        assert shift["to_intent"] == INTENT_EMOTIONAL
        assert shift["is_concerning"] is True

    def test_no_shift_when_same_intent(self, classifier):
        history = [
            {"role": "user", "content": "Write me an email"},
            {"role": "assistant", "content": "Here's a template..."},
            {"role": "user", "content": "Now help me write another email"}
        ]
        shift = classifier.detect_intent_shift(
            history,
            INTENT_PRACTICAL,
            "Now help me write another email"
        )
        assert shift is None

    def test_no_shift_on_first_message(self, classifier):
        history = [{"role": "user", "content": "I'm feeling overwhelmed"}]
        shift = classifier.detect_intent_shift(
            history,
            INTENT_PRACTICAL,
            "I'm feeling overwhelmed"
        )
        assert shift is None  # Too early to detect shift


class TestSessionIntentTracking:
    """Tests for Phase 4 session intent tracking in WellnessTracker"""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return data_dir

    @pytest.fixture
    def tracker(self, temp_data_dir, monkeypatch):
        """Create a WellnessTracker with temp data directory."""
        # Patch settings.DATA_DIR
        from config import settings as cfg
        monkeypatch.setattr(cfg.settings, "DATA_DIR", temp_data_dir)
        return WellnessTracker()

    def test_should_not_show_check_in_first_session(self, tracker):
        """First session ever - don't interrupt."""
        assert tracker.should_show_intent_check_in() is False

    def test_should_not_show_check_in_clear_practical(self, tracker):
        """Clear practical request - skip check-in."""
        assert tracker.should_show_intent_check_in("Write me an email") is False
        assert tracker.should_show_intent_check_in("Help me write code") is False
        assert tracker.should_show_intent_check_in("Create a template for me") is False

    def test_record_session_intent(self, tracker):
        """Test recording session intent."""
        record = tracker.record_session_intent(TRACKER_PRACTICAL, was_check_in=True)
        assert record["intent"] == TRACKER_PRACTICAL
        assert record["was_check_in"] is True
        assert "datetime" in record

    def test_get_recent_intent(self, tracker):
        """Test getting most recent intent."""
        tracker.record_session_intent(TRACKER_PRACTICAL)
        tracker.record_session_intent(TRACKER_CONNECTION)

        recent = tracker.get_recent_intent()
        assert recent == TRACKER_CONNECTION

    def test_get_connection_seeking_frequency(self, tracker):
        """Test connection-seeking frequency calculation."""
        # Record some intents
        tracker.record_session_intent(TRACKER_PRACTICAL)
        tracker.record_session_intent(TRACKER_PRACTICAL)
        tracker.record_session_intent(TRACKER_CONNECTION)

        freq = tracker.get_connection_seeking_frequency(days=30)
        assert freq["total_sessions"] == 3
        assert freq["connection_seeking"] == 1
        assert freq["practical"] == 2
        assert freq["connection_ratio"] == round(1/3, 2)
        assert freq["is_concerning"] is False  # Not above threshold

    def test_connection_seeking_concerning_when_high(self, tracker):
        """Test that high connection-seeking is flagged as concerning."""
        # Record many connection-seeking sessions
        for _ in range(5):
            tracker.record_session_intent(TRACKER_CONNECTION)

        freq = tracker.get_connection_seeking_frequency(days=30)
        assert freq["connection_ratio"] == 1.0
        assert freq["is_concerning"] is True


class TestScenarioLoaderIntents:
    """Tests for Phase 4 intent configuration loading"""

    def test_get_session_intent_config(self, scenario_loader):
        config = scenario_loader.get_session_intent_config()
        assert "check_in" in config
        assert "intent_indicators" in config
        assert "shift_detection" in config

    def test_get_intent_check_in_config(self, scenario_loader):
        config = scenario_loader.get_intent_check_in_config()
        assert "prompt" in config
        assert "options" in config
        assert "practical" in config["options"]
        assert "processing" in config["options"]
        assert "connection" in config["options"]

    def test_get_intent_indicators(self, scenario_loader):
        indicators = scenario_loader.get_intent_indicators()
        assert "practical" in indicators
        assert "emotional" in indicators
        assert "connection_seeking" in indicators

    def test_get_connection_responses(self, scenario_loader):
        explicit = scenario_loader.get_connection_responses("explicit")
        assert len(explicit) > 0

        ai_relationship = scenario_loader.get_connection_responses("ai_relationship")
        assert len(ai_relationship) > 0


# ==================== PHASE 3: GRADUATION TESTS ====================

class TestTaskCategoryDetection:
    """Tests for Phase 3 task category detection in RiskClassifier"""

    @pytest.fixture
    def classifier(self, scenario_loader):
        return RiskClassifier(scenario_loader)

    def test_detect_email_drafting(self, classifier):
        category, confidence = classifier.detect_task_category("Write me an email to my boss")
        assert category == "email_drafting"
        assert confidence >= 0.8

    def test_detect_email_drafting_reply(self, classifier):
        category, confidence = classifier.detect_task_category("Help me reply to this email")
        assert category == "email_drafting"
        assert confidence >= 0.6

    def test_detect_code_help(self, classifier):
        category, confidence = classifier.detect_task_category("Write me a function that sorts numbers")
        assert category == "code_help"
        assert confidence >= 0.8

    def test_detect_code_help_debug(self, classifier):
        category, confidence = classifier.detect_task_category("Debug this code for me")
        assert category == "code_help"
        assert confidence >= 0.8

    def test_detect_explanations(self, classifier):
        category, confidence = classifier.detect_task_category("Explain how async/await works")
        assert category == "explanations"
        assert confidence >= 0.8

    def test_detect_explanations_what_is(self, classifier):
        category, confidence = classifier.detect_task_category("What is machine learning?")
        assert category == "explanations"
        assert confidence >= 0.8

    def test_detect_writing_general(self, classifier):
        category, confidence = classifier.detect_task_category("Write me a blog post about cooking")
        assert category == "writing_general"
        assert confidence >= 0.8

    def test_detect_summarizing(self, classifier):
        category, confidence = classifier.detect_task_category("Summarize this article for me")
        assert category == "summarizing"
        assert confidence >= 0.8

    def test_email_excluded_from_general_writing(self, classifier):
        # Should match email_drafting, not writing_general
        category, confidence = classifier.detect_task_category("Write me an email about the project")
        assert category == "email_drafting"

    def test_no_category_for_unmatched(self, classifier):
        category, confidence = classifier.detect_task_category("Hello, how are you?")
        assert category is None
        assert confidence == 0.0


class TestScenarioLoaderGraduation:
    """Tests for Phase 3 graduation configuration loading"""

    def test_get_graduation_settings(self, scenario_loader):
        settings = scenario_loader.get_graduation_settings()
        assert "min_tasks_before_prompt" in settings
        assert "max_prompts_per_session" in settings
        assert "max_dismissals" in settings

    def test_get_graduation_categories(self, scenario_loader):
        categories = scenario_loader.get_graduation_categories()
        assert "email_drafting" in categories
        assert "code_help" in categories
        assert "explanations" in categories

    def test_get_graduation_category(self, scenario_loader):
        category = scenario_loader.get_graduation_category("email_drafting")
        assert category is not None
        assert "threshold" in category
        assert "indicators" in category
        assert "graduation_prompts" in category
        assert "skill_tips" in category
        assert "celebration" in category

    def test_get_graduation_prompts(self, scenario_loader):
        prompts = scenario_loader.get_graduation_prompts("email_drafting")
        assert len(prompts) > 0
        assert isinstance(prompts[0], str)

    def test_get_skill_tips(self, scenario_loader):
        tips = scenario_loader.get_skill_tips("email_drafting")
        assert len(tips) > 0
        assert "title" in tips[0]
        assert "content" in tips[0]

    def test_get_graduation_celebration(self, scenario_loader):
        celebration = scenario_loader.get_graduation_celebration("email_drafting")
        assert len(celebration) > 0

    def test_get_independence_config(self, scenario_loader):
        config = scenario_loader.get_independence_config()
        assert "celebration_messages" in config
        assert "button_labels" in config

    def test_get_independence_celebrations(self, scenario_loader):
        celebrations = scenario_loader.get_independence_celebrations()
        assert len(celebrations) > 0

    def test_get_independence_button_labels(self, scenario_loader):
        labels = scenario_loader.get_independence_button_labels()
        assert len(labels) > 0
        assert "I did it myself!" in labels


class TestWellnessTrackerGraduation:
    """Tests for Phase 3 task pattern tracking in WellnessTracker"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a WellnessTracker with temporary data directory."""
        from config.settings import settings
        original_data_dir = settings.DATA_DIR
        settings.DATA_DIR = tmp_path
        tracker = WellnessTracker()
        yield tracker
        settings.DATA_DIR = original_data_dir

    def test_record_task_category(self, tracker):
        """Test recording a task category."""
        stats = tracker.record_task_category("email_drafting")
        assert stats["category"] == "email_drafting"
        assert stats["count"] == 1

    def test_record_task_category_increments(self, tracker):
        """Test that recording increments count."""
        tracker.record_task_category("email_drafting")
        stats = tracker.record_task_category("email_drafting")
        assert stats["count"] == 2

    def test_get_task_patterns(self, tracker):
        """Test getting all task patterns."""
        tracker.record_task_category("email_drafting")
        tracker.record_task_category("code_help")
        tracker.record_task_category("email_drafting")

        patterns = tracker.get_task_patterns()
        assert "email_drafting" in patterns
        assert "code_help" in patterns
        assert patterns["email_drafting"]["count"] == 2
        assert patterns["code_help"]["count"] == 1

    def test_get_category_stats(self, tracker):
        """Test getting stats for a specific category."""
        tracker.record_task_category("email_drafting")
        tracker.record_task_category("email_drafting")

        stats = tracker.get_category_stats("email_drafting")
        assert stats is not None
        assert stats["count"] == 2
        assert "last_7_days" in stats
        assert "last_30_days" in stats

    def test_should_show_graduation_prompt_below_threshold(self, tracker):
        """Test that graduation prompt not shown below threshold."""
        tracker.record_task_category("email_drafting")

        should_show, reason = tracker.should_show_graduation_prompt("email_drafting", threshold=10)
        assert should_show is False
        assert reason == "below_threshold"

    def test_should_show_graduation_prompt_at_threshold(self, tracker):
        """Test that graduation prompt shown at threshold."""
        for _ in range(10):
            tracker.record_task_category("email_drafting")

        should_show, reason = tracker.should_show_graduation_prompt("email_drafting", threshold=10)
        assert should_show is True
        assert reason == "threshold_met"

    def test_should_not_show_after_max_dismissals(self, tracker):
        """Test that graduation prompt not shown after max dismissals."""
        for _ in range(10):
            tracker.record_task_category("email_drafting")

        # Dismiss 3 times
        for _ in range(3):
            tracker.record_graduation_dismissal("email_drafting")

        should_show, reason = tracker.should_show_graduation_prompt(
            "email_drafting", threshold=10, max_dismissals=3
        )
        assert should_show is False
        assert reason == "max_dismissals_reached"

    def test_record_graduation_shown(self, tracker):
        """Test recording graduation shown."""
        tracker.record_task_category("email_drafting")
        tracker.record_graduation_shown("email_drafting")

        stats = tracker.get_category_stats("email_drafting")
        assert stats["graduation_shown_count"] == 1

    def test_record_graduation_dismissal(self, tracker):
        """Test recording graduation dismissal."""
        tracker.record_task_category("email_drafting")
        tracker.record_graduation_dismissal("email_drafting")

        stats = tracker.get_category_stats("email_drafting")
        assert stats["dismissal_count"] == 1

    def test_record_independence(self, tracker):
        """Test recording independence."""
        record = tracker.record_independence("email_drafting", "Wrote my own email!")
        assert record["category"] == "email_drafting"
        assert record["notes"] == "Wrote my own email!"

    def test_get_independence_stats(self, tracker):
        """Test getting independence stats."""
        tracker.record_independence("email_drafting")
        tracker.record_independence("code_help")
        tracker.record_independence("email_drafting")

        stats = tracker.get_independence_stats()
        assert stats["total_recent"] == 3
        assert stats["by_category"]["email_drafting"] == 2
        assert stats["by_category"]["code_help"] == 1

    def test_independence_milestone_detection(self, tracker):
        """Test milestone detection for independence."""
        # Record 5 independence events (milestone count)
        for _ in range(5):
            tracker.record_independence("general")

        stats = tracker.get_independence_stats()
        assert stats["is_milestone"] is True

    def test_get_recent_independence(self, tracker):
        """Test getting recent independence records."""
        tracker.record_independence("email_drafting", "First")
        tracker.record_independence("code_help", "Second")

        recent = tracker.get_recent_independence(limit=5)
        assert len(recent) == 2
        assert recent[-1]["notes"] == "Second"


# ==================== PHASE 5: ENHANCED HANDOFF TESTS ====================


class TestScenarioLoaderHandoff:
    """Tests for Phase 5 handoff configuration loading"""

    def test_get_handoff_settings(self, scenario_loader):
        """Test loading handoff settings."""
        settings = scenario_loader.get_handoff_settings()
        assert "show_follow_up" in settings
        assert "follow_up_delay_hours" in settings
        assert settings["max_follow_ups_per_week"] == 2

    def test_get_handoff_templates(self, scenario_loader):
        """Test loading handoff template categories."""
        templates = scenario_loader.get_handoff_templates()
        assert "after_difficult_task" in templates
        assert "processing_decision" in templates
        assert "general" in templates

    def test_get_handoff_template_category(self, scenario_loader):
        """Test getting a specific handoff template category."""
        template = scenario_loader.get_handoff_template_category("after_difficult_task")
        assert template is not None
        assert "intro_prompts" in template
        assert "messages" in template
        assert "follow_up_prompts" in template

    def test_get_handoff_intro_prompts(self, scenario_loader):
        """Test getting intro prompts for a handoff category."""
        prompts = scenario_loader.get_handoff_intro_prompts("after_difficult_task")
        assert len(prompts) > 0
        # Should mention drafting something hard
        assert any("hard" in p.lower() or "draft" in p.lower() for p in prompts)

    def test_get_handoff_messages(self, scenario_loader):
        """Test getting handoff messages."""
        messages = scenario_loader.get_handoff_messages("after_difficult_task")
        assert len(messages) > 0

    def test_get_handoff_messages_by_domain(self, scenario_loader):
        """Test getting domain-specific handoff messages."""
        messages = scenario_loader.get_handoff_messages("after_sensitive_topic", "health")
        assert len(messages) > 0
        # Should be health-related
        assert any("health" in m.lower() for m in messages)

    def test_detect_handoff_context_high_weight(self, scenario_loader):
        """Test context detection for high emotional weight task."""
        context = scenario_loader.detect_handoff_context(
            emotional_weight="high_weight"
        )
        assert context == "after_difficult_task"

    def test_detect_handoff_context_processing(self, scenario_loader):
        """Test context detection for processing intent."""
        context = scenario_loader.detect_handoff_context(
            session_intent="processing"
        )
        assert context == "processing_decision"

    def test_detect_handoff_context_domain(self, scenario_loader):
        """Test context detection for sensitive domain."""
        context = scenario_loader.detect_handoff_context(
            domain="relationships"
        )
        assert context == "after_sensitive_topic"

    def test_detect_handoff_context_high_usage(self, scenario_loader):
        """Test context detection for high usage pattern."""
        context = scenario_loader.detect_handoff_context(
            sessions_today=5
        )
        assert context == "high_usage_pattern"

    def test_detect_handoff_context_general(self, scenario_loader):
        """Test default context detection."""
        context = scenario_loader.detect_handoff_context()
        assert context == "general"

    def test_get_handoff_follow_up_prompts(self, scenario_loader):
        """Test getting follow-up prompts."""
        prompts = scenario_loader.get_handoff_follow_up_prompts("after_difficult_task")
        assert len(prompts) > 0

    def test_get_handoff_celebrations(self, scenario_loader):
        """Test getting handoff celebration messages."""
        celebrations = scenario_loader.get_handoff_celebrations("reached_out")
        assert len(celebrations) > 0

    def test_get_handoff_celebrations_very_helpful(self, scenario_loader):
        """Test getting celebration for very helpful outcome."""
        celebrations = scenario_loader.get_handoff_celebrations("very_helpful")
        assert len(celebrations) > 0


class TestTrustedNetworkHandoff:
    """Tests for Phase 5 context-aware handoff in TrustedNetwork"""

    @pytest.fixture
    def network(self, tmp_path):
        """Create a TrustedNetwork with temp data file."""
        from utils.trusted_network import TrustedNetwork
        from config.settings import settings
        settings.DATA_DIR = tmp_path
        return TrustedNetwork()

    def test_get_contextual_handoff(self, network):
        """Test getting context-aware handoff."""
        handoff = network.get_contextual_handoff(
            emotional_weight="high_weight",
            domain="logistics"
        )
        assert handoff["context"] == "after_difficult_task"
        assert handoff.get("intro_prompt") is not None

    def test_get_contextual_handoff_processing(self, network):
        """Test contextual handoff for processing intent."""
        handoff = network.get_contextual_handoff(
            session_intent="processing"
        )
        assert handoff["context"] == "processing_decision"

    def test_log_handoff_initiated(self, network):
        """Test logging handoff initiation."""
        handoff = network.log_handoff_initiated(
            context="after_difficult_task",
            domain="logistics",
            person_name="Mom",
            message_sent="Hey, I just drafted a hard email..."
        )
        assert handoff["context"] == "after_difficult_task"
        assert handoff["status"] == "initiated"
        assert handoff["person_name"] == "Mom"

    def test_record_handoff_outcome(self, network):
        """Test recording handoff outcome."""
        # First initiate
        handoff = network.log_handoff_initiated(
            context="general",
            person_name="Friend"
        )

        # Then record outcome
        updated = network.record_handoff_outcome(
            handoff_id=handoff["id"],
            reached_out=True,
            outcome="very_helpful"
        )

        assert updated["status"] == "completed"
        assert updated["outcome"] == "very_helpful"
        assert updated["reached_out"] is True

    def test_get_handoff_stats(self, network):
        """Test getting handoff statistics."""
        # Log some handoffs
        network.log_handoff_initiated("context1", person_name="A")
        h2 = network.log_handoff_initiated("context2", person_name="B")
        network.record_handoff_outcome(h2["id"], reached_out=True, outcome="very_helpful")

        stats = network.get_handoff_stats()
        assert stats["total_initiated"] == 2
        assert stats["total_reached_out"] == 1
        assert stats["reach_out_rate"] == 0.5

    def test_get_handoff_celebration(self, network):
        """Test getting handoff celebration message."""
        celebration = network.get_handoff_celebration("reached_out")
        assert celebration is not None
        assert len(celebration) > 0


class TestWellnessTrackerHandoff:
    """Tests for Phase 5 handoff tracking in WellnessTracker"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a WellnessTracker with temp data file."""
        from config.settings import settings
        settings.DATA_DIR = tmp_path
        return WellnessTracker()

    def test_log_handoff_event(self, tracker):
        """Test logging handoff events."""
        event = tracker.log_handoff_event(
            event_type="initiated",
            context="after_difficult_task",
            domain="logistics"
        )
        assert event["event_type"] == "initiated"
        assert event["context"] == "after_difficult_task"

    def test_log_handoff_reached_out(self, tracker):
        """Test logging reached out event."""
        event = tracker.log_handoff_event(
            event_type="reached_out",
            context="general",
            outcome="very_helpful"
        )
        assert event["event_type"] == "reached_out"
        assert event["outcome"] == "very_helpful"

    def test_get_handoff_success_metrics(self, tracker):
        """Test calculating handoff success metrics."""
        # Log some handoff events
        tracker.log_handoff_event("initiated", "context1")
        tracker.log_handoff_event("initiated", "context2")
        tracker.log_handoff_event("reached_out", "context1", outcome="very_helpful")
        tracker.log_handoff_event("outcome_reported", "context1", outcome="very_helpful")

        metrics = tracker.get_handoff_success_metrics()
        assert metrics["handoffs_initiated"] == 2
        assert metrics["handoffs_completed"] == 1
        assert metrics["reach_out_rate"] == 0.5
        assert metrics["outcomes"]["very_helpful"] == 2

    def test_should_show_handoff_follow_up_no_pending(self, tracker):
        """Test follow-up check with no pending handoffs."""
        should_show, pending = tracker.should_show_handoff_follow_up()
        assert should_show is False
        assert pending is None

    def test_mark_handoff_follow_up_shown(self, tracker):
        """Test marking follow-up as shown."""
        # Log an event
        event = tracker.log_handoff_event("initiated", "general")

        # Mark as shown
        tracker.mark_handoff_follow_up_shown(event["datetime"])

        # Verify
        data = tracker._load_data()
        events = data.get("handoff_events", [])
        for e in events:
            if e.get("datetime") == event["datetime"]:
                assert e.get("follow_up_shown") is True

    def test_handoff_success_metrics_is_healthy(self, tracker):
        """Test healthy metric calculation."""
        # Log handoffs with good outcomes
        for _ in range(3):
            tracker.log_handoff_event("initiated", "general")
            tracker.log_handoff_event("reached_out", "general", outcome="very_helpful")
            tracker.log_handoff_event("outcome_reported", "general", outcome="very_helpful")

        metrics = tracker.get_handoff_success_metrics()
        # 3 initiated, 3 reached out = 100% rate
        # 3 very helpful = 100% helpful rate
        assert metrics["is_healthy"] is True
