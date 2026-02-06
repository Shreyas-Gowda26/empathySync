"""
CLI entry point for empathySync.

Usage:
    empathysync              # Launches Streamlit web interface (default)
    empathysync --mode web   # Same as above
    empathysync --mode cli   # Direct terminal interface (no browser needed)
"""

import sys
import argparse
import subprocess
from pathlib import Path


def run_streamlit():
    """Launch empathySync Streamlit app."""
    app_path = Path(__file__).parent / "app.py"
    sys.exit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.headless",
                "true",
            ]
        )
    )


def run_cli():
    """Launch empathySync in direct terminal mode."""
    # Add src to path for imports (same as app.py)
    sys.path.append(str(Path(__file__).parent))

    from models.ai_wellness_guide import WellnessGuide
    from models.conversation_session import ConversationSession
    from utils.wellness_tracker import WellnessTracker
    from utils.trusted_network import TrustedNetwork
    from interfaces.cli_adapter import CLIAdapter

    guide = WellnessGuide()
    tracker = WellnessTracker()
    network = TrustedNetwork()

    session = ConversationSession(guide, tracker, network)
    adapter = CLIAdapter(session)
    adapter.run()


def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(description="empathySync — Help that knows when to stop")
    parser.add_argument(
        "--mode",
        choices=["web", "cli"],
        default="web",
        help="Interface mode: web (Streamlit) or cli (terminal)",
    )

    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    else:
        run_streamlit()


if __name__ == "__main__":
    main()
