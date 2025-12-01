"""Main UI class for typer-gui - integrated API."""

from typing import Callable, Optional
import typer

from .core import build_gui_model, _GUI_OPTIONS_ATTR
from .types import GuiCommandOptions
from .runner import run_gui


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
        """Launch the GUI application.

        This should be called at the end of your script to start the GUI.

        Example:
            >>> if __name__ == "__main__":
            >>>     ui.app()
        """
        run_gui(
            self._typer_app,
            title=self.title,
            description=self.description,
        )

    @property
    def typer_app(self) -> typer.Typer:
        """Access the underlying Typer application.

        This allows advanced usage if you need direct access to the Typer app.
        """
        return self._typer_app
