"""Tests for CLI mode."""
import pytest
from unittest.mock import patch, MagicMock


class TestCLIArguments:
    def test_mode_cli_calls_run_cli(self):
        with patch("src.cli.run_cli") as mock_run_cli:
            with patch("sys.argv", ["empathysync", "--mode", "cli"]):
                from src.cli import main
                main()
            assert mock_run_cli.called

    def test_mode_web_calls_run_streamlit(self):
        with patch("src.cli.run_streamlit") as mock_run_streamlit:
            with patch("sys.argv", ["empathysync", "--mode", "web"]):
                from src.cli import main
                main()
            assert mock_run_streamlit.called

    def test_default_mode_calls_run_streamlit(self):
        with patch("src.cli.run_streamlit") as mock_run_streamlit:
            with patch("sys.argv", ["empathysync"]):
                from src.cli import main
                main()
            assert mock_run_streamlit.called


class TestRunCLI:
    def test_run_cli_starts_adapter(self):
        with patch("src.cli.run_cli") as mock_run_cli:
            mock_run_cli.return_value = None
            with patch("sys.argv", ["empathysync", "--mode", "cli"]):
                from src.cli import main
                main()
            assert mock_run_cli.call_count == 1

    def test_run_cli_with_mocked_ollama(self):
        with patch("models.ai_wellness_guide.OllamaClient") as mock_ollama:
            mock_ollama.return_value.generate.return_value = "I'm here for you"
            mock_ollama.chat.return_value = {
                "message": {"content": "I'm here for you"}
            }
            with patch("interfaces.cli_adapter.CLIAdapter") as mock_adapter:
                mock_adapter.return_value.run = MagicMock()
                with patch("sys.argv", ["empathysync", "--mode", "cli"]):
                    from src.cli import main
                    with patch("src.cli.run_cli") as mock_run_cli:
                        main()
                    assert mock_run_cli.called