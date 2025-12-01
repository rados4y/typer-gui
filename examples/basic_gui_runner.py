"""Example of running a Typer app with the GUI."""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import typer_gui
sys.path.insert(0, str(Path(__file__).parent.parent))

from typer_gui import run_gui

from basic_typer_app import app

if __name__ == "__main__":
    run_gui(
        app,
        title="Typer Demo GUI",
        description="A simple demonstration of typer-gui with various command types and parameters.",
    )
