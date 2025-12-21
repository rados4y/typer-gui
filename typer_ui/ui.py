"""Main UI class for typer-ui - integrated API."""

from typing import Callable, Optional
import sys
import typer
import flet as ft

from .spec_builder import build_app_spec, _GUI_OPTIONS_ATTR
from .specs import CommandUiSpec
from .runners.gui_runner import create_flet_app
from .runners.cli_runner import CLIRunner
from .ui_blocks import get_current_runner


class Ui:
    """Main entry point for typer-ui - extension API for Typer apps.

    This class provides GUI-specific configuration on top of existing Typer applications.
    It works alongside Typer's decorators, not as a replacement.

    Example:
        >>> import typer
        >>> import typer_ui as tg
        >>>
        >>> app = typer.Typer()
        >>> ui = tg.Ui(
        >>>     app,
        >>>     title="My Application",
        >>>     description="A demo app"
        >>> )
        >>>
        >>> @app.command()
        >>> @ui.command(is_button=True)
        >>> def greet(name: str):
        >>>     ui(tg.Md("# Hello!"))
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
        self._cli_mode = False

    def __call__(self, component):
        """Present a component and return it for further use.

        This is the universal output method. It displays the component
        and returns it, allowing for chaining or context manager usage.

        Args:
            component: UiBlock component to display

        Returns:
            The component (for chaining or context manager usage)

        Example:
            >>> # Simple presentation
            >>> ui(tg.Table(cols=["Name"], data=[["Alice"]]))
            >>>
            >>> # Present and modify
            >>> t = tg.Table(cols=["Name"], data=[])
            >>> ui(t)  # Present it
            >>> t.add_row(["Alice"])  # Auto-updates!
            >>>
            >>> # Context manager
            >>> with ui(tg.Table(cols=["Name"], data=[])) as t:
            >>>     t.add_row(["Alice"])
            >>>     time.sleep(1)
            >>>     t.add_row(["Bob"])

        Raises:
            RuntimeError: If called outside of command execution context
        """
        runner = get_current_runner()
        if not runner:
            raise RuntimeError(
                "ui() can only be called during command execution. "
                "Ensure you're calling it from within a command function."
            )

        # Show the component
        runner.show(component)

        # Mark component as presented for auto-updates
        if hasattr(component, '_mark_presented'):
            component._mark_presented(runner)

        # Return component for chaining/context manager
        return component

    def out(self, component) -> None:
        """Legacy output method. Use ui(component) instead.

        Args:
            component: UiBlock component to display
        """
        self(component)

    def command(
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
                CommandUiSpec(
                    is_button=is_button,
                    is_long=is_long,
                    is_auto_exec=is_auto_exec,
                ),
            )
            return func

        return decorator

    # Alias for backward compatibility
    options = command

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
            self._cli_mode = True

            # Remove --cli flag from arguments
            sys.argv.remove("--cli")

            # Build app spec
            app_spec = build_app_spec(
                self._typer_app,
                title=self.title,
                description=self.description
            )

            # Create CLI runner and set as current
            from .ui_blocks import set_current_runner
            cli_runner = CLIRunner(app_spec)
            set_current_runner(cli_runner)

            try:
                # Run the Typer CLI directly
                self._typer_app()
            finally:
                # Clear runner reference
                set_current_runner(None)
        else:
            # Launch the GUI
            self._run_gui()

    def _run_gui(self):
        """Internal method to launch the GUI."""
        # Build the GUI model from the Typer app
        app_spec = build_app_spec(
            self._typer_app,
            title=self.title,
            description=self.description
        )

        # Create the Flet app function
        flet_main = create_flet_app(app_spec)

        # Run the Flet app
        ft.app(target=flet_main)

    @property
    def is_cli_mode(self) -> bool:
        """Check if running in CLI mode.

        Returns:
            True if in CLI mode, False if in GUI mode.
        """
        return self._cli_mode

    @property
    def typer_app(self) -> typer.Typer:
        """Access the underlying Typer application.

        This allows advanced usage if you need direct access to the Typer app.
        """
        return self._typer_app
