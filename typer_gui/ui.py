"""Main UI class for typer-gui - integrated API."""

from typing import Callable, Optional
import sys
import typer
import flet as ft

from .core import build_gui_model, _GUI_OPTIONS_ATTR
from .types import GuiCommandOptions
from .flet_ui import create_flet_app
from .ui_blocks import UiContext, set_context, get_context, UiOutput
from .ui_app import UIApp, UICommand

# Global flag to track if we're in CLI mode
_CLI_MODE = False


def _run_gui(
    app: typer.Typer,
    *,
    ui_instance: 'Ui',
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Internal function to launch a Flet GUI for a Typer application.

    Args:
        app: A Typer application instance
        ui_instance: The Ui instance that launched the GUI
        title: Optional window title (defaults to "Typer GUI")
        description: Optional description text shown at the top of the GUI
    """
    # Build the GUI model from the Typer app
    gui_app = build_gui_model(app, title=title, description=description)

    # Create the Flet app function
    flet_main = create_flet_app(gui_app, ui_instance=ui_instance)

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
        self._ui_app_instance: Optional['UIApp'] = None
        self.out = UiOutput()

    def options(
        self,
        *,
        is_button: bool = False,
        is_long: bool = False,
        is_auto_exec: bool = False,
    ):
        """Decorator to add GUI-specific options to a Typer command.

        This decorator should be used alongside @app.command(), not instead of it.
        It only stores GUI metadata and doesn't affect Typer's behavior.

        Args:
            is_button: Display as a button in the left panel
            is_long: Enable real-time output streaming for long-running commands
            is_auto_exec: Execute automatically when selected, hide 'Run Command' button

        Example:
            >>> @app.command()
            >>> @ui.options(is_button=True, is_long=True)
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
                    is_auto_exec=is_auto_exec,
                ),
            )
            return func

        return decorator

    def command(self, name: str) -> 'UICommand':
        """Get a command by name from the runtime context.

        Args:
            name: The command name (using hyphens, as registered with Typer)

        Returns:
            UICommand instance

        Raises:
            RuntimeError: If not in GUI runtime context
            ValueError: If command with the given name is not found

        Example:
            >>> ui.command("refresh-data").select()
            >>> ui.command("process").run(steps=5)
        """
        if not self.runtime:
            raise RuntimeError(
                f"Cannot access command '{name}': not in GUI runtime context. "
                "ui.command() can only be called from within command execution in GUI mode."
            )

        cmd = self.runtime.get_command(name)
        if not cmd:
            available = [c.name for c in self.runtime.commands]
            raise ValueError(
                f"Command '{name}' not found. Available commands: {', '.join(available)}"
            )

        return cmd

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

            # Set up CLI context
            context = UiContext(mode="cli")
            set_context(context)

            try:
                # Run the Typer CLI directly
                self._typer_app()
            finally:
                # Clear context after CLI execution
                set_context(None)
        else:
            # Launch the GUI
            _run_gui(
                self._typer_app,
                ui_instance=self,
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

    @property
    def runtime(self) -> Optional[UIApp]:
        """Access the UIApp runtime instance.

        This provides access to commands, UI blocks, and application state.
        Only available during GUI mode execution (returns None in CLI mode or before GUI starts).

        Returns:
            UIApp instance if in GUI mode during command execution, None otherwise.

        Example:
            >>> @app.command()
            >>> def my_command():
            >>>     # Access current command
            >>>     current = ui.runtime.cmd
            >>>     # Access all commands
            >>>     all_cmds = ui.runtime.commands
            >>>     # Access UI blocks
            >>>     header = ui.runtime.blocks.header
        """
        # First check if we have a stored instance (available in GUI mode)
        if self._ui_app_instance:
            return self._ui_app_instance

        # Fall back to context (for command execution)
        context = get_context()
        if context and context.ui_app:
            return context.ui_app

        return None
