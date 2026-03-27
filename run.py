"""
CreditSage Loan Advisory Agent — Entry Point
=============================================
Launches the Streamlit application.

Usage:
    python run.py
    OR
    python start.py   (symlink / alias)
"""

import subprocess
import sys
import os


def main():
    """Launch the Streamlit app."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless", "true"],
        cwd=os.path.dirname(__file__),
    )


if __name__ == "__main__":
    main()
