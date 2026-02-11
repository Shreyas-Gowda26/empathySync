"""
Tests for src/utils/helpers.py

Covers:
- setup_logging() configuration
- validate_environment() delegation
- format_wellness_tip() formatting
- create_progress_summary() edge cases
"""

import logging
import pytest
from unittest.mock import patch, MagicMock


class TestSetupLogging:
    """Tests for setup_logging()."""

    def test_creates_log_directory(self, tmp_path):
        logs_dir = tmp_path / "logs"

        mock_settings = MagicMock()
        mock_settings.LOGS_DIR = logs_dir
        mock_settings.LOG_FILE = "test.log"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.APP_VERSION = "0.1.0"
        mock_settings.ENVIRONMENT = "test"

        with patch("utils.helpers.settings", mock_settings):
            from utils.helpers import setup_logging

            setup_logging()

        assert logs_dir.exists()

    def test_sets_log_level_from_settings(self, tmp_path):
        logs_dir = tmp_path / "logs"

        mock_settings = MagicMock()
        mock_settings.LOGS_DIR = logs_dir
        mock_settings.LOG_FILE = "test.log"
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.APP_VERSION = "0.1.0"
        mock_settings.ENVIRONMENT = "test"

        with (
            patch("utils.helpers.settings", mock_settings),
            patch("logging.basicConfig") as mock_basic,
        ):
            from utils.helpers import setup_logging

            setup_logging()

        mock_basic.assert_called_once()
        call_kwargs = mock_basic.call_args
        assert call_kwargs[1]["level"] == logging.DEBUG


class TestValidateEnvironment:
    """Tests for validate_environment()."""

    def test_returns_empty_when_valid(self):
        mock_settings = MagicMock()
        mock_settings.validate_config.return_value = []

        with patch("utils.helpers.settings", mock_settings):
            from utils.helpers import validate_environment

            result = validate_environment()

        assert result == []

    def test_returns_missing_config(self):
        mock_settings = MagicMock()
        mock_settings.validate_config.return_value = ["OLLAMA_HOST", "OLLAMA_MODEL"]

        with patch("utils.helpers.settings", mock_settings):
            from utils.helpers import validate_environment

            result = validate_environment()

        assert "OLLAMA_HOST" in result
        assert "OLLAMA_MODEL" in result


class TestFormatWellnessTip:
    """Tests for format_wellness_tip()."""

    def test_includes_tip_text(self):
        from utils.helpers import format_wellness_tip

        result = format_wellness_tip("Stay hydrated")
        assert "Stay hydrated" in result

    def test_includes_wellness_insight_label(self):
        from utils.helpers import format_wellness_tip

        result = format_wellness_tip("Take breaks")
        assert "Wellness Insight" in result


class TestCreateProgressSummary:
    """Tests for create_progress_summary()."""

    def test_zero_conversations_returns_welcome(self):
        from utils.helpers import create_progress_summary

        result = create_progress_summary(0, 0)
        assert "Welcome" in result

    def test_single_day_says_today(self):
        from utils.helpers import create_progress_summary

        result = create_progress_summary(3, 1)
        assert "today" in result
        assert "3" in result

    def test_multiple_days_shows_average(self):
        from utils.helpers import create_progress_summary

        result = create_progress_summary(10, 5)
        assert "over 5 days" in result
        assert "2.0" in result

    def test_zero_days_no_division_error(self):
        from utils.helpers import create_progress_summary

        # Should not raise ZeroDivisionError
        result = create_progress_summary(5, 0)
        assert isinstance(result, str)
        assert "5" in result
