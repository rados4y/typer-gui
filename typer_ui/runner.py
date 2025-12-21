"""Entry point for running Typer apps as Flet GUIs."""

from typing import Optional

import flet as ft
import typer

from .spec_builder import build_app_spec
from .flet_ui import create_flet_app


def run_gui(
    app: typer.Typer,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """
    Launch a Flet GUI for a Typer application.

    Args:
        app: A Typer application instance
        title: Optional window title (defaults to "Typer GUI")
        description: Optional description text shown at the top of the GUI

    Example:
        >>> import typer
        >>> from typer_ui import run_gui
        >>>
        >>> app = typer.Typer()
        >>>
        >>> @app.command()
        >>> def greet(name: str):
        >>>     print(f"Hello {name}!")
        >>>
        >>> if __name__ == "__main__":
        >>>     run_gui(app, title="My App")
    """
    # Build the GUI model from the Typer app
    gui_app = build_app_spec(app, title=title, description=description)

    # Create the Flet app function
    flet_main = create_flet_app(gui_app)

    # Run the Flet app
    ft.app(target=flet_main)
