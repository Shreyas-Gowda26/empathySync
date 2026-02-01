"""
CLI entry point for empathySync.

Launches the Streamlit app via the command line.
Usage: empathysync
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Launch empathySync Streamlit app."""
    app_path = Path(__file__).parent / "app.py"
    sys.exit(subprocess.call([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true",
    ]))


if __name__ == "__main__":
    main()
