"""
Tests for empathySync core components
"""

import pytest
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.risk_classifier import RiskClassifier
from prompts.wellness_prompts import WellnessPrompts


class TestRiskClassifier:
    """Tests for RiskClassifier domain detection and risk scoring"""

    @pytest.fixture
    def classifier(self):
        return RiskClassifier()

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
    def prompts(self):
        return WellnessPrompts()

    def test_get_system_prompt_gentle(self, prompts):
        prompt = prompts.get_system_prompt("Gentle")
        assert "ancient soul" in prompt.lower()
        assert "gentle" in prompt.lower() or "sanctuary" in prompt.lower()

    def test_get_system_prompt_direct(self, prompts):
        prompt = prompts.get_system_prompt("Direct")
        assert "direct" in prompt.lower()
        assert "truth" in prompt.lower()

    def test_get_system_prompt_balanced(self, prompts):
        prompt = prompts.get_system_prompt("Balanced")
        assert "balanced" in prompt.lower() or "compassion" in prompt.lower()

    def test_get_system_prompt_unknown_defaults_to_balanced(self, prompts):
        balanced = prompts.get_system_prompt("Balanced")
        unknown = prompts.get_system_prompt("Unknown")
        assert balanced == unknown

    def test_check_in_prompts_not_empty(self, prompts):
        check_ins = prompts.get_check_in_prompts()
        assert len(check_ins) > 0
        assert all(isinstance(p, str) for p in check_ins)

    def test_mindfulness_prompts_not_empty(self, prompts):
        mindfulness = prompts.get_mindfulness_prompts()
        assert len(mindfulness) > 0
        assert all(isinstance(p, str) for p in mindfulness)


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
