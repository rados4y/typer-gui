"""Main UI class for typer-gui - integrated API."""

from typing import Callable, Optional
import sys
import typer
import flet as ft

from .core import build_gui_model, _GUI_OPTIONS_ATTR
from .types import GuiCommandOptions
from .flet_ui import create_flet_app
from . import ui_blocks

# Global flag to track if we're in CLI mode
_CLI_MODE = False


def _run_gui(
    app: typer.Typer,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Internal function to launch a Flet GUI for a Typer application.

    Args:
        app: A Typer application instance
        title: Optional window title (defaults to "Typer GUI")
        description: Optional description text shown at the top of the GUI
    """
    # Build the GUI model from the Typer app
    gui_app = build_gui_model(app, title=title, description=description)

    # Create the Flet app function
    flet_main = create_flet_app(gui_app)

    # Run the Flet app
    ft.app(target=flet_main)


class Ui:
    """Main entry point for typer-gui - extension API for Typer apps.

    This class provides GUI-specific configuration on top of existing Typer applications.
    It works alongside Typer's decorators, not as a replacement.

    Example:
        >>> import typer
        >>> import typer_gui
        >>>
        >>> app = typer.Typer()
        >>> ui = typer_gui.Ui(
        >>>     app,
        >>>     title="My Application",
        >>>     description="A demo app"
        >>> )
        >>>
        >>> @app.command()
        >>> @ui.command(is_button=True)
        >>> def greet(name: str):
        >>>     print(f"Hello {name}!")
        >>>
        >>> if __name__ == "__main__":
        >>>     ui.app()
    """

    # UI Blocks - accessible as ui.table(), ui.md(), etc.
    table = staticmethod(ui_blocks.table)
    md = staticmethod(ui_blocks.md)
    link = staticmethod(ui_blocks.link)
    button = staticmethod(ui_blocks.button)

    def __init__(
        self,
        app: typer.Typer,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the UI wrapper for a Typer app.

        Args:
            app: The Typer application instance to extend
            title: Window title for the GUI
            description: Description text shown at the top of the GUI
        """
        self.title = title
        self.description = description
        self._typer_app = app

    def command(
        self,
        *,
        is_button: bool = False,
        is_long: bool = False,
        is_markdown: bool = False,
        is_auto_exec: bool = False,
    ):
        """Decorator to add GUI-specific options to a Typer command.

        This decorator should be used alongside @app.command(), not instead of it.
        It only stores GUI metadata and doesn't affect Typer's behavior.

        Args:
            is_button: Display as a button in the left panel
            is_long: Enable real-time output streaming for long-running commands
            is_markdown: Render return value as Markdown
            is_auto_exec: Execute automatically when selected, hide 'Run Command' button

        Example:
            >>> @app.command()
            >>> @ui.command(is_button=True, is_long=True)
            >>> def process():
            >>>     for i in range(10):
            >>>         print(f"Step {i}")
            >>>         time.sleep(1)
        """

        def decorator(func: Callable) -> Callable:
            # Store GUI options on the function
            setattr(
                func,
                _GUI_OPTIONS_ATTR,
                GuiCommandOptions(
                    is_button=is_button,
                    is_long=is_long,
                    is_markdown=is_markdown,
                    is_auto_exec=is_auto_exec,
                ),
            )
            return func

        return decorator

    def app(self):
        """Launch the GUI application or CLI based on --cli flag.

        This should be called at the end of your script to start the GUI.
        If --cli flag is present in command line arguments, the GUI is bypassed
        and the Typer CLI is executed directly.

        Example:
            >>> if __name__ == "__main__":
            >>>     ui.app()  # Launches GUI
            >>>     # Or use: python script.py --cli command arg1 arg2
        """
        # Check if --cli flag is present
        if "--cli" in sys.argv:
            global _CLI_MODE
            _CLI_MODE = True

            # Remove --cli flag from arguments
            sys.argv.remove("--cli")

            # Run the Typer CLI directly
            self._typer_app()
        else:
            # Launch the GUI
            _run_gui(
                self._typer_app,
                title=self.title,
                description=self.description,
            )

    @staticmethod
    def is_cli_mode() -> bool:
        """Check if running in CLI mode.

        Returns:
            True if in CLI mode, False if in GUI mode.
        """
        return _CLI_MODE

    @property
    def typer_app(self) -> typer.Typer:
        """Access the underlying Typer application.

        This allows advanced usage if you need direct access to the Typer app.
        """
        return self._typer_app
